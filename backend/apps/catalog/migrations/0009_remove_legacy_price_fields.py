"""
Step 3 of 3: drop the old rounded-rate columns. Forward-only; back up the DB first.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("catalog", "0008_set_new_coin_prices")]

    operations = [
        migrations.RemoveField(model_name="cointype", name="price_per_1000"),
        migrations.RemoveField(model_name="cointype", name="conversion_rate"),
    ]
