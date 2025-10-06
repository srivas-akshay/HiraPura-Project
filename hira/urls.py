from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),  # Home page goes to login
    path("details/<str:phone>/", views.user_details_view, name="details"),
    path("success/", views.success_page, name="success_page"),
    path("upi/<str:token>/", views.upi_redirect_view, name="upi_redirect"),
]
