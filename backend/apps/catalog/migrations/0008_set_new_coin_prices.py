"""
Step 2 of 3: apply the new price list (data only).

(min_coins, step_coins, step_price_kes)

- Glow-family: 10,000 coins = KES 15, sold in multiples of 10,000.
- Minemo:      100,000 coins = KES 15, sold in multiples of 100,000.
- Baat/Crush Live/Hala/BoloUp: 1,000 coins = KES 15, minimum 9,000.
- Taka:        1,000 coins = KES 15, minimum 5,000.
- Mashi:       600,000 coins = KES 64  ->  9,375 coins = KES 1 is the smallest whole-KES step.
- Poppo:       8,000 coins = KES 111 (111 and 8,000 share no factor, so 8,000 is the smallest whole-KES step).
- Boomlive:    deactivated (kept, because it may have orders).
Any coin not listed keeps its previous effective price (converted from price_per_1000).
"""
from fractions import Fraction

from django.db import migrations

NEW_PRICES = {
    "glow":       (10_000, 10_000, 15),
    "dessparty":  (10_000, 10_000, 15),
    "tello":      (10_000, 10_000, 15),
    "dreamparty": (10_000, 10_000, 15),
    "minemo":     (100_000, 100_000, 15),
    "baat":       (9_000, 1_000, 15),
    "crush":      (9_000, 1_000, 15),
    "hala":       (9_000, 1_000, 15),
    "boloup":     (9_000, 1_000, 15),
    "taka":       (5_000, 1_000, 15),
    "mashi":      (600_000, 9_375, 1),
    "poppo":      (8_000, 8_000, 111),
}
DEACTIVATE = ["boomlive"]


def apply_prices(apps, schema_editor):
    CoinType = apps.get_model("catalog", "CoinType")

    for slug, (min_coins, step_coins, step_price) in NEW_PRICES.items():
        # one UPDATE so the CHECK constraints never see a half-updated row
        CoinType.objects.filter(slug=slug).update(
            min_coins=min_coins, step_coins=step_coins, step_price_kes=step_price,
        )

    # Every coin not in the new list (hand-added coins and Boomlive): keep its old
    # whole-shilling pack so nothing changes silently.
    for coin in CoinType.objects.exclude(slug__in=list(NEW_PRICES)):
        price = Fraction(str(coin.price_per_1000))
        step = price.denominator * 1000
        CoinType.objects.filter(pk=coin.pk).update(
            min_coins=step, step_coins=step, step_price_kes=int(price * step / 1000),
        )

    CoinType.objects.filter(slug__in=DEACTIVATE).update(active=False)


class Migration(migrations.Migration):

    dependencies = [("catalog", "0007_coin_step_pricing_fields")]

    operations = [migrations.RunPython(apply_prices, migrations.RunPython.noop)]
