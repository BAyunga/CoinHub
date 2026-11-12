"""
Admin-panel restrictions: what a limited "client" account can and cannot do,
compared with the developer (superuser) account.
"""
from django.contrib.auth.models import Group, Permission, User
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import CoinType
from apps.core.constants import ORDER_LOADED, ORDER_PAID
from apps.orders.models import Order
from apps.payments.models import Payment

CLIENT_PERMS = [
    "view_order", "change_order",
    "view_payment",
    "view_cointype", "change_cointype",
]


class AdminRestrictionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = Group.objects.create(name="Client Manager")
        group.permissions.set(Permission.objects.filter(codename__in=CLIENT_PERMS))
        cls.client_user = User.objects.create_user("client", password="pw", is_staff=True)
        cls.client_user.groups.add(group)
        cls.dev = User.objects.create_superuser("dev", "d@x.test", "pw")

        cls.coin = CoinType.objects.get(slug="baat")
        cls.order = Order.objects.create(
            reference="CH-TEST-1", coin_type=cls.coin, app_user_id="1", phone_number="254712345678",
            coins_requested=9000, amount_paid=135, status=ORDER_PAID)
        cls.payment = Payment.objects.create(order=cls.order, phone_number="254712345678", amount=135)

    def as_client(self):
        self.client.force_login(self.client_user)

    def as_dev(self):
        self.client.force_login(self.dev)

    # ── Coin types ───────────────────────────────────────────────────────────
    def test_client_cannot_add_or_delete_coins(self):
        self.as_client()
        self.assertEqual(self.client.get(reverse("admin:catalog_cointype_add")).status_code, 403)
        r = self.client.get(reverse("admin:catalog_cointype_delete", args=[self.coin.pk]))
        self.assertEqual(r.status_code, 403)

    def test_client_edit_form_has_no_icon_and_locks_structure(self):
        self.as_client()
        r = self.client.get(reverse("admin:catalog_cointype_change", args=[self.coin.pk]))
        self.assertEqual(r.status_code, 200)
        form = r.context["adminform"].form
        self.assertNotIn("icon", form.fields)
        for locked in ("name", "slug", "min_coins", "step_coins"):
            self.assertNotIn(locked, form.fields, locked)
        self.assertIn("step_price_kes", form.fields)
        self.assertIn("active", form.fields)

    def test_client_can_change_price_but_not_locked_fields(self):
        self.as_client()
        url = reverse("admin:catalog_cointype_change", args=[self.coin.pk])
        r = self.client.post(url, {"step_price_kes": 16, "active": "on"})
        self.assertEqual(r.status_code, 302)
        self.coin.refresh_from_db()
        self.assertEqual(self.coin.step_price_kes, 16)
        self.assertEqual((self.coin.min_coins, self.coin.step_coins, self.coin.slug), (9000, 1000, "baat"))

    def test_developer_still_has_full_control(self):
        self.as_dev()
        self.assertEqual(self.client.get(reverse("admin:catalog_cointype_add")).status_code, 200)
        r = self.client.get(reverse("admin:catalog_cointype_change", args=[self.coin.pk]))
        self.assertIn("icon", r.context["adminform"].form.fields)
        self.assertIn("min_coins", r.context["adminform"].form.fields)

    # ── Orders ───────────────────────────────────────────────────────────────
    def test_client_cannot_add_or_delete_orders(self):
        self.as_client()
        self.assertEqual(self.client.get(reverse("admin:orders_order_add")).status_code, 403)
        r = self.client.get(reverse("admin:orders_order_delete", args=[self.order.pk]))
        self.assertEqual(r.status_code, 403)

    def test_client_cannot_edit_order_status(self):
        self.as_client()
        url = reverse("admin:orders_order_change", args=[self.order.pk])
        form = self.client.get(url).context["adminform"].form
        self.assertNotIn("status", form.fields)
        self.client.post(url, {"status": "pending", "loading_notes": "x"})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, ORDER_PAID)

    def test_ship_coins_works_with_change_permission(self):
        self.as_client()
        self.client.get(reverse("admin:order-mark-loaded", args=[self.order.pk]))
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, ORDER_LOADED)
        self.assertEqual(self.order.loaded_by, self.client_user)

    def test_ship_coins_blocked_without_change_permission(self):
        view_only = User.objects.create_user("viewer", password="pw", is_staff=True)
        view_only.user_permissions.set(Permission.objects.filter(codename="view_order"))
        self.client.force_login(view_only)
        r = self.client.get(reverse("admin:order-mark-loaded", args=[self.order.pk]))
        self.assertEqual(r.status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, ORDER_PAID)

    def test_developer_can_correct_status(self):
        self.as_dev()
        form = self.client.get(reverse("admin:orders_order_change", args=[self.order.pk])).context["adminform"].form
        self.assertIn("status", form.fields)

    # ── Payments ─────────────────────────────────────────────────────────────
    def test_payments_are_read_only_for_everyone(self):
        for login in (self.as_client, self.as_dev):
            login()
            self.assertEqual(self.client.get(reverse("admin:payments_payment_add")).status_code, 403)
            self.assertEqual(
                self.client.get(reverse("admin:payments_payment_delete", args=[self.payment.pk])).status_code, 403)
        self.as_client()
        self.assertEqual(
            self.client.get(reverse("admin:payments_payment_change", args=[self.payment.pk])).status_code, 200)

    # ── Users / groups are invisible to the client ───────────────────────────
    def test_client_cannot_reach_users_or_groups(self):
        self.as_client()
        self.assertEqual(self.client.get(reverse("admin:auth_user_changelist")).status_code, 403)
        self.assertEqual(self.client.get(reverse("admin:auth_group_changelist")).status_code, 403)
