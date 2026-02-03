from django.contrib import admin

from .models import Category, MenuItem, Modifier, ModifierOption


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0
    fields = ["name", "price", "is_available"]
    show_change_link = True


class ModifierInline(admin.TabularInline):
    model = Modifier
    extra = 0
    fields = ["name", "required", "max_selections", "display_order"]
    show_change_link = True


class ModifierOptionInline(admin.TabularInline):
    model = ModifierOption
    extra = 0
    fields = ["name", "price_adjustment", "is_available", "display_order"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "restaurant", "display_order", "is_visible"]
    list_filter = ["restaurant", "is_visible"]
    search_fields = ["name"]
    ordering = ["restaurant", "display_order", "name"]
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "restaurant", "price", "is_available"]
    list_filter = ["restaurant", "category", "is_available"]
    search_fields = ["name", "description"]
    ordering = ["restaurant", "category", "name"]
    inlines = [ModifierInline]


@admin.register(Modifier)
class ModifierAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "menu_item",
        "restaurant",
        "required",
        "max_selections",
        "display_order",
    ]
    list_filter = ["restaurant", "required"]
    search_fields = ["name", "menu_item__name"]
    ordering = ["restaurant", "display_order", "name"]
    inlines = [ModifierOptionInline]


@admin.register(ModifierOption)
class ModifierOptionAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "modifier",
        "restaurant",
        "price_adjustment",
        "is_available",
        "display_order",
    ]
    list_filter = ["restaurant", "is_available"]
    search_fields = ["name", "modifier__name"]
    ordering = ["restaurant", "display_order", "name"]
