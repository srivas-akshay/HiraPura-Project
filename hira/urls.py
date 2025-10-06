from django.urls import path
from . import views

app_name = "home"  # adjust if needed
urlpatterns = [
    path("login/", views.login_view, name="login"),  # now 'login' reverses correctly
    path("details/<str:phone>/", views.user_details_view, name="details"),
    path("success/", views.success_page, name="success_page"),
    path("upi/<str:token>/", views.upi_redirect_view, name="upi_redirect"),
]