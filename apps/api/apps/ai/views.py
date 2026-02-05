"""Views for AI-powered menu features."""

import logging
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.menu.models import Category, MenuItem

from .models import AIJob, AIJobStatus, AIJobType, AIUsage, MenuImportBatch
from .serializers import (
    AIJobSerializer,
    AIUsageSerializer,
    BulkImportSerializer,
    GenerateDescriptionSerializer,
    ImportConfirmSerializer,
    MenuImportBatchSerializer,
    MenuOCRSerializer,
    PhotoAnalysisSerializer,
    PriceSuggestionSerializer,
    TranslateItemSerializer,
    TranslateMenuSerializer,
)
from .services import CSVImporter, ExcelImporter, MenuTranslator, OpenAIService

logger = logging.getLogger(__name__)


class GenerateDescriptionView(APIView):
    """Generate AI description for a menu item."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateDescriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            service = OpenAIService()
            description = service.generate_item_description(
                item_name=data["item_name"],
                category=data["category"],
                ingredients=data.get("ingredients"),
                cuisine_type=data.get("cuisine_type", "West African"),
                language=data.get("language", "en"),
            )

            # Track usage
            AIUsage.objects.create(
                business=request.user.business,
                job_type=AIJobType.DESCRIPTION,
                model_used="gpt-4o-mini",
                prompt_tokens=100,  # Estimate
                completion_tokens=50,
                total_tokens=150,
                estimated_cost_cents=1,
            )

            return Response({"description": description})

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Description generation error: {e}")
            return Response(
                {"error": "Failed to generate description. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PhotoAnalysisView(APIView):
    """Analyze a food photo for quality and suggestions."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = PhotoAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data["image"]
        image_data = image.read()

        try:
            service = OpenAIService()
            analysis = service.enhance_item_photo(image_data)

            # Track usage
            AIUsage.objects.create(
                business=request.user.business,
                job_type=AIJobType.PHOTO_ANALYSIS,
                model_used="gpt-4o",
                prompt_tokens=1000,  # Vision uses more tokens
                completion_tokens=200,
                total_tokens=1200,
                estimated_cost_cents=5,
            )

            return Response(analysis)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Photo analysis error: {e}")
            return Response(
                {"error": "Failed to analyze photo. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MenuOCRView(APIView):
    """Extract menu items from a photo using OCR."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = MenuOCRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image = serializer.validated_data["image"]
        language = serializer.validated_data.get("language", "en")
        image_data = image.read()

        try:
            service = OpenAIService()
            items = service.extract_menu_from_image(image_data, language)

            # Create import batch for review
            batch = MenuImportBatch.objects.create(
                business=request.user.business,
                source_type="ocr",
                original_filename=image.name,
                items=items,
                total_items=len(items),
                valid_items=len(items),
            )

            # Track usage
            AIUsage.objects.create(
                business=request.user.business,
                job_type=AIJobType.MENU_OCR,
                model_used="gpt-4o",
                prompt_tokens=2000,
                completion_tokens=500,
                total_tokens=2500,
                estimated_cost_cents=10,
            )

            return Response(MenuImportBatchSerializer(batch).data)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Menu OCR error: {e}")
            return Response(
                {"error": "Failed to extract menu. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BulkImportView(APIView):
    """Import menu items from CSV/Excel file."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = BulkImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        filename = uploaded_file.name.lower()

        # Select importer
        if filename.endswith(".csv"):
            importer = CSVImporter()
            source_type = "csv"
        elif filename.endswith((".xlsx", ".xls")):
            importer = ExcelImporter()
            source_type = "excel"
        else:
            return Response(
                {"error": "Unsupported file format. Use CSV or Excel."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = importer.parse(uploaded_file)
            items = result.get("items", [])
            errors = result.get("errors", [])

            # Create import batch
            batch = MenuImportBatch.objects.create(
                business=request.user.business,
                source_type=source_type,
                original_filename=uploaded_file.name,
                items=items,
                errors=errors,
                total_items=len(items) + len(errors),
                valid_items=len(items),
            )

            return Response(MenuImportBatchSerializer(batch).data)

        except Exception as e:
            logger.error(f"Bulk import error: {e}")
            return Response(
                {"error": f"Failed to parse file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ImportConfirmView(APIView):
    """Confirm and apply a menu import batch."""

    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        try:
            batch = MenuImportBatch.objects.get(
                id=batch_id,
                business=request.user.business,
                status="pending",
            )
        except MenuImportBatch.DoesNotExist:
            return Response(
                {"error": "Import batch not found or already processed"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ImportConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        items_to_create = data["items"]
        default_category_id = data.get("category_id")
        create_categories = data.get("create_categories", True)

        # Track categories
        category_cache = {}
        created_count = 0

        try:
            for item_data in items_to_create:
                # Determine category
                category = None
                cat_name = item_data.get("category")

                if cat_name and create_categories:
                    if cat_name in category_cache:
                        category = category_cache[cat_name]
                    else:
                        category, _ = Category.objects.get_or_create(
                            business=request.user.business,
                            name=cat_name,
                            defaults={"display_order": Category.objects.filter(
                                business=request.user.business
                            ).count()},
                        )
                        category_cache[cat_name] = category
                elif default_category_id:
                    if default_category_id not in category_cache:
                        category_cache[default_category_id] = Category.objects.get(
                            id=default_category_id,
                            business=request.user.business,
                        )
                    category = category_cache[default_category_id]

                if not category:
                    continue  # Skip items without category

                # Create menu item
                MenuItem.objects.create(
                    business=request.user.business,
                    category=category,
                    name=item_data["name"],
                    price=item_data["price"],
                    description=item_data.get("description", ""),
                    is_available=item_data.get("is_available", True),
                    allergens=item_data.get("allergens", []),
                    dietary_tags=item_data.get("dietary_tags", []),
                    spice_level=item_data.get("spice_level", 0),
                    prep_time_minutes=item_data.get("prep_time_minutes"),
                    ingredients=item_data.get("ingredients", ""),
                )
                created_count += 1

            # Update batch
            batch.status = "confirmed"
            batch.confirmed_at = timezone.now()
            batch.created_items = created_count
            batch.save()

            return Response({
                "message": f"Successfully imported {created_count} items",
                "created_items": created_count,
            })

        except Exception as e:
            logger.error(f"Import confirm error: {e}")
            return Response(
                {"error": f"Failed to import items: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TranslateItemView(APIView):
    """Translate a single menu item."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TranslateItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            translator = MenuTranslator()
            result = translator.translate_single(
                name=data["name"],
                description=data.get("description"),
                source_lang=data["source_lang"],
                target_lang=data["target_lang"],
            )

            # Track usage
            AIUsage.objects.create(
                business=request.user.business,
                job_type=AIJobType.TRANSLATION,
                model_used="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                estimated_cost_cents=1,
            )

            return Response(result)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return Response(
                {"error": "Failed to translate. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TranslateMenuView(APIView):
    """Translate entire menu or selected items."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TranslateMenuSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get items to translate
        items = data.get("items")
        if not items:
            # Fetch all menu items
            menu_items = MenuItem.objects.filter(
                business=request.user.business
            ).values("id", "name", "description")
            items = list(menu_items)

        if not items:
            return Response(
                {"error": "No items to translate"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            translator = MenuTranslator()
            translated = translator.translate_menu(
                items=items,
                source_lang=data["source_lang"],
                target_lang=data["target_lang"],
            )

            # Track usage
            AIUsage.objects.create(
                business=request.user.business,
                job_type=AIJobType.TRANSLATION,
                model_used="gpt-4o-mini",
                prompt_tokens=len(items) * 50,
                completion_tokens=len(items) * 50,
                total_tokens=len(items) * 100,
                estimated_cost_cents=len(items),
            )

            return Response({"items": translated})

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Menu translation error: {e}")
            return Response(
                {"error": "Failed to translate menu. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PriceSuggestionView(APIView):
    """Get AI price suggestion for a menu item."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PriceSuggestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            service = OpenAIService()
            suggestion = service.suggest_price(
                item_name=data["item_name"],
                category=data["category"],
                description=data.get("description"),
                location=data.get("location", "Dakar, Senegal"),
                currency=data.get("currency", "XOF"),
            )

            # Track usage
            AIUsage.objects.create(
                business=request.user.business,
                job_type=AIJobType.PRICE_SUGGESTION,
                model_used="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                estimated_cost_cents=1,
            )

            return Response(suggestion)

        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Price suggestion error: {e}")
            return Response(
                {"error": "Failed to suggest price. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AIJobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI job tracking."""

    serializer_class = AIJobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AIJob.objects.filter(business=self.request.user.business)


class AIUsageView(APIView):
    """Get AI usage summary for the restaurant."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum

        usage = AIUsage.objects.filter(
            business=request.user.business
        )

        # Get totals
        totals = usage.aggregate(
            total_tokens=Sum("total_tokens"),
            total_cost_cents=Sum("estimated_cost_cents"),
        )

        # Get by type
        by_type = {}
        for choice in AIJobType.choices:
            type_usage = usage.filter(job_type=choice[0]).aggregate(
                count=Sum("id"),
                tokens=Sum("total_tokens"),
                cost=Sum("estimated_cost_cents"),
            )
            if type_usage["count"]:
                by_type[choice[0]] = {
                    "label": choice[1],
                    "count": usage.filter(job_type=choice[0]).count(),
                    "tokens": type_usage["tokens"] or 0,
                    "cost_cents": type_usage["cost"] or 0,
                }

        return Response({
            "total_tokens": totals["total_tokens"] or 0,
            "total_cost_cents": totals["total_cost_cents"] or 0,
            "by_type": by_type,
        })


class MenuImportBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for menu import batches."""

    serializer_class = MenuImportBatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MenuImportBatch.objects.filter(business=self.request.user.business)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending import batch."""
        batch = self.get_object()
        if batch.status != "pending":
            return Response(
                {"error": "Only pending batches can be cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        batch.status = "cancelled"
        batch.save()
        return Response({"message": "Import cancelled"})
