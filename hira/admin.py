from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Contact, Event, SiteInfo, ContactMessage, PreFeedback, PostFeedback
# ===========================
# Custom AdminSite
# ===========================
class HirapuraAdminSite(AdminSite):
    site_header = "Hirapura Admin Dashboard"       # Navbar title
    site_title = "Hirapura Admin"                 # Browser tab title
    index_title = "Welcome to Hirapura Admin Panel"  # Index page heading

# Instantiate custom admin
hirapura_admin = HirapuraAdminSite(name='hirapura_admin')


# ===========================
# Contact Admin
# ===========================
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'whatsapp_no', 'vip', 'area', 'zone', 'family_members', 'email'
    )
    search_fields = ('full_name', 'whatsapp_no', 'alternate_no', 'email', 'area', 'zone')
    list_filter = ('vip', 'zone', 'area')
    list_per_page = 25
    ordering = ('full_name',)
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('full_name', 'sub_cast', 'vip')
        }),
        ('Contact Info', {
            'fields': ('whatsapp_no', 'alternate_no', 'email')
        }),
        ('Address', {
            'fields': ('address', 'area', 'zone', 'family_members')
        }),
    )

hirapura_admin.register(Contact, ContactAdmin)


# ===========================
# Event Admin
# ===========================
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'time', 'place', 'admin_name', 'admin_phone')
    search_fields = ('title', 'place', 'admin_name', 'admin_phone')
    list_filter = ('date', 'place')
    ordering = ('-date',)
    
    fieldsets = (
        ('Event Details', {
            'fields': ('title', 'date', 'time', 'place')
        }),
        ('Admin Contact', {
            'fields': ('admin_name', 'admin_phone')
        }),
    )

hirapura_admin.register(Event, EventAdmin)


# ===========================
# SiteInfo Admin
# ===========================

class SiteInfoAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "phone",
        "email",
        "office_hours",
    )
    search_fields = ("company_name", "email", "phone")
    ordering = ("company_name",)
    
    # Group fields into sections for better admin experience
    fieldsets = (
        ("Basic Info", {
            "fields": ("company_name", "address", "phone", "email", "office_hours", "invitation_image")
        }),
        ("About Us Content", {
            "fields": ("about_title_en", "about_text_en", "about_text_gu", "about_values"),
            "description": "Edit the About Us page content in English and Gujarati. Use JSON for 'about_values'."
        }),
    )

# Register SiteInfo with your custom admin panel
hirapura_admin.register(SiteInfo, SiteInfoAdmin)



# ===========================
# ContactMessage Admin
# ===========================
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'message_excerpt', 'created_at')
    search_fields = ('name', 'phone', 'message')
    list_filter = ('created_at',)
    ordering = ('-created_at',)
    
    def message_excerpt(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_excerpt.short_description = 'Message'

hirapura_admin.register(ContactMessage, ContactMessageAdmin)


# ===========================
# PreFeedback Admin
# ===========================
class PreFeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "get_expectations_display", "additional_message", "submitted_at")
    search_fields = ("name", "phone", "expectations", "additional_message")
    list_filter = ("submitted_at",)
    ordering = ("-submitted_at",)
    list_per_page = 25
    
    fieldsets = (
        ("User Info", {
            "fields": ("name", "phone")
        }),
        ("Expectations / Interests", {
            "fields": ("expectations", "additional_message"),
            "description": "Expectations can include Cultural, Food, Networking, Workshops, or Other."
        }),
    )

    # Optional: Show expectations as readable string if stored as JSON or comma-separated
    def get_expectations_display(self, obj):
        if isinstance(obj.expectations, list):
            return ", ".join(obj.expectations)
        return obj.expectations
    get_expectations_display.short_description = "Expectations"

hirapura_admin.register(PreFeedback, PreFeedbackAdmin)


#  ===========================
# Post Feedback Admin
# ===========================

class PostFeedbackAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "rating", "submitted_at")
    search_fields = ("name", "phone", "liked_most", "improvements")
    list_filter = ("rating", "submitted_at")
    ordering = ("-submitted_at",)
    list_per_page = 25

    fieldsets = (
        ("User Information", {
            "fields": ("name", "phone")
        }),
        ("Experience Feedback", {
            "fields": ("rating", "liked_most", "improvements"),
            "description": "User experience rating + areas they liked and want improved."
        }),
        ("Additional Message", {
            "fields": ("additional_message",),
        }),
    )

# Register using your custom admin site
hirapura_admin.register(PostFeedback, PostFeedbackAdmin)