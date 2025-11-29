import secrets
import base64
from io import BytesIO
from functools import wraps

from django.core.mail import send_mail
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import qrcode

from .models import Contact,  Event, PhoneOTP,Booking,SiteInfo,ContactMessage, PreFeedback , PostFeedback
from .forms import PhoneLoginForm
from .utils import can_send_otp, record_send_otp, create_and_dispatch_otp



# -----------------------------------------
# LOGIN  Requierd Decorator
# -----------------------------------------

def contact_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('contact_id'):
            messages.warning(request, "⚠️ Please login first to access this page.")
            return redirect(f"/login/?next={request.get_full_path()}")
        return view_func(request, *args, **kwargs)
    return wrapper
# -----------------------------------------
# LOGIN VIA PHONE + OTP
# -----------------------------------------
def login_view(request):
    form = PhoneLoginForm()
    show_otp = False
    phone = ""
    next_url = request.GET.get("next", "/")  # Redirect after login

    if request.method == "POST":
        action = request.POST.get("action")
        phone = request.POST.get("phone", "").strip()
        next_url = request.POST.get("next_url", next_url)  # preserve next

        # -------------------------
        # STEP 1: Send OTP
        # -------------------------
        if action == "send_otp":
            try:
                contact = Contact.objects.get(whatsapp_no=phone)
            except Contact.DoesNotExist:
                messages.error(request, "This number is not registered. Please contact admin.")
                return render(request, "home/login.html", {
                    "form": form,
                    "show_otp": False,
                    "phone": phone,
                    "next": next_url
                })

            ok, msg = can_send_otp(phone)
            if not ok:
                messages.error(request, msg)
                return render(request, "home/login.html", {
                    "form": form,
                    "show_otp": False,
                    "phone": phone,
                    "next": next_url
                })

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
                request.session['contact_id'] = contact.id
                request.session['contact_phone'] = contact.whatsapp_no
                messages.success(request, f"Welcome {contact.full_name}!")

                # 🔥 Redirect to next if provided
                return redirect(next_url)

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
        "phone": phone,
        "next": next_url
    })




@contact_login_required
def logout_view(request):
    request.session.flush()  # Clear all session data
    messages.success(request, "You have successfully logged out.")
    return redirect("home")



# -----------------------------------------
# BOOKING VIEW
# -----------------------------------------

@contact_login_required
def create_booking(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    contact_id = request.session.get("contact_id")
    contact = get_object_or_404(Contact, id=contact_id)

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        people_count = int(request.POST.get("people_count"))

        # Price calculation (VIP = free)
        price_per_person = 60
        total_amount = 0 if contact.vip else people_count * price_per_person

        booking = Booking.objects.create(
            contact=contact,
            event=event,
            name=name,
            phone=phone,
            people_count=people_count,
            amount_paid=0,              # Initial before real payment
            payment_status="pending"    # ✔ correct field name
        )

        return redirect("payment_page", booking_id=booking.id)

    return render(request, "home/booking.html", {"event": event, "contact": contact})


@contact_login_required 
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    return render(request, "home/payment.html", {"booking": booking})




@csrf_exempt
def payment_success(request):
    booking_id = request.POST.get("booking_id")

    booking = get_object_or_404(Booking, id=booking_id)

    booking.payment_status = "success"
    booking.save()

    return redirect("booking_confirmation", booking_id=booking.id)


@csrf_exempt
def payment_failed(request):
    booking_id = request.POST.get("booking_id")

    booking = get_object_or_404(Booking, id=booking_id)
    booking.payment_status = "failed"
    booking.save()

    return redirect("payment_failed_page")




# -----------------------------------------
# HOME VIEW
# -----------------------------------------
def home_view(request):
    event = Event.objects.first()  # Fetch the first upcoming event
    details_url = None
    button_text = "Login to Register"

    contact_id = request.session.get("contact_id")
    if contact_id and event:
        # Logged-in user → generate booking link
        details_url = reverse("create_booking", args=[event.id])
        # Check if user already has a booking for this event
        try:
            contact = Contact.objects.get(id=contact_id)
            booking = Booking.objects.filter(contact=contact, event=event).first()
            if booking:
                button_text = "Update Booking"
            else:
                button_text = "Register / Book Now"
        except Contact.DoesNotExist:
            button_text = "Register / Book Now"

    return render(request, "home/home.html", {
        "event": event,
        "details_url": details_url,
        "button_text": button_text
    })

# -----------------------------------------
# CONTACT & ABOUT VIEWS
# -----------------------------------------


def contact_us_view(request):
    site_info = SiteInfo.objects.first()

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        message_text = request.POST.get("message")

        # Save in DB
        ContactMessage.objects.create(name=name, phone=phone, message=message_text)

        # Send email notification to admin
        subject = f"New Contact Message from {name}"
        message_body = f"""
        Name: {name}
        Phone: {phone}
        Message: {message_text}
        """
        admin_email = site_info.email  # or any admin email
        send_mail(
            subject,
            message_body,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            fail_silently=False,
        )

        messages.success(request, "Your message has been received. Thank you for reaching out. Our team will get back to you shortly — તમારો સંદેશ પ્રાપ્ત થયો છે. સંપર્ક કરવા બદલ આભાર. અમારી ટીમ ટૂંક સમયમાં તમને સંપર્ક કરશે.")
        return redirect("contact_us")

    return render(request, "home/contact_us.html", {"site_info": site_info})




def about_us_view(request):
    site_info = SiteInfo.objects.first()  # assuming only 1 SiteInfo record
    return render(request, "home/about_us.html", {"site_info": site_info})

# -----------------------------------------
# PRE-EVENT FEEDBACK
# -----------------------------------------

def pre_feedback_view(request):
    site_info = SiteInfo.objects.first()

    expectations_options = [
        "Cultural Performances",
        "Food & Drinks",
        "Networking",
        "Workshops",
        "Other"
    ]

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        expectations = request.POST.getlist("expectations")  # multiple checkboxes
        additional_message = request.POST.get("additional_message")

        PreFeedback.objects.create(
            name=name,
            phone=phone,
            expectations=", ".join(expectations),
            additional_message=additional_message
        )

        messages.success(request, "Your feedback has been submitted successfully!")
        return redirect("pre_feedback")

    return render(request, "home/pre_feedback.html", {
        "site_info": site_info,
        "expectations_options": expectations_options
    })

# -----------------------------------------
# POST-EVENT FEEDBACK
# -----------------------------------------
def post_event_feedback_view(request):
    site_info = SiteInfo.objects.first()

    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        rating = request.POST.get("rating")
        liked_most = request.POST.get("liked_most")
        improvements = request.POST.get("improvements")
        additional_message = request.POST.get("additional_message")

        PostFeedback.objects.create(
            name=name,
            phone=phone,
            rating=rating,
            liked_most=liked_most,
            improvements=improvements,
            additional_message=additional_message,
        )

        messages.success(request, "Thank you! Your experience feedback has been submitted.")
        return redirect("post_feedback")

    return render(request, "home/post_feedback.html", {"site_info": site_info})

@contact_login_required 
def dashboard(request):
    contact = get_object_or_404(Contact, id=request.session["contact_id"])
    bookings = Booking.objects.filter(contact=contact).select_related('event')
    return render(request, "home/dashboard.html", {"contact": contact, "bookings": bookings})