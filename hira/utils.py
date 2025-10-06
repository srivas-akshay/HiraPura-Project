import secrets
import hashlib
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
import requests

from .models import PhoneOTP, Contact

# -------------------------------
# OTP GENERATION & HASHING
# -------------------------------
def generate_otp_code(length=6):
    """Generate numeric OTP of given length."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))

def hash_otp(plain):
    """Hash OTP securely using SHA256."""
    return hashlib.sha256(plain.encode()).hexdigest()

# -------------------------------
# SEND OTP VIA 2FACTOR API
# -------------------------------
def send_otp_via_2factor(phone, otp):
    api_key = getattr(settings, "TWO_FACTOR_API_KEY", None)
    if not api_key:
        return {"Status": "Error", "Details": "API key not configured."}

    # Use SMS endpoint with your approved template
    template_name = "HiraPuraLogin"
    url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone}/{template_name}"
    
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except Exception as e:
        return {"Status": "Error", "Details": str(e)}

# -------------------------------
# RATE LIMIT CHECK
# -------------------------------
def can_send_otp(phone):
    """
    Returns (True, "") if OTP can be sent, else (False, "reason").
    Enforces cooldown and hourly limits.
    """
    cooldown_key = f"otp_cd_{phone}"
    hourly_key = f"otp_hour_{phone}"

    if cache.get(cooldown_key):
        return False, "Cooldown active. Try again later."

    hour_count = cache.get(hourly_key) or 0
    if hour_count >= getattr(settings, "OTP_RESEND_MAX_PER_HOUR", 5):
        return False, "Resend limit reached for this hour."

    return True, ""

def record_send_otp(phone):
    """Record that an OTP was sent: update cooldown and hourly counters."""
    cooldown_key = f"otp_cd_{phone}"
    hourly_key = f"otp_hour_{phone}"

    cache.set(cooldown_key, 1, timeout=getattr(settings, "OTP_RESEND_COOLDOWN", 60))
    hour_count = cache.get(hourly_key) or 0
    cache.set(hourly_key, hour_count + 1, timeout=3600)

# -------------------------------
# CREATE & DISPATCH OTP
# -------------------------------
def create_and_dispatch_otp(contact: Contact):
    """
    Create OTP record for Contact and send via 2factor API.
    Marks all previous unused OTPs as used.
    """
    # Mark old OTPs as used
    PhoneOTP.objects.filter(contact=contact, used=False).update(used=True)

    # Generate new OTP
    otp_plain = generate_otp_code(6)
    hashed = hash_otp(otp_plain)
    expires_at = timezone.now() + timedelta(seconds=getattr(settings, "OTP_EXPIRY_SECONDS", 300))

    otp_obj = PhoneOTP.objects.create(
        contact=contact,
        hashed_otp=hashed,
        expires_at=expires_at
    )

    # Send OTP via SMS
    resp = send_otp_via_2factor(contact.whatsapp_no, otp_plain)
    if resp.get("Status") == "Success":
        return True, "OTP sent successfully!"
    else:
        otp_obj.delete()
        return False, resp.get("Details") or "Failed to send OTP"
