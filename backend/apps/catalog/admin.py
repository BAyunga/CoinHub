from django.contrib import admin
from .models import CoinType


@admin.register(CoinType)
class CoinTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "min_coins", "step_coins", "step_price_kes",
                    "per_1000", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("active",)
    actions = ["deactivate_selected", "activate_selected"]

    @admin.display(description="≈ KES per 1,000")
    def per_1000(self, obj):
        return f"{obj.price_per_1000:g}"

    # only superusers can delete coins (this also hides "Delete selected")
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    # safe alternative to deleting; hides coins from the site but keeps history
    @admin.action(description="Hide selected coins from the site (deactivate)")
    def deactivate_selected(self, request, queryset):
        count = queryset.update(active=False)
        self.message_user(request, f"{count} coin(s) deactivated.")

    @admin.action(description="Show selected coins on the site (activate)")
    def activate_selected(self, request, queryset):
        count = queryset.update(active=True)
        self.message_user(request, f"{count} coin(s) activated.")
