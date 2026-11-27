"""
Order reference generation: references must be unique even when many customers
order at the same moment, on any worker.
"""
import threading
from unittest import skipUnless

from django.db import connection, connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.catalog.models import CoinType
from apps.core.utils import generate_reference
from apps.orders.models import Order, OrderReferenceCounter


def _prefix():
    return f"CH{timezone.localdate().strftime('%d%m%y')}"


class ReferenceSequenceTests(TestCase):
    def test_sequence_starts_at_1_and_counts_up(self):
        p = _prefix()
        self.assertEqual([generate_reference() for _ in range(3)], [f"{p}0001", f"{p}0002", f"{p}0003"])

    def test_continues_after_orders_that_already_exist_today(self):
        """First call after deployment: the counter row does not exist yet but orders do."""
        p = _prefix()
        coin = CoinType.objects.get(slug="baat")
        for seq in ("0003", "0007"):     # includes a gap on purpose
            Order.objects.create(reference=f"{p}{seq}", coin_type=coin, app_user_id="1",
                                 phone_number="254712345678", coins_requested=10000, amount_paid=150)
        self.assertEqual(generate_reference(), f"{p}0008")
        self.assertEqual(generate_reference(), f"{p}0009")

    def test_does_not_reuse_numbers_when_an_order_is_deleted(self):
        p = _prefix()
        first = generate_reference()
        coin = CoinType.objects.get(slug="baat")
        order = Order.objects.create(reference=first, coin_type=coin, app_user_id="1",
                                     phone_number="254712345678", coins_requested=10000, amount_paid=150)
        order.delete()
        self.assertNotEqual(generate_reference(), first)    # the old "count + 1" would hand it out again

    def test_one_counter_row_per_day(self):
        for _ in range(5):
            generate_reference()
        self.assertEqual(OrderReferenceCounter.objects.count(), 1)


@skipUnless(connection.vendor == "postgresql", "needs a real database with row locks (PostgreSQL)")
class ReferenceConcurrencyTests(TransactionTestCase):
    serialized_rollback = True      # put the migration data (coins) back after this test

    def test_simultaneous_orders_never_share_a_reference(self):
        """Same steps as POST /api/recharges/: generate a reference, then create the order."""
        threads_n, per_thread = 12, 8
        errors = []
        start = threading.Barrier(threads_n)

        def worker():
            try:
                coin = CoinType.objects.get(slug="baat")
                start.wait()                       # everyone fires at the same instant
                for _ in range(per_thread):
                    Order.objects.create(
                        reference=generate_reference(), coin_type=coin, app_user_id="1",
                        phone_number="254712345678", coins_requested=10000, amount_paid=150)
            except Exception as exc:               # noqa: BLE001
                errors.append(repr(exc))
            finally:
                connections.close_all()

        threads = [threading.Thread(target=worker) for _ in range(threads_n)]
        [t.start() for t in threads]
        [t.join() for t in threads]

        self.assertEqual(errors, [], "some orders failed (duplicate reference)")
        refs = sorted(Order.objects.values_list("reference", flat=True))
        self.assertEqual(len(refs), threads_n * per_thread)
        self.assertEqual(len(set(refs)), len(refs))
        self.assertEqual(refs[0], f"{_prefix()}0001")
        self.assertEqual(refs[-1], f"{_prefix()}{threads_n * per_thread:04d}")   # no gaps either
