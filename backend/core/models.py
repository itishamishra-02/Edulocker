from django.db import models
from django.contrib.auth.models import User

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=50, unique=True)
    course = models.CharField(max_length=100)
    institute = models.CharField(max_length=150)
    masked_identity = models.CharField(max_length=20, default="XXXX-XXXX-XXXX")  
    wallet_address = models.CharField(max_length=42, blank=True, null=True)     

    def __str__(self):
        return f"{self.student_id} - {self.user.username}"

class AcademicRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='records')
    semester = models.CharField(max_length=20)
    sgpa = models.DecimalField(max_digits=4, decimal_places=2)
    verification_status = models.CharField(max_length=20, default="Pending")

    def __str__(self):
        return f"{self.student.student_id} - Sem {self.semester} (SGPA: {self.sgpa})"

class Certificate(models.Model):
    CERT_TYPES = [
        ('Academic', 'Academic'),
        ('Technical', 'Technical'),
        ('Sports', 'Sports'),
        ('Cultural', 'Cultural'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CERT_TYPES)
    file_path = models.FileField(upload_to='certificates/')
    document_hash = models.CharField(max_length=64, blank=True, null=True) 
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.category})"