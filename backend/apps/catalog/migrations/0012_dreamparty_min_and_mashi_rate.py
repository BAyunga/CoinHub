"""
Pricing update (data only).

    Dream Party : minimum purchase 10,000 -> 50,000 coins (still sold in multiples of 10,000).
                  Only `min_coins` is written, so any price edit made in the admin is kept.
    Mashi       : 600,000 coins = KES 63  (was KES 64).

Mashi maths: 63 / 600,000 reduces to 21 / 200,000, so 200,000 coins = KES 21 is the smallest
pack that costs a whole number of shillings. Customers can only buy multiples of 200,000
(600,000 = KES 63, 800,000 = KES 84, 1,000,000 = KES 105 ...); the minimum stays 600,000.
The Mashi row is written with a single UPDATE so the CHECK constraints never see a half-updated row.

Reversible: going back restores the previous values.
"""
from django.db import migrations

DREAM_PARTY_NEW_MIN = 50_000
DREAM_PARTY_OLD_MIN = 10_000

# (min_coins, step_coins, step_price_kes)
MASHI_NEW = (600_000, 200_000, 21)
MASHI_OLD = (600_000, 9_375, 1)


def _set_mashi(apps, values):
    min_coins, step_coins, step_price = values
    apps.get_model("catalog", "CoinType").objects.filter(slug="mashi").update(
        min_coins=min_coins, step_coins=step_coins, step_price_kes=step_price,
    )


def apply_new(apps, schema_editor):
    CoinType = apps.get_model("catalog", "CoinType")
    CoinType.objects.filter(slug="dreamparty").update(min_coins=DREAM_PARTY_NEW_MIN)
    _set_mashi(apps, MASHI_NEW)


def restore_old(apps, schema_editor):
    CoinType = apps.get_model("catalog", "CoinType")
    CoinType.objects.filter(slug="dreamparty").update(min_coins=DREAM_PARTY_OLD_MIN)
    _set_mashi(apps, MASHI_OLD)


class Migration(migrations.Migration):

    dependencies = [("catalog", "0011_hala_boloup_minimum_1000")]

    operations = [migrations.RunPython(apply_new, restore_old)]
