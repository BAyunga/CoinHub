from django.contrib import admin
from .models import CoinType

# Fields only a superuser (the developer) may change. Everyone else sees them read-only.
# To make prices developer-only as well, add "step_price_kes" to this tuple.
CLIENT_LOCKED_FIELDS = ("name", "slug", "min_coins", "step_coins")


@admin.register(CoinType)
class CoinTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "min_coins", "step_coins", "step_price_kes",
                    "per_1000", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("active",)
    actions = ["deactivate_selected", "activate_selected"]

    @admin.display(description="≈ KES per 1,000")
    def per_1000(self, obj):
        return f"{obj.price_per_1000:g}"

    # ── What the client can and cannot do ────────────────────────────────────
    def has_add_permission(self, request):
        return request.user.is_superuser          # new coins need an icon + site work

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser          # also hides "Delete selected"

    def get_exclude(self, request, obj=None):
        return None if request.user.is_superuser else ("icon",)   # no icon upload for the client

    def get_readonly_fields(self, request, obj=None):
        base = ("created_at", "updated_at")
        return base if request.user.is_superuser else base + CLIENT_LOCKED_FIELDS

    def get_prepopulated_fields(self, request, obj=None):
        return self.prepopulated_fields if request.user.is_superuser else {}

    # safe alternative to deleting; hides coins from the site but keeps history
    @admin.action(description="Hide selected coins from the site (deactivate)", permissions=["change"])
    def deactivate_selected(self, request, queryset):
        count = queryset.update(active=False)
        self.message_user(request, f"{count} coin(s) deactivated.")

    @admin.action(description="Show selected coins on the site (activate)", permissions=["change"])
    def activate_selected(self, request, queryset):
        count = queryset.update(active=True)
        self.message_user(request, f"{count} coin(s) activated.")
