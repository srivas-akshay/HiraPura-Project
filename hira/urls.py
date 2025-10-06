from django.contrib import admin
from django.urls import path
from hira import views  # adjust this if your app name is different

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root URL goes to login
    path('', views.login_view, name='login'),

    # Optional: keep /login/ as well
    path('login/', views.login_view),

    # User details page
    path('details/<str:phone>/', views.user_details_view, name='details'),

    # Success page
    path('success/', views.success_page, name='success_page'),

    # UPI redirect page
    path('upi/<str:token>/', views.upi_redirect_view, name='upi_redirect'),
]