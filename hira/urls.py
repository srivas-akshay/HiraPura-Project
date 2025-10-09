from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),  # Home / login page
    path("details/<str:phone>/", views.user_details_view, name="details"),
    path("success/", views.success_page, name="success_page"),
    path("upi/<str:token>/", views.upi_redirect_view, name="upi_redirect"),

    # Feedback pages
    path("pre-feedback/", views.pre_feedback_view, name="pre_feedback"),
    path("post-feedback/", views.post_feedback_view, name="post_feedback"),

    # Contact & About
    path("contact-us/", views.contact_us_view, name="contact_us"),
    path("about-us/", views.about_us_view, name="about_us"),
]