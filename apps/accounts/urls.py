from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    VerifyEmailView,
    ResendVerificationView,
    SocialAuthView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetConfirmView,
    RefreshTokenView,
    LogoutView,
    ProfileView,
    ChangePasswordView
)

app_name = 'accounts'

urlpatterns = [

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('social-auth/', SocialAuthView.as_view(), name='social-auth'),
    

    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    

    path('token/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    

    path('profile/', ProfileView.as_view(), name='get-update-profile'),
    path('profile/change-password/', ChangePasswordView.as_view(), name='change-password'),
]
