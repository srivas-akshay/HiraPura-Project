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
# Booking Models
# ---------------------------

from django.db import models
class Booking(models.Model):
    contact = models.ForeignKey("Contact", on_delete=models.CASCADE)
    event = models.ForeignKey("Event", on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)

    # fully updateable field
    people_count = models.PositiveIntegerField(default=1)

    # gets recalculated automatically
    amount_paid = models.PositiveIntegerField(default=0)

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # <-- TRACK UPDATES

    PRICE_PER_PERSON = 60  # update pricing here in one place

    def save(self, *args, **kwargs):
        """
        Automatically recalculates amount based on:
        - VIP = always free
        - Normal = people_count × PRICE_PER_PERSON
        """
        if getattr(self.contact, "is_vip", False):
            self.amount_paid = 0
        else:
            self.amount_paid = self.people_count * self.PRICE_PER_PERSON

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking by {self.name} — {self.people_count} people"



class SiteInfo(models.Model):
    # Only one record is needed, so you can enforce it with logic later
    company_name = models.CharField(max_length=200, default="Hirapura Event Portal")
    address = models.TextField(default="Hirapura Village, Community Ground Road, Hirapura, Gujarat, India")
    phone = models.CharField(max_length=20, default="+91 98765 43210")
    email = models.EmailField(default="info@hirapuraevents.com")
    office_hours = models.CharField(max_length=100, default="Monday – Saturday: 9:00 AM – 6:00 PM")
    invitation_image = models.ImageField(upload_to="site_images/", null=True, blank=True)  # optional, for event image

    
    # New About Us fields
    about_title_en = models.CharField(max_length=255, default="About Hirapura Event Portal")
    about_text_en = models.TextField(blank=True, null=True)
    about_text_gu = models.TextField(blank=True, null=True)  # Gujarati text
    about_values = models.JSONField(blank=True, null=True)  # list of value dicts [{icon, title_en, title_gu}]
    
    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = "Site Information"
        verbose_name_plural = "Site Information"






class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)  # Use max_length according to your format
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"
    



class PreFeedback(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    expectations = models.TextField(blank=True)  # JSON string or comma-separated
    additional_message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"
    

class PostFeedback(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)

    rating = models.IntegerField(choices=[(1, "1 ⭐"), (2, "2 ⭐"), (3, "3 ⭐"), (4, "4 ⭐"), (5, "5 ⭐")])
    liked_most = models.TextField(blank=True, null=True)
    improvements = models.TextField(blank=True, null=True)
    additional_message = models.TextField(blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.rating} Stars"