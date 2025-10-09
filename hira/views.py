import secrets
import base64
from io import BytesIO

import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

from .models import Contact, Booking, Event, PhoneOTP
from .forms import PhoneLoginForm
from .utils import can_send_otp, record_send_otp, create_and_dispatch_otp

# -------------------------------
# LOGIN VIA PHONE + OTP
# -------------------------------

def login_view(request):
    form = PhoneLoginForm()
    show_otp = False
    phone = ""

    if request.method == "POST":
        action = request.POST.get("action")
        phone = request.POST.get("phone", "").strip()

        # -------------------------
        # STEP 1: Send OTP
        # -------------------------
        if action == "send_otp":
            try:
                contact = Contact.objects.get(whatsapp_no=phone)
            except Contact.DoesNotExist:
                messages.error(request, "This number is not registered. Please Contact to Admin Mr. Tushar Patel (+91 9924120875 ) ")
                
                return render(request, "home/login.html", {"form": form, "show_otp": False})

            ok, msg = can_send_otp(phone)
            if not ok:
                messages.error(request, msg)
                return render(request, "home/login.html", {"form": form, "show_otp": False})

            success, info = create_and_dispatch_otp(contact)
            if success:
                record_send_otp(phone)
                request.session['otp_contact_id'] = contact.id
                messages.success(request, f"OTP sent to {phone}. Please enter OTP below.")
                show_otp = True
                form = PhoneLoginForm(initial={"phone": phone})
            else:
                messages.error(request, f"Failed to send OTP: {info}")

        # -------------------------
        # STEP 2: Verify OTP
        # -------------------------
        elif action == "verify_otp":
            otp_entered = request.POST.get("otp", "").strip()
            contact_id = request.session.get("otp_contact_id")
            if not contact_id:
                messages.error(request, "Session expired. Please send OTP again.")
                return redirect("login")

            contact = get_object_or_404(Contact, id=contact_id)
            otp_obj = PhoneOTP.objects.filter(contact=contact, used=False).order_by("-created_at").first()

            if not otp_obj:
                messages.error(request, "No valid OTP found. Please resend.")
                return redirect("login")

            if otp_obj.is_expired():
                otp_obj.mark_used()
                messages.error(request, "OTP expired. Please resend OTP.")
                return redirect("login")

            if otp_obj.check_otp(otp_entered):
                otp_obj.mark_used()
                messages.success(request, f"Welcome {contact.full_name}!")
                return redirect("details", phone=contact.whatsapp_no)
            else:
                otp_obj.attempts += 1
                otp_obj.save(update_fields=["attempts"])
                remaining = getattr(settings, "OTP_MAX_ATTEMPTS", 3) - otp_obj.attempts
                messages.error(request, f"Invalid OTP. Remaining attempts: {remaining}")
                show_otp = True
                form = PhoneLoginForm(initial={"phone": phone})

    return render(request, "home/login.html", {
                            "form": form,
                            "show_otp": show_otp,
                            "phone": phone
                         })




# -------------------------------
# USER DETAILS & BOOKING VIEW
# -------------------------------
def user_details_view(request, phone):
    """
    Booking view for logged-in user.
    Handles VIP direct booking and Non-VIP UPI payments.
    """
    contact = get_object_or_404(Contact, whatsapp_no=phone)
    event = Event.objects.last()

    if request.method == "POST":
        try:
            num_people = int(request.POST.get("num_people", 0))
        except ValueError:
            messages.error(request, "Please enter a valid number of people.")
            return redirect("details", phone=phone)

        if num_people <= 0:
            messages.error(request, "કૃપા કરીને યોગ્ય લોકોની સંખ્યા નાખો.")
            return redirect("details", phone=phone)

        total_amount = num_people * 50

        # Create Booking
        booking = Booking.objects.create(
            name=contact.full_name,
            phone=contact.whatsapp_no,
            num_people=num_people,
            total_amount=total_amount,
            is_vip=contact.vip,
            is_paid=True if contact.vip else False,
            event=event,
        )

        # Generate secure token for Non-VIP
        if not contact.vip:
            booking.upi_token = secrets.token_urlsafe(8)
            booking.save()

        # VIP → Direct success
        if contact.vip:
            messages.success(
                request,
                f"🎉 {num_people} લોકો માટે બુકિંગ સફળ!\n\n"
                f"📅 {event.date}, 🕔 {event.time}, 📍 {event.place}\n"
                f"સંપર્ક: {event.admin_name} ({event.admin_phone})"
            )
            return redirect("success_page")

        # Non-VIP → UPI QR + secure redirect
        else:
            upi_id = getattr(settings, "UPI_ID", None)
            if not upi_id:
                messages.error(request, "Payment system not configured.")
                return redirect("details", phone=phone)

            # Generate UPI URL server-side
            upi_url = (
                f"upi://pay?pa={upi_id}&pn=Hirapura%20Event"
                f"&mc=0000&tid={booking.id}&tr={booking.id}"
                f"&tn=Booking%20for%20{num_people}%20people"
                f"&am={total_amount}&cu=INR"
            )

            # Generate QR code as PNG → Base64
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(upi_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()

            return render(
                request,
                "home/payment_qr.html",
                {"booking": booking, "qr_base64": qr_base64, "upi_url": upi_url},
            )

    return render(request, "home/details.html", {"contact": contact, "event": event})


# -------------------------------
# SUCCESS PAGE
# -------------------------------
def success_page(request):
    """
    Generic success page after VIP booking.
    """
    event = Event.objects.last()
    return render(request, "home/success.html", {"event": event})


# -------------------------------
# SECURE UPI REDIRECT
# -------------------------------
def upi_redirect_view(request, token):
    """
    Redirect user securely to UPI URL using server-side token.
    """
    booking = get_object_or_404(Booking, upi_token=token)
    upi_id = getattr(settings, "UPI_ID", None)
    if not upi_id:
        messages.error(request, "Payment system not configured.")
        return redirect("details", phone=booking.phone)

    upi_url = (
        f"upi://pay?pa={upi_id}&pn=Hirapura%20Event"
        f"&mc=0000&tid={booking.id}&tr={booking.id}"
        f"&tn=Booking%20for%20{booking.num_people}%20people"
        f"&am={booking.total_amount}&cu=INR"
    )
    return redirect(upi_url)
