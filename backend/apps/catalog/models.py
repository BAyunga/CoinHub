"""
CoinHub catalog — CoinType model.

Pricing is stored as exact integers, never as a rounded decimal rate:

    min_coins       smallest purchase allowed
    step_coins      purchases must be a multiple of this many coins
    step_price_kes  whole KES charged for each `step_coins` bought

    amount_kes = (coins / step_coins) * step_price_kes

Example (Poppo): step_coins=8000, step_price_kes=111  ->  8,000 coins = KES 111.
Every payable amount is therefore a whole number of shillings, with no rounding.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimestampedModel


class CoinType(TimestampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    min_coins = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Smallest number of coins a customer can buy. Must be a multiple of 'Step coins'.",
    )
    step_coins = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Coins are sold in multiples of this number, e.g. 1000.",
    )
    step_price_kes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Whole KES charged for each 'Step coins', e.g. 15.",
    )

    icon = models.ImageField(upload_to="catalog/icons/", blank=True, null=True)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Coin Type"
        verbose_name_plural = "Coin Types"
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(step_coins__gte=1), name="cointype_step_coins_gte_1"
            ),
            models.CheckConstraint(
                check=models.Q(step_price_kes__gte=1), name="cointype_step_price_kes_gte_1"
            ),
            models.CheckConstraint(
                check=models.Q(min_coins__gte=models.F("step_coins")),
                name="cointype_min_coins_gte_step_coins",
            ),
        ]

    def __str__(self):
        return self.name

    # ── Pricing helpers ──────────────────────────────────────────────────────
    @property
    def price_per_1000(self) -> Decimal:
        """Display only (admin). Never used to charge a customer."""
        if not self.step_coins:
            return Decimal(0)
        return (Decimal(self.step_price_kes) * 1000 / Decimal(self.step_coins)).quantize(
            Decimal("0.0001")
        )

    def is_valid_quantity(self, coins: int) -> bool:
        return coins >= self.min_coins and coins % self.step_coins == 0

    def calculate_kes(self, coins: int) -> int:
        """Exact KES for `coins`. Raises ValueError for an invalid quantity (never rounds money)."""
        if not self.is_valid_quantity(coins):
            raise ValueError(
                f"{self.name}: {coins} coins is not valid "
                f"(min {self.min_coins}, multiples of {self.step_coins})."
            )
        return (coins // self.step_coins) * self.step_price_kes

    def clean(self):
        super().clean()
        if self.min_coins and self.step_coins:
            if self.min_coins < self.step_coins:
                raise ValidationError({"min_coins": "Minimum cannot be smaller than the step."})
            if self.min_coins % self.step_coins != 0:
                raise ValidationError(
                    {"min_coins": f"Minimum must be a multiple of the step ({self.step_coins:,})."}
                )
