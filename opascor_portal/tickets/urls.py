from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('',                                  views.login_view,             name='login'),
    path('login/',                            views.login_view,             name='login'),
    path('logout/',                           views.logout_view,            name='logout'),
    path('register/',                         views.register_view,          name='register'),
    path('choose-department/',                views.choose_department_view, name='choose_department'),
    path('dashboard/',                        views.user_dashboard,         name='user_dashboard'),
    path('submit-concern/',                   views.submit_concern,         name='submit_concern'),
    path('admin-dashboard/',                  views.admin_dashboard,        name='admin_dashboard'),
    path('update-concern/<int:concern_id>/',  views.update_concern,         name='update_concern'),
    path('send-message/',  views.send_message,  name='send_message'),
path('inbox/',         views.admin_inbox,   name='admin_inbox'),

    # ── Forgot Password ──
    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='tickets/forgot_password.html',
        email_template_name='tickets/password_reset_email.html',
        subject_template_name='tickets/password_reset_subject.txt',
        success_url='/forgot-password/done/'
    ), name='forgot_password'),

    path('forgot-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='tickets/forgot_password_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='tickets/forgot_password_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='tickets/forgot_password_complete.html'
    ), name='password_reset_complete'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)