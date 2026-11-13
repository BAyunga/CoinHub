"""
Lower the minimum purchase for Hala and BoloUp to 1,000 coins (data only).

    Hala, BoloUp : minimum 10,000 -> 1,000 coins

Step (1,000) and price (KES 15 per 1,000) are untouched. Baat stays at 10,000 and
Crush Live at 1,000. Only `min_coins` is written, so price edits made in the admin are kept.
Reversible: going back restores the 10,000 minimum.
"""
from django.db import migrations

SLUGS = ["hala", "boloup"]
NEW_MINIMUM = 1_000
OLD_MINIMUM = 10_000


def apply_minimum(apps, schema_editor):
    apps.get_model("catalog", "CoinType").objects.filter(slug__in=SLUGS).update(min_coins=NEW_MINIMUM)


def restore_minimum(apps, schema_editor):
    apps.get_model("catalog", "CoinType").objects.filter(slug__in=SLUGS).update(min_coins=OLD_MINIMUM)


class Migration(migrations.Migration):

    dependencies = [("catalog", "0010_update_minimum_purchases")]

    operations = [migrations.RunPython(apply_minimum, restore_minimum)]
