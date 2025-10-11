from django.db import models
from django.conf import settings
from django.utils import timezone
import hashlib


class Contact(models.Model):
    full_name = models.CharField(max_length=100)
    sub_cast = models.CharField(max_length=50)
    address = models.TextField()
    area = models.CharField(max_length=50)
    zone = models.CharField(max_length=50)
    whatsapp_no = models.CharField(max_length=10, unique=False, blank=True, null=True)
    alternate_no = models.CharField(max_length=10,unique=False, blank=True, null=True)
    family_members = models.IntegerField(default=0)
    email = models.EmailField(unique=False, blank=True, null=True)
    vip = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} ({self.whatsapp_no})"





class Event(models.Model):
    title = models.CharField(max_length=200, default="હિરાપુરા સ્વાગત સમ્મેલન")
    date = models.DateField()
    time = models.TimeField()
    place = models.CharField(max_length=255)
    admin_name = models.CharField(max_length=100)
    admin_phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.title} on {self.date} at {self.time}"


class Booking(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    num_people = models.PositiveIntegerField()
    total_amount = models.PositiveIntegerField()
    is_vip = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Relationship with event (1 event = many bookings)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bookings")
    upi_token = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.num_people} people"
    


 
class PhoneOTP(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="phone_otps", null=True, blank=True)
    hashed_otp = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used = models.BooleanField(default=False)

    def is_expired(self):
        """Check if OTP is expired."""
        return timezone.now() > self.expires_at

    def check_otp(self, plain_otp):
        """Check if the provided OTP matches the hashed OTP."""
        return hashlib.sha256(plain_otp.encode()).hexdigest() == self.hashed_otp

    def mark_used(self):
        """Mark the OTP as used."""
        self.used = True
        self.save(update_fields=["used"])

    def __str__(self):
        return f"OTP for {self.contact.full_name} ({self.contact.whatsapp_no})"
    


    


# ---------------------------
# Feedback Models
# ---------------------------

RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

class PreEventFeedback(models.Model):
    """
    Feedback given before attending the event (expectations, clarity, registration experience, etc.)
    """
    event = models.ForeignKey(
        'Event', on_delete=models.CASCADE, related_name="pre_feedbacks",
        verbose_name="Event"
    )
    contact = models.ForeignKey(
        'Contact', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Contact Person"
    )
    submitted_at = models.DateTimeField(default=timezone.now, verbose_name="Submitted At")

    # Ratings
    expected_experience_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, null=True, blank=True,
        verbose_name="Expected Experience Rating",
        help_text="1–5 rating for expected experience"
    )
    ease_of_registration = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, null=True, blank=True,
        verbose_name="Ease of Registration Rating",
        help_text="1–5 rating for how easy registration was"
    )
    clarity_of_communications = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, null=True, blank=True,
        verbose_name="Clarity of Communication Rating",
        help_text="1–5 rating for how clear event info was"
    )

    # Text feedback
    expectations = models.TextField(
        blank=True, verbose_name="Expectations",
        help_text="What are you expecting from the event?"
    )
    concerns = models.TextField(
        blank=True, verbose_name="Concerns / Questions",
        help_text="Any questions or special requests?"
    )

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Pre-event Feedback"
        verbose_name_plural = "Pre-event Feedbacks"

    def __str__(self):
        who = self.contact.full_name if self.contact else "Anonymous"
        return f"Pre-Event Feedback by {who} for {self.event}"


class PostEventFeedback(models.Model):
    """
    Feedback after the event (satisfaction, highlights, improvement suggestions)
    """
    event = models.ForeignKey(
        'Event', on_delete=models.CASCADE, related_name="post_feedbacks",
        verbose_name="Event"
    )
    contact = models.ForeignKey(
        'Contact', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Contact Person"
    )
    submitted_at = models.DateTimeField(default=timezone.now, verbose_name="Submitted At")

    # Core ratings
    overall_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, null=True, blank=True,
        verbose_name="Overall Satisfaction",
        help_text="1–5 rating for overall satisfaction"
    )
    organization_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, null=True, blank=True,
        verbose_name="Organization Rating",
        help_text="1–5 rating for event organization"
    )
    venue_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, null=True, blank=True,
        verbose_name="Venue Rating",
        help_text="1–5 rating for venue and facilities"
    )
    food_rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES, null=True, blank=True,
        verbose_name="Food Rating",
        help_text="1–5 rating for food / refreshments"
    )

    # Free text feedback
    highlights = models.TextField(
        blank=True, verbose_name="Highlights",
        help_text="What did you like the most about the event?"
    )
    improvements = models.TextField(
        blank=True, verbose_name="Improvements",
        help_text="Any suggestions for improvement?"
    )

    # Optional preference
    would_recommend = models.BooleanField(
        null=True, blank=True, verbose_name="Would Recommend",
        help_text="Would you recommend this event to others?"
    )

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Post-event Feedback"
        verbose_name_plural = "Post-event Feedbacks"

    def __str__(self):
        who = self.contact.full_name if self.contact else "Anonymous"
        return f"Post-event feedback by {who} for {self.event}"