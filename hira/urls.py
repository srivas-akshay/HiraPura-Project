from django.urls import path
from . import views

app_name = "home"  # adjust if needed

urlpatterns = [
    path("", views.login_view, name="login"),  # single login page handles both sending and verifying OTP
    path("details/<str:phone>/", views.user_details_view, name="details"),
    path("success/", views.success_page, name="success_page"),
    path("upi/<str:token>/", views.upi_redirect_view, name="upi_redirect"),
]