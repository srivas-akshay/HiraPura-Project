from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from .models import Contact, Event, Booking

# ===========================
# Custom AdminSite
# ===========================
class HirapuraAdminSite(AdminSite):
    site_header = " Hirapura Admin Dashboard "       # Navbar title
    site_title = "Hirapura Admin"                       # Browser tab title
    index_title = "Welcome to Hirapura Admin Panel"     # Index page heading

# Instantiate custom admin
hirapura_admin = HirapuraAdminSite(name='hirapura_admin')

# ===========================
# Register built-in auth models
# ===========================
hirapura_admin.register(User)
hirapura_admin.register(Group)

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
# Booking Admin
# ===========================
class BookingAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "upi_token")
    list_display = ('name', 'phone', 'num_people', 'total_amount', 'is_vip', 'is_paid', 'event')
    search_fields = ('name', 'phone', 'event__title')
    list_filter = ('is_vip', 'is_paid', 'event')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Booking Info', {
            'fields': ('name', 'phone', 'num_people', 'total_amount', 'is_vip', 'is_paid')
        }),
        ('Event Info', {
            'fields': ('event',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )

hirapura_admin.register(Booking, BookingAdmin)
