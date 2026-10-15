from django.urls import path
from .views import CustomerSignupView, CustomerLoginView, CustomerLogoutView

urlpatterns = [
    path('signup/', CustomerSignupView.as_view(), name='customer-signup'),
    path('login/', CustomerLoginView.as_view(), name='customer-login'),
    path('logout/', CustomerLogoutView.as_view(), name='customer-logout'),
]