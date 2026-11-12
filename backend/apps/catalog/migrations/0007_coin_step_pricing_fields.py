"""
Step 1 of 3: add the exact-integer pricing fields (schema only).
Existing rows get a placeholder that 0008 immediately replaces with real values.
"""
from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("catalog", "0006_remove_unwanted_coins")]

    operations = [
        migrations.AddField(
            model_name="cointype",
            name="min_coins",
            field=models.PositiveIntegerField(
                default=1000, validators=[MinValueValidator(1)],
                help_text="Smallest number of coins a customer can buy. Must be a multiple of 'Step coins'.",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cointype",
            name="step_coins",
            field=models.PositiveIntegerField(
                default=1000, validators=[MinValueValidator(1)],
                help_text="Coins are sold in multiples of this number, e.g. 1000.",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cointype",
            name="step_price_kes",
            field=models.PositiveIntegerField(
                default=15, validators=[MinValueValidator(1)],
                help_text="Whole KES charged for each 'Step coins', e.g. 15.",
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="cointype",
            constraint=models.CheckConstraint(check=models.Q(step_coins__gte=1), name="cointype_step_coins_gte_1"),
        ),
        migrations.AddConstraint(
            model_name="cointype",
            constraint=models.CheckConstraint(check=models.Q(step_price_kes__gte=1), name="cointype_step_price_kes_gte_1"),
        ),
        migrations.AddConstraint(
            model_name="cointype",
            constraint=models.CheckConstraint(check=models.Q(min_coins__gte=models.F("step_coins")), name="cointype_min_coins_gte_step_coins"),
        ),
    ]
