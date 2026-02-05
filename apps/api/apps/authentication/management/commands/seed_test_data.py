"""
Management command to seed test data for all business types and user roles.

Creates:
- Businesses of all types (restaurant, cafe, bakery, retail, pharmacy, etc.)
- Users with all roles (owner, manager, cashier, kitchen, driver)
- Categories and products for each business
- Sample orders and customer data

Usage:
    python manage.py seed_test_data
    python manage.py seed_test_data --clear  # Clear existing data first
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.db import transaction
from decimal import Decimal
import random

from apps.authentication.models import Business, User
from apps.menu.models import Category, Product
from apps.orders.models import Order, OrderItem


class Command(BaseCommand):
    help = "Seed test data for all business types and user roles"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing test data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing test data...")
            self.clear_test_data()

        self.stdout.write("Seeding test data...")

        with transaction.atomic():
            businesses = self.create_businesses()
            self.create_users(businesses)
            self.create_categories_and_products(businesses)
            self.create_sample_orders(businesses)

        self.stdout.write(
            self.style.SUCCESS("Successfully seeded test data!")
        )
        self.print_summary(businesses)

    def clear_test_data(self):
        """Clear all test data."""
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        Business.objects.all().delete()
        self.stdout.write(self.style.WARNING("Cleared all test data"))

    def create_businesses(self):
        """Create businesses of all types."""
        businesses_data = [
            # Restaurants
            {
                "name": "Maquis Chez Adjoua",
                "business_type": "restaurant",
                "phone": "+225 07 01 02 03 04",
                "email": "contact@chezadjoua.ci",
                "address": "Cocody Angré, Abidjan",
                "plan_type": "pro",
                "has_kitchen_display": True,
                "has_table_service": True,
                "has_delivery": True,
            },
            {
                "name": "Le Kédjenou d'Or",
                "business_type": "restaurant",
                "phone": "+225 05 11 22 33 44",
                "email": "info@kedjenoudor.ci",
                "address": "Plateau, Abidjan",
                "plan_type": "full",
                "has_kitchen_display": True,
                "has_table_service": True,
                "has_delivery": True,
                "tax_id": "CI123456789",
                "tax_regime": "fne",
            },
            # Cafe
            {
                "name": "Café Ivoire",
                "business_type": "cafe",
                "phone": "+225 01 55 66 77 88",
                "email": "hello@cafeivoire.ci",
                "address": "Zone 4, Marcory, Abidjan",
                "plan_type": "pro",
                "has_table_service": True,
            },
            # Bakery
            {
                "name": "Boulangerie Le Fournil",
                "business_type": "bakery",
                "phone": "+225 07 99 88 77 66",
                "email": "contact@lefournil.ci",
                "address": "Yopougon, Abidjan",
                "plan_type": "pro",
                "has_delivery": True,
            },
            # Retail Shop
            {
                "name": "Boutique Mode Chic",
                "business_type": "retail",
                "phone": "+225 05 44 33 22 11",
                "email": "vente@modechic.ci",
                "address": "Treichville, Abidjan",
                "plan_type": "free",
            },
            # Pharmacy
            {
                "name": "Pharmacie Santé Plus",
                "business_type": "pharmacy",
                "phone": "+225 01 12 34 56 78",
                "email": "pharma@santeplus.ci",
                "address": "Cocody, Abidjan",
                "plan_type": "pro",
                "tax_id": "CI987654321",
                "tax_regime": "rne",
            },
            # Confectionery
            {
                "name": "Délices Sucrés",
                "business_type": "confectionery",
                "phone": "+225 07 22 33 44 55",
                "email": "commande@delicessucres.ci",
                "address": "Riviera, Abidjan",
                "plan_type": "free",
            },
            # Grocery
            {
                "name": "Épicerie du Quartier",
                "business_type": "grocery",
                "phone": "+225 05 66 77 88 99",
                "email": "contact@epiceriequartier.ci",
                "address": "Adjamé, Abidjan",
                "plan_type": "free",
            },
            # Boutique
            {
                "name": "Fashion House Abidjan",
                "business_type": "boutique",
                "phone": "+225 01 99 00 11 22",
                "email": "style@fashionhouse.ci",
                "address": "Plateau, Abidjan",
                "plan_type": "pro",
            },
            # Hardware Store
            {
                "name": "Quincaillerie Express",
                "business_type": "hardware",
                "phone": "+225 07 33 44 55 66",
                "email": "vente@quincexpress.ci",
                "address": "Koumassi, Abidjan",
                "plan_type": "free",
            },
        ]

        businesses = []
        for data in businesses_data:
            slug = slugify(data["name"])
            business, created = Business.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": data["name"],
                    "business_type": data["business_type"],
                    "phone": data["phone"],
                    "email": data.get("email", ""),
                    "address": data.get("address", ""),
                    "plan_type": data.get("plan_type", "free"),
                    "has_kitchen_display": data.get("has_kitchen_display", False),
                    "has_table_service": data.get("has_table_service", False),
                    "has_delivery": data.get("has_delivery", False),
                    "tax_id": data.get("tax_id", ""),
                    "tax_regime": data.get("tax_regime", ""),
                },
            )
            businesses.append(business)
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  {status}: {business.name} ({business.business_type})")

        return businesses

    def create_users(self, businesses):
        """Create users with all roles for each business."""
        roles = ["owner", "manager", "cashier", "kitchen", "driver"]

        # Ivorian first names and last names
        first_names = [
            "Kouadio", "Aya", "Koffi", "Aminata", "Yao", "Adjoua",
            "Kouamé", "Fatou", "Jean-Pierre", "Marie", "Seydou", "Mariam",
            "Ibrahim", "Aïcha", "François", "Cécile", "Moussa", "Bintou",
        ]
        last_names = [
            "Konan", "Tra", "Brou", "Kouassi", "N'Guessan", "Koffi",
            "Diallo", "Touré", "Ouattara", "Coulibaly", "Yao", "Aka",
        ]

        user_count = 0
        for business in businesses:
            for role in roles:
                # Generate unique phone number
                phone = f"+225 0{random.randint(1, 7)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}"

                # Check if phone already exists
                if User.objects.filter(phone=phone).exists():
                    phone = f"+225 0{random.randint(1, 7)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}"

                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                name = f"{first_name} {last_name}"

                try:
                    user, created = User.objects.get_or_create(
                        phone=phone,
                        defaults={
                            "name": name,
                            "email": f"{first_name.lower()}.{last_name.lower()}@{slugify(business.name)}.ci",
                            "business": business,
                            "role": role,
                            "language": "fr",
                        },
                    )
                    if created:
                        user.set_password("test1234")
                        user.save()
                        user_count += 1
                except Exception:
                    pass  # Skip duplicates

        self.stdout.write(f"  Created {user_count} users across all businesses")

        # Create a superuser for testing
        if not User.objects.filter(phone="+225 00 00 00 00 00").exists():
            User.objects.create_superuser(
                phone="+225 00 00 00 00 00",
                password="admin1234",
                name="Admin BIZ360",
                email="admin@biz360.ci",
            )
            self.stdout.write("  Created superuser: +225 00 00 00 00 00 / admin1234")

    def create_categories_and_products(self, businesses):
        """Create categories and products based on business type."""

        # Product data by business type
        products_by_type = {
            "restaurant": {
                "categories": ["Entrées", "Plats Principaux", "Accompagnements", "Boissons", "Desserts"],
                "products": {
                    "Entrées": [
                        ("Salade Ivoirienne", 2500, "Salade fraîche avec avocat et tomates"),
                        ("Alloco", 1500, "Bananes plantains frites dorées"),
                        ("Kelewele", 1800, "Plantains épicés à la ghanéenne"),
                    ],
                    "Plats Principaux": [
                        ("Kédjenou de Poulet", 5500, "Poulet mijoté aux légumes dans une canari"),
                        ("Garba", 2500, "Attiéké avec thon frit et piment"),
                        ("Sauce Graine", 6000, "Sauce de noix de palme avec viande"),
                        ("Foutou Banane", 4500, "Foutou avec sauce claire"),
                        ("Placali", 4000, "Pâte de manioc fermenté avec sauce"),
                    ],
                    "Accompagnements": [
                        ("Attiéké", 1000, "Semoule de manioc"),
                        ("Riz Blanc", 800, "Riz parfumé"),
                        ("Frites de Plantain", 1200, "Plantains frits croustillants"),
                    ],
                    "Boissons": [
                        ("Bissap", 1000, "Jus d'hibiscus frais"),
                        ("Gnamakoudji", 1000, "Jus de gingembre"),
                        ("Eau Minérale", 500, "Bouteille 50cl"),
                        ("Bière Flag", 1500, "Bière locale 33cl"),
                    ],
                    "Desserts": [
                        ("Dêguê", 1500, "Yaourt au mil"),
                        ("Fruits Frais", 2000, "Assortiment de fruits de saison"),
                    ],
                },
            },
            "cafe": {
                "categories": ["Cafés", "Thés", "Jus Frais", "Pâtisseries", "Snacks"],
                "products": {
                    "Cafés": [
                        ("Espresso", 1000, "Café serré"),
                        ("Café Crème", 1500, "Espresso avec lait chaud"),
                        ("Cappuccino", 2000, "Espresso avec mousse de lait"),
                        ("Café Glacé", 2500, "Café froid avec glaçons"),
                    ],
                    "Thés": [
                        ("Thé Vert", 1200, "Thé vert nature"),
                        ("Thé à la Menthe", 1500, "Thé vert à la menthe fraîche"),
                        ("Kinkeliba", 1000, "Infusion traditionnelle"),
                    ],
                    "Jus Frais": [
                        ("Jus d'Orange", 1800, "Oranges pressées"),
                        ("Jus de Mangue", 2000, "Mangues fraîches"),
                        ("Cocktail Fruits", 2500, "Mélange de fruits tropicaux"),
                    ],
                    "Pâtisseries": [
                        ("Croissant", 800, "Croissant au beurre"),
                        ("Pain au Chocolat", 1000, "Viennoiserie au chocolat"),
                        ("Gâteau Coco", 1200, "Gâteau à la noix de coco"),
                    ],
                    "Snacks": [
                        ("Sandwich Poulet", 2500, "Sandwich au poulet grillé"),
                        ("Salade César", 3000, "Salade avec poulet et parmesan"),
                    ],
                },
            },
            "bakery": {
                "categories": ["Pains", "Viennoiseries", "Pâtisseries", "Gâteaux", "Sandwichs"],
                "products": {
                    "Pains": [
                        ("Baguette Tradition", 300, "Baguette croustillante"),
                        ("Pain Complet", 500, "Pain aux céréales"),
                        ("Pain de Mie", 800, "Pain de mie moelleux"),
                    ],
                    "Viennoiseries": [
                        ("Croissant Beurre", 500, "Croissant pur beurre"),
                        ("Pain au Chocolat", 600, "Chocolatine"),
                        ("Brioche", 700, "Brioche nature"),
                    ],
                    "Pâtisseries": [
                        ("Éclair Chocolat", 1200, "Éclair au chocolat"),
                        ("Tarte aux Fruits", 1500, "Tarte de saison"),
                        ("Mille-Feuille", 1800, "Mille-feuille vanille"),
                    ],
                    "Gâteaux": [
                        ("Gâteau Anniversaire", 15000, "Gâteau personnalisé"),
                        ("Cake Marbré", 5000, "Cake chocolat-vanille"),
                    ],
                    "Sandwichs": [
                        ("Sandwich Jambon", 1500, "Jambon beurre"),
                        ("Sandwich Thon", 2000, "Thon mayonnaise"),
                    ],
                },
            },
            "retail": {
                "categories": ["Vêtements Femme", "Vêtements Homme", "Accessoires", "Chaussures"],
                "products": {
                    "Vêtements Femme": [
                        ("Robe Wax", 25000, "Robe en tissu wax"),
                        ("Jupe Pagne", 15000, "Jupe traditionnelle"),
                        ("Blouse", 12000, "Blouse élégante"),
                    ],
                    "Vêtements Homme": [
                        ("Chemise Wax", 18000, "Chemise en tissu africain"),
                        ("Pantalon", 20000, "Pantalon classique"),
                        ("Boubou", 35000, "Boubou traditionnel"),
                    ],
                    "Accessoires": [
                        ("Sac à Main", 25000, "Sac en cuir"),
                        ("Foulard", 8000, "Foulard en soie"),
                        ("Bijoux", 5000, "Parure de bijoux"),
                    ],
                    "Chaussures": [
                        ("Sandales", 15000, "Sandales confortables"),
                        ("Escarpins", 30000, "Escarpins élégants"),
                    ],
                },
            },
            "pharmacy": {
                "categories": ["Médicaments", "Parapharmacie", "Hygiène", "Bébé & Maman"],
                "products": {
                    "Médicaments": [
                        ("Paracétamol 500mg", 1500, "Boîte de 16 comprimés"),
                        ("Ibuprofène 400mg", 2500, "Boîte de 20 comprimés"),
                        ("Vitamine C", 3000, "Boîte de 30 comprimés effervescents"),
                    ],
                    "Parapharmacie": [
                        ("Crème Solaire SPF50", 8500, "Protection solaire 100ml"),
                        ("Crème Hydratante", 6000, "Soin visage 50ml"),
                        ("Huile de Coco", 4500, "Huile naturelle 200ml"),
                    ],
                    "Hygiène": [
                        ("Dentifrice", 2000, "Dentifrice fluoré 75ml"),
                        ("Savon Antiseptique", 1500, "Savon liquide 250ml"),
                        ("Déodorant", 3500, "Déodorant 48h"),
                    ],
                    "Bébé & Maman": [
                        ("Couches Bébé", 8000, "Paquet de 30 couches"),
                        ("Lait Infantile", 12000, "Boîte 400g"),
                        ("Lingettes Bébé", 3000, "Paquet de 72 lingettes"),
                    ],
                },
            },
            "confectionery": {
                "categories": ["Chocolats", "Bonbons", "Biscuits", "Glaces"],
                "products": {
                    "Chocolats": [
                        ("Tablette Chocolat Noir", 3500, "Chocolat noir 70%"),
                        ("Pralinés", 5000, "Boîte de 12 pralinés"),
                        ("Truffes", 6000, "Boîte de 8 truffes"),
                    ],
                    "Bonbons": [
                        ("Caramels", 2000, "Sachet 200g"),
                        ("Nougat", 2500, "Barre de nougat"),
                        ("Sucettes", 500, "Sucette fruits"),
                    ],
                    "Biscuits": [
                        ("Cookies Chocolat", 1800, "Paquet de 6"),
                        ("Sablés", 1500, "Boîte de sablés"),
                    ],
                    "Glaces": [
                        ("Glace Vanille", 2000, "Pot 500ml"),
                        ("Sorbet Mangue", 2500, "Pot 500ml"),
                    ],
                },
            },
            "grocery": {
                "categories": ["Fruits & Légumes", "Épicerie", "Boissons", "Produits Laitiers"],
                "products": {
                    "Fruits & Légumes": [
                        ("Tomates (kg)", 800, "Tomates fraîches"),
                        ("Oignons (kg)", 600, "Oignons locaux"),
                        ("Bananes Plantain", 500, "Lot de 3"),
                        ("Mangues", 1000, "Lot de 3 mangues"),
                    ],
                    "Épicerie": [
                        ("Riz (5kg)", 5000, "Riz parfumé"),
                        ("Huile (1L)", 2500, "Huile de palme"),
                        ("Sucre (1kg)", 800, "Sucre en poudre"),
                    ],
                    "Boissons": [
                        ("Eau (pack 6)", 1500, "Bouteilles 1.5L"),
                        ("Soda (1.5L)", 800, "Coca-Cola"),
                        ("Jus Pack", 2000, "Pack de 6 jus"),
                    ],
                    "Produits Laitiers": [
                        ("Lait (1L)", 1200, "Lait entier"),
                        ("Yaourt (pack 4)", 2000, "Yaourts nature"),
                    ],
                },
            },
            "boutique": {
                "categories": ["Prêt-à-Porter", "Accessoires", "Maroquinerie", "Parfums"],
                "products": {
                    "Prêt-à-Porter": [
                        ("Robe de Soirée", 75000, "Robe élégante"),
                        ("Costume Homme", 120000, "Costume 3 pièces"),
                        ("Tailleur Femme", 85000, "Tailleur classique"),
                    ],
                    "Accessoires": [
                        ("Montre de Luxe", 250000, "Montre automatique"),
                        ("Cravate Soie", 25000, "Cravate en soie"),
                        ("Lunettes Soleil", 45000, "Lunettes designer"),
                    ],
                    "Maroquinerie": [
                        ("Sac Designer", 180000, "Sac à main cuir"),
                        ("Portefeuille", 35000, "Portefeuille cuir"),
                        ("Ceinture", 28000, "Ceinture cuir"),
                    ],
                    "Parfums": [
                        ("Parfum Femme", 65000, "Eau de parfum 100ml"),
                        ("Parfum Homme", 55000, "Eau de toilette 100ml"),
                    ],
                },
            },
            "hardware": {
                "categories": ["Outillage", "Plomberie", "Électricité", "Peinture"],
                "products": {
                    "Outillage": [
                        ("Perceuse", 45000, "Perceuse électrique"),
                        ("Marteau", 5000, "Marteau de charpentier"),
                        ("Tournevis Set", 8000, "Set de 6 tournevis"),
                    ],
                    "Plomberie": [
                        ("Robinet", 15000, "Robinet mitigeur"),
                        ("Tuyau PVC", 3000, "Tuyau 2m"),
                        ("Joints", 1000, "Lot de joints"),
                    ],
                    "Électricité": [
                        ("Ampoule LED", 2500, "Ampoule 12W"),
                        ("Interrupteur", 3000, "Interrupteur double"),
                        ("Câble électrique", 5000, "Câble 10m"),
                    ],
                    "Peinture": [
                        ("Peinture (5L)", 25000, "Peinture acrylique"),
                        ("Pinceau Set", 8000, "Set de pinceaux"),
                        ("Rouleau", 3500, "Rouleau de peinture"),
                    ],
                },
            },
        }

        # Default for types not specifically defined
        default_products = {
            "categories": ["Produits", "Services"],
            "products": {
                "Produits": [
                    ("Produit Standard", 5000, "Produit générique"),
                ],
                "Services": [
                    ("Service Standard", 10000, "Service de base"),
                ],
            },
        }

        for business in businesses:
            btype = business.business_type
            type_data = products_by_type.get(btype, default_products)

            for cat_name in type_data["categories"]:
                category, _ = Category.objects.get_or_create(
                    business=business,
                    name=cat_name,
                    defaults={"display_order": type_data["categories"].index(cat_name)},
                )

                products = type_data["products"].get(cat_name, [])
                for name, price, description in products:
                    Product.objects.get_or_create(
                        business=business,
                        category=category,
                        name=name,
                        defaults={
                            "price": price,
                            "description": description,
                            "is_available": True,
                        },
                    )

            self.stdout.write(f"  Created products for: {business.name}")

    def create_sample_orders(self, businesses):
        """Create sample orders for testing."""
        order_count = 0

        for business in businesses:
            # Get products for this business
            products = list(Product.objects.filter(business=business)[:5])
            if not products:
                continue

            # Create 3-5 orders per business
            for i in range(random.randint(3, 5)):
                # Get next order number for this business
                last_order = Order.objects.filter(business=business).order_by('-order_number').first()
                next_order_number = (last_order.order_number + 1) if last_order else 1

                order = Order.objects.create(
                    business=business,
                    order_number=next_order_number,
                    status=random.choice(["pending", "preparing", "ready", "completed"]),
                    order_type=random.choice(["dine_in", "takeaway", "delivery"]),
                    customer_name=f"Client {i+1}",
                    customer_phone=f"+225 0{random.randint(1,7)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)} {random.randint(10,99)}",
                )

                # Add 1-3 items to the order
                order_products = random.sample(products, min(random.randint(1, 3), len(products)))
                for product in order_products:
                    quantity = random.randint(1, 3)
                    OrderItem.objects.create(
                        order=order,
                        business=business,
                        menu_item=product,
                        name=product.name,
                        quantity=quantity,
                        unit_price=product.price,
                    )

                # Update order totals
                order.calculate_totals()
                order.save()
                order_count += 1

        self.stdout.write(f"  Created {order_count} sample orders")

    def print_summary(self, businesses):
        """Print summary of created data."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("TEST DATA SUMMARY"))
        self.stdout.write("=" * 60)

        self.stdout.write("\nBUSINESSES BY TYPE:")
        for btype, label in Business.BUSINESS_TYPE_CHOICES:
            count = Business.objects.filter(business_type=btype).count()
            if count > 0:
                self.stdout.write(f"  {label}: {count}")

        self.stdout.write("\nUSERS BY ROLE:")
        for role, label in User.ROLE_CHOICES:
            count = User.objects.filter(role=role).count()
            self.stdout.write(f"  {label}: {count}")

        self.stdout.write(f"\nTotal Categories: {Category.objects.count()}")
        self.stdout.write(f"Total Products: {Product.objects.count()}")
        self.stdout.write(f"Total Orders: {Order.objects.count()}")

        self.stdout.write("\n" + "-" * 60)
        self.stdout.write(self.style.SUCCESS("TEST CREDENTIALS:"))
        self.stdout.write("-" * 60)
        self.stdout.write("Superuser: +225 00 00 00 00 00 / admin1234")
        self.stdout.write("All other users: <phone> / test1234")
        self.stdout.write("\nView all users with: python manage.py shell")
        self.stdout.write(">>> from apps.authentication.models import User")
        self.stdout.write(">>> User.objects.values('phone', 'name', 'role', 'business__name')")
        self.stdout.write("=" * 60 + "\n")
