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
def generate_otp_code(length=4):
    """Generate numeric OTP of given length."""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))

def hash_otp(plain):
    """Hash OTP securely using SHA256."""
    return hashlib.sha256(plain.encode()).hexdigest()

# -------------------------------
# SEND OTP VIA SMS
# -------------------------------
def send_otp_via_sms(phone, otp):
    api_key = getattr(settings, "TWO_FACTOR_API_KEY", None)
    if not api_key:
        return {"Status": "Error", "Details": "API key not configured."}

    template_name = "HiraPuraLogin"  # your approved SMS template
    url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone}/{otp}/{template_name}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        print("2Factor Response:", data)  # optional debug log
        return data
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
    Create OTP record for Contact and send via SMS.
    Marks all previous unused OTPs as used.
    """
    # Mark old OTPs as used
    PhoneOTP.objects.filter(contact=contact, used=False).update(used=True)

    # Generate new OTP
    otp_plain = generate_otp_code(4)  # 4-digit OTP to match template
    hashed = hash_otp(otp_plain)
    expires_at = timezone.now() + timedelta(seconds=getattr(settings, "OTP_EXPIRY_SECONDS", 300))

    otp_obj = PhoneOTP.objects.create(
        contact=contact,
        hashed_otp=hashed,
        expires_at=expires_at
    )

    # Use phone number field for SMS
    phone_number = contact.whatsapp_no or contact.alternate_no
    if not phone_number:
        otp_obj.delete()
        return False, "Phone number not available for SMS"

    # Send OTP
    resp = send_otp_via_sms(phone_number, otp_plain)
    if resp.get("Status") == "Success":
        record_send_otp(phone_number)
        return True, "OTP sent successfully!"
    else:
        otp_obj.delete()
        return False, resp.get("Details") or "Failed to send OTP"
