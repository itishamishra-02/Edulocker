from django.urls import path
from .views import (
    api_login_view,
    api_logout_view,
    document_asset_api_view,
    document_verification_api_view,
    home_view,
    login_view,
    logout_view,
    student_locker_api_view,
    student_dashboard_view,
    upload_document_view,
    verify_document_view,
)

urlpatterns = [
    path('api/login/', api_login_view, name='api_login'),
    path('api/logout/', api_logout_view, name='api_logout'),
    path('api/student-locker/', student_locker_api_view, name='student_locker_api'),
    path(
        'api/documents/<str:document_id>/<str:asset_type>/',
        document_asset_api_view,
        name='document_asset_api',
    ),
    path(
        'api/verify/',
        document_verification_api_view,
        name='document_verification_api',
    ),
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify/', verify_document_view, name='verify_document'),
    path('student-dashboard/', student_dashboard_view, name='student_dashboard'),
    path('admin-dashboard/', upload_document_view, name='upload_document'),
]