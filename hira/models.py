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