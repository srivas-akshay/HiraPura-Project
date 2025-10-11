from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),  # Home / login page
    path("details/<str:phone>/", views.user_details_view, name="details"),
    path("success/", views.success_page, name="success_page"),
    path("upi/<str:token>/", views.upi_redirect_view, name="upi_redirect"),

    # Feedback pages
    path('pre-feedback/', views.pre_event_feedback, name='pre_feedback'),
    path('post-feedback/', views.post_event_feedback, name='post_feedback'),

    # Contact & About
    path("contact-us/", views.contact_us_view, name="contact_us"),
    path("about-us/", views.about_us_view, name="about_us"),

     path("register-event/<int:event_id>/", views.register_event, name="register_event"),
     path("logout/", views.logout_view, name="logout"),

]

