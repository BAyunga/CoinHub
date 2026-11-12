from django.test import TestCase

from apps.catalog.models import CoinType

# slug: (min_coins, step_coins, step_price_kes, [(coins, expected_kes), ...])
EXPECTED = {
    "glow":       (10_000, 10_000, 15, [(10_000, 15), (20_000, 30)]),
    "dessparty":  (10_000, 10_000, 15, [(10_000, 15)]),
    "tello":      (10_000, 10_000, 15, [(30_000, 45)]),
    "dreamparty": (10_000, 10_000, 15, [(10_000, 15)]),
    "minemo":     (100_000, 100_000, 15, [(100_000, 15), (300_000, 45)]),
    "baat":       (9_000, 1_000, 15, [(9_000, 135), (11_000, 165), (10_000, 150)]),
    "crush":      (9_000, 1_000, 15, [(9_000, 135)]),
    "hala":       (9_000, 1_000, 15, [(9_000, 135)]),
    "boloup":     (9_000, 1_000, 15, [(9_000, 135), (12_000, 180)]),
    "taka":       (5_000, 1_000, 15, [(5_000, 75), (6_000, 90)]),
    "mashi":      (600_000, 9_375, 1, [(600_000, 64), (609_375, 65), (1_200_000, 128)]),
    "poppo":      (8_000, 8_000, 111, [(8_000, 111), (16_000, 222)]),
}


class NewPriceListTests(TestCase):
    """Runs against the data produced by the migrations."""

    def test_price_list(self):
        for slug, (mn, step, price, cases) in EXPECTED.items():
            coin = CoinType.objects.get(slug=slug)
            self.assertEqual((coin.min_coins, coin.step_coins, coin.step_price_kes), (mn, step, price), slug)
            self.assertTrue(coin.active, slug)
            for coins, kes in cases:
                self.assertEqual(coin.calculate_kes(coins), kes, f"{slug} {coins}")

    def test_boomlive_is_hidden(self):
        self.assertFalse(CoinType.objects.get(slug="boomlive").active)

    def test_only_active_coins_listed(self):
        self.assertFalse(CoinType.objects.filter(active=True, slug="boomlive").exists())


class QuantityRulesTests(TestCase):
    def test_invalid_quantities_rejected(self):
        baat = CoinType.objects.get(slug="baat")
        for bad in (0, 1_000, 8_999, 9_500, 10_001):
            self.assertFalse(baat.is_valid_quantity(bad), bad)
            with self.assertRaises(ValueError):
                baat.calculate_kes(bad)

    def test_mashi_and_poppo_only_whole_kes(self):
        mashi = CoinType.objects.get(slug="mashi")
        poppo = CoinType.objects.get(slug="poppo")
        self.assertFalse(mashi.is_valid_quantity(600_001))
        self.assertFalse(mashi.is_valid_quantity(601_010))
        self.assertFalse(poppo.is_valid_quantity(8_001))
        self.assertFalse(poppo.is_valid_quantity(9_100))
        # every valid Mashi amount is a whole number of KES with no remainder
        for n in range(64, 200):
            self.assertEqual(mashi.calculate_kes(n * 9_375), n)


class RechargeApiValidationTests(TestCase):
    def _post(self, slug, coins):
        from rest_framework.test import APIClient
        return APIClient().post("/api/recharges/", {
            "coin_type_slug": slug, "app_user_id": "123",
            "phone_number": "254712345678", "coins_requested": coins,
        }, format="json")

    def test_below_minimum_is_400(self):
        r = self._post("baat", 5_000)
        self.assertEqual(r.status_code, 400)
        self.assertIn("coins_requested", r.json())

    def test_not_a_multiple_is_400(self):
        self.assertEqual(self._post("poppo", 9_100).status_code, 400)
        self.assertEqual(self._post("mashi", 601_010).status_code, 400)

    def test_inactive_coin_is_400(self):
        self.assertEqual(self._post("boomlive", 9_000).status_code, 400)

    def test_coin_list_hides_boomlive_and_has_new_fields(self):
        from rest_framework.test import APIClient
        r = APIClient().get("/api/coins/")
        data = r.json()
        rows = data["results"] if isinstance(data, dict) else data
        slugs = {c["slug"] for c in rows}
        self.assertNotIn("boomlive", slugs)
        mashi = next(c for c in rows if c["slug"] == "mashi")
        self.assertEqual((mashi["min_coins"], mashi["step_coins"], mashi["step_price_kes"]), (600_000, 9_375, 1))
        self.assertNotIn("price_per_1000", mashi)
