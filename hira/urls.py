from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),  # Home / login page
    path('dashboard/', views.dashboard, name='dashboard'),
  

    
    # Contact & About
     path("contact-us/", views.contact_us_view, name="contact_us"),
     path("about-us/", views.about_us_view, name="about_us"),

    
     path("logout/", views.logout_view, name="logout"),


    path("post-feedback/", views.post_event_feedback_view, name="post_feedback"),
    path("event/<int:event_id>/book/", views.create_booking, name="create_booking"),
    path("booking/<int:booking_id>/payment/", views.payment_page, name="payment_page"),
    path("contact-us/", views.contact_us_view, name="contact_us"),
    path("pre-feedback/", views.pre_feedback_view, name="pre_feedback"),

]




