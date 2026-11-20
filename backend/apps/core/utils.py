"""
CoinHub core utilities.

Reference format: CH<DDMMYY><SEQUENCE>
Example: CH2605250001, CH2605250002
"""

def generate_reference() -> str:
    """
    Format: CH + DDMMYY + 4-digit zero-padded daily sequence, e.g. CH2605250001.
    The sequence comes from a one-row-per-day counter incremented with a single UPDATE,
    which the database serializes across all workers.
    """
    from django.db import transaction
    from django.db.models import F
    from django.utils import timezone

    from apps.orders.models import Order, OrderReferenceCounter

    today = timezone.localdate()
    prefix = f"CH{today.strftime('%d%m%y')}"

    # Make sure today's row exists. The first call after deployment seeds it from the highest
    # reference already issued today, so the sequence continues instead of restarting at 1.
    if not OrderReferenceCounter.objects.filter(day=today).exists():
        latest = (Order.objects.filter(reference__startswith=prefix)
                  .order_by("-reference").values_list("reference", flat=True).first())
        seed = int(latest[len(prefix):]) if latest else 0
        OrderReferenceCounter.objects.get_or_create(day=today, defaults={"last_value": seed})

    with transaction.atomic():
        OrderReferenceCounter.objects.filter(day=today).update(last_value=F("last_value") + 1)
        sequence = OrderReferenceCounter.objects.get(day=today).last_value

    return f"{prefix}{sequence:04d}"


def normalize_phone(phone: str) -> str:
    """
    Normalise a phone number to the 2547XXXXXXXX format required by Daraja.
    Accepts: 07XXXXXXXX, 7XXXXXXXX, 2547XXXXXXXX, +2547XXXXXXXX
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    if phone.startswith("7") or phone.startswith("1"):
        phone = "254" + phone
    return phone
