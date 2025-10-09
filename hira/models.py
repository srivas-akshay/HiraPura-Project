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
    Feedback given BEFORE attending the event (expectations, travel help, info, etc.)
    """
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, blank=True, null=True, related_name="pre_feedbacks")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="pre_feedbacks")
    submitted_at = models.DateTimeField(default=timezone.now)

    # Core rating / summary
    expected_experience_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                                                  help_text="1-5 rating for expected experience")
    ease_of_registration = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                                            help_text="1-5 registration process ease")
    clarity_of_communications = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                                                 help_text="1-5 clarity of pre-event information")

    # attendance intent + logistics
    will_attend = models.BooleanField(default=True, help_text="Does the person intend to attend?")
    travel_help_needed = models.BooleanField(default=False, help_text="Does the person need travel help?")
    expected_number_of_people = models.PositiveSmallIntegerField(default=1)

    # free text
    expectations = models.TextField(blank=True, help_text="What do you expect from the event?")
    concerns = models.TextField(blank=True, help_text="Any concerns or special requests?")

    # admin helpers
    is_anonymous = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Pre-event feedback"
        verbose_name_plural = "Pre-event feedbacks"

    def __str__(self):
        who = self.contact.full_name if self.contact else "Anonymous"
        return f"PreFeedback: {who} ({self.event})"


class PostEventFeedback(models.Model):
    """
    Feedback after the event (satisfaction, suggestions, rating, would-attend-again)
    """
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, blank=True, null=True, related_name="post_feedbacks")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="post_feedbacks")
    submitted_at = models.DateTimeField(default=timezone.now)

    # core ratings
    overall_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                                      help_text="1-5 overall satisfaction")
    organization_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                                           help_text="1-5 event organization")
    food_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                                   help_text="1-5 food / refreshments")
    venue_rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True,
                                                    help_text="1-5 venue / facilities")

    attended = models.BooleanField(default=True, help_text="Did they actually attend?")
    would_recommend = models.BooleanField(null=True, blank=True, help_text="Would they recommend this event?")

    # free text
    highlights = models.TextField(blank=True, help_text="What did you like most?")
    improvements = models.TextField(blank=True, help_text="What should we improve?")

    # optional follow-up
    allow_contact_for_followup = models.BooleanField(default=False)
    contact_note = models.TextField(blank=True, help_text="If allow_contact_for_followup is True, note preferred follow up method.")

    # admin helpers
    is_anonymous = models.BooleanField(default=False)
    reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Post-event feedback"
        verbose_name_plural = "Post-event feedbacks"

    def __str__(self):
        who = self.contact.full_name if self.contact else "Anonymous"
        return f"PostFeedback: {who} ({self.event})"