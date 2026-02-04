from django.contrib import admin

from .models import DGIConfiguration, ElectronicInvoice, ElectronicInvoiceLine


@admin.register(DGIConfiguration)
class DGIConfigurationAdmin(admin.ModelAdmin):
    list_display = ["business", "taxpayer_id", "is_production", "is_active", "last_sync_at"]
    list_filter = ["is_production", "is_active"]
    search_fields = ["business__name", "taxpayer_id"]


class ElectronicInvoiceLineInline(admin.TabularInline):
    model = ElectronicInvoiceLine
    extra = 0
    readonly_fields = ["order_item"]


@admin.register(ElectronicInvoice)
class ElectronicInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "invoice_number",
        "business",
        "customer_name",
        "total_ttc",
        "status",
        "invoice_date",
    ]
    list_filter = ["status", "invoice_date"]
    search_fields = ["invoice_number", "customer_name", "dgi_uid"]
    readonly_fields = ["dgi_uid", "dgi_qr_code", "dgi_signature", "dgi_validation_date"]
    inlines = [ElectronicInvoiceLineInline]
