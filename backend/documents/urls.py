from django.urls import path
from .views import (
    home_view,
    login_view,
    logout_view,
    student_dashboard_view,
    upload_document_view,
    verify_document_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('verify/', verify_document_view, name='verify_document'),
    path('student-dashboard/', student_dashboard_view, name='student_dashboard'),
    path('admin-dashboard/', upload_document_view, name='upload_document'),
]