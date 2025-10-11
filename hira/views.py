import secrets
import base64
from io import BytesIO
from functools import wraps

from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse

import qrcode

from .models import Contact, Booking, Event, PhoneOTP
from .forms import PhoneLoginForm, PreEventFeedbackForm, PostEventFeedbackForm
from .utils import can_send_otp, record_send_otp, create_and_dispatch_otp



# -----------------------------------------
# LOGIN  Requierd Decorator
# -----------------------------------------


def contact_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('contact_id'):
            messages.warning(request, "⚠️ Please login first to access this page.")
            # Redirect to login with next parameter
            return redirect(f"/login/?next={request.path}")
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

        # -------------------------
        # STEP 1: Send OTP
        # -------------------------
        if action == "send_otp":
            try:
                contact = Contact.objects.get(whatsapp_no=phone)
            except Contact.DoesNotExist:
                messages.error(request, "This number is not registered. Please contact admin.")
                return render(request, "home/login.html", {"form": form, "show_otp": False, "phone": phone})

            ok, msg = can_send_otp(phone)
            if not ok:
                messages.error(request, msg)
                return render(request, "home/login.html", {"form": form, "show_otp": False, "phone": phone})

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
                # ✅ Set contact_id in session
                request.session['contact_id'] = contact.id
                messages.success(request, f"Welcome {contact.full_name}!")
                return redirect('home')
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
# USER DETAILS & BOOKING VIEW
# -----------------------------------------
@contact_login_required
def user_details_view(request, phone):
    """
    Booking view for logged-in users.
    Handles VIP direct booking and Non-VIP bookings without QR code.
    """
    contact = get_object_or_404(Contact, whatsapp_no=phone)
    event = Event.objects.last()  # Get latest event

    if request.method == "POST":

        # Validate number of people
        try:
            num_people = int(request.POST.get("num_people", 0))
        except ValueError:
            messages.error(request, "Please enter a valid number of people.")
            return redirect("details", phone=phone)

        if num_people <= 0:
            messages.error(request, "કૃપા કરીને યોગ્ય લોકોની સંખ્યા નાખો.")  # Gujarati message
            return redirect("details", phone=phone)

        total_amount = num_people * 50  # Calculate total amount

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

        # Generate secure token for Non-VIP users (if needed for future)
        if not contact.vip:
            booking.upi_token = secrets.token_urlsafe(8)
            booking.save()

        # VIP users → Direct success
        messages.success(
            request,
            f"🎉 {num_people} લોકો માટે બુકિંગ સફળ!\n\n"
            f"📅 {event.date}, 🕔 {event.time}, 📍 {event.place}\n"
            f"સંપર્ક: {event.admin_name} ({event.admin_phone})"
        )
        return redirect("success_page")

    # Render details page
    return render(request, "home/details.html", {"contact": contact, "event": event})
# -----------------------------------------
# SUCCESS PAGE
# -----------------------------------------
def success_page(request):
    """
    Generic success page after VIP booking.
    """
    event = Event.objects.last()
    return render(request, "home/success.html", {"event": event})


# -----------------------------------------
# SECURE UPI REDIRECT
# -----------------------------------------
@contact_login_required
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


# -----------------------------------------
# HOME VIEW
# -----------------------------------------

def home_view(request):
    event = Event.objects.first()
    if request.session.get('otp_contact_id'):
        contact_id = request.session['otp_contact_id']
        contact = Contact.objects.get(id=contact_id)
        details_url = reverse('details', kwargs={'phone': contact.whatsapp_no})
    else:
        details_url = None
    return render(request, "home/home.html", {"event": event, "details_url": details_url})\
    
# -----------------------------------------
# CONTACT & ABOUT VIEWS
# -----------------------------------------
def contact_us_view(request):
    """Display Contact Us page."""
    return render(request, "home/contact_us.html")


def about_us_view(request):
    """Display About Us page."""
    return render(request, "home/about_us.html")


# -----------------------------------------
# PRE-EVENT FEEDBACK
# -----------------------------------------
@contact_login_required
def pre_event_feedback(request):
    """
    Collect feedback from users before event starts.
    """
    if request.method == "POST":
        form = PreEventFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.contact = request.user.contact if hasattr(request.user, "contact") else None
            feedback.submitted_at = timezone.now()
            feedback.save()
            return redirect("pre_feedback_success")
    else:
        form = PreEventFeedbackForm()

    return render(request, "home/pre_feedback.html", {
        "form": form,
        "now": timezone.now()
    })


# -----------------------------------------
# POST-EVENT FEEDBACK
# -----------------------------------------
@contact_login_required
def post_event_feedback(request):
    """
    Collect feedback from users after event ends.
    """
    if request.method == "POST":
        form = PostEventFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.contact = request.user.contact if hasattr(request.user, "contact") else None
            feedback.submitted_at = timezone.now()
            feedback.save()
            return redirect("post_feedback_success")
    else:
        form = PostEventFeedbackForm()

    return render(request, "home/post_feedback.html", {
        "form": form,
        "now": timezone.now()
    })


# -----------------------------------------
# EVENT REGISTRATION VIEW
# -----------------------------------------
@contact_login_required
def register_event(request, event_id):
    contact_id = request.session.get('contact_id')
    contact = get_object_or_404(Contact, id=contact_id)
    event = get_object_or_404(Event, id=event_id)

    # Check if already registered
    if Booking.objects.filter(phone=contact.whatsapp_no, event=event).exists():
        messages.info(request, f"You are already registered for {event.title}")
        return redirect("home")

    Booking.objects.create(
        name=contact.full_name,
        phone=contact.whatsapp_no,
        num_people=1,  # default, or from form
        total_amount=50,
        is_vip=contact.vip,
        is_paid=contact.vip,  # VIP auto paid
        event=event
    )
    messages.success(request, f"Registered successfully for {event.title}")
    return redirect("home")