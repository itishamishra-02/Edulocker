from django.urls import path
from . import views

urlpatterns = [
    path('register-student/', views.register_student, name='register-student'),
    path('upload-certificate/', views.upload_certificate_api, name='upload-certificate'),
    path('verify-certificate/', views.verify_certificate_api, name='verify-certificate'),
    path('login/', views.login_api, name='login'),
]