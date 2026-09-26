from django.contrib import admin
from django.urls import path, include

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [

    # Django Admin
    path(
        "admin/",
        admin.site.urls
    ),

    # Module 1: Accounts
    path(
        "api/accounts/",
        include("accounts.urls")
    ),

    # Module 2: Applications
    path(
        "api/applications/",
        include("applications.urls")
    ),

    # JWT Login
    path(
        "api/auth/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    # JWT Refresh
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

]