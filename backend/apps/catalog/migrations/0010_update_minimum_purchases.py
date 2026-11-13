"""
Change minimum purchase amounts (data only; prices and steps are untouched).

    Baat, Hala, BoloUp : minimum 9,000  -> 10,000 coins
    Crush Live         : minimum 9,000  ->  1,000 coins

Only `min_coins` is written, so any price change made in the admin since 0008 is kept.
Reversible: going back restores the previous 9,000 minimum for all four coins.
"""
from django.db import migrations

NEW_MINIMUMS = {"baat": 10_000, "hala": 10_000, "boloup": 10_000, "crush": 1_000}
OLD_MINIMUM = 9_000


def apply_minimums(apps, schema_editor):
    CoinType = apps.get_model("catalog", "CoinType")
    for slug, minimum in NEW_MINIMUMS.items():
        CoinType.objects.filter(slug=slug).update(min_coins=minimum)


def restore_minimums(apps, schema_editor):
    CoinType = apps.get_model("catalog", "CoinType")
    CoinType.objects.filter(slug__in=list(NEW_MINIMUMS)).update(min_coins=OLD_MINIMUM)


class Migration(migrations.Migration):

    dependencies = [("catalog", "0009_remove_legacy_price_fields")]

    operations = [migrations.RunPython(apply_minimums, restore_minimums)]
