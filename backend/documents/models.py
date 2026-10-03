import hashlib
import io
import qrcode
from django.core.files import File
from django.db import models


class Student(models.Model):
  student_id = models.CharField(max_length=50, unique=True)
  name = models.CharField(max_length=100)
  email = models.EmailField(unique=True)
  course = models.CharField(max_length=100)
  year = models.IntegerField()

  def __str__(self):
    return f"{self.student_id} - {self.name}"


class Document(models.Model):
  DOCUMENT_TYPES = [
      ('Marksheet', 'Marksheet'),
      ('Certificate', 'Certificate'),
      ('Bonafide', 'Bonafide Certificate'),
      ('Internship', 'Internship Certificate'),
      ('Identity', 'Identity Document'),
  ]

  STATUS_CHOICES = [
      ('Pending', 'Pending Blockchain Registration'),
      ('Registered', 'Registered on Blockchain'),
  ]

  document_id = models.CharField(max_length=50, unique=True)
  student = models.ForeignKey(Student, on_delete=models.CASCADE)
  document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
  file = models.FileField(upload_to='documents/')
  original_filename = models.CharField(max_length=255, blank=True)
  uploaded_at = models.DateTimeField(auto_now_add=True)
  sha256_hash = models.CharField(max_length=64, blank=True, editable=False)
  blockchain_tx_hash = models.CharField(max_length=100, blank=True, null=True)
  status = models.CharField(
      max_length=20, choices=STATUS_CHOICES, default='Pending'
  )
  qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

  def save(self, *args, **kwargs):
    if self.file and not self.original_filename:
      self.original_filename = self.file.name.split('/')[-1]

    is_new = self.pk is None
    if self.file and not self.sha256_hash:
      sha256 = hashlib.sha256()
      for chunk in self.file.chunks():
        sha256.update(chunk)
      self.sha256_hash = sha256.hexdigest()

    # Automatically generate QR code if it doesn't exist yet
    if not self.qr_code and self.document_id:
      verify_url = f'http://127.0.0.1:8000/verify/?document_id={self.document_id}'
      qr = qrcode.make(verify_url)
      buffer = io.BytesIO()
      qr.save(buffer, format='PNG')
      self.qr_code.save(
          f'qr_{self.document_id}.png',
          File(buffer),
          save=False,
      )

    super().save(*args, **kwargs)

    if (
        is_new
        and self.status == 'Pending'
        and self.sha256_hash
        and not self.blockchain_tx_hash
    ):
      try:
        from .blockchain_utils import register_document_on_blockchain

        tx_hash = register_document_on_blockchain(
            document_id=self.document_id,
            student_id=self.student.student_id,
            document_hash=self.sha256_hash,
        )
        Document.objects.filter(pk=self.pk).update(
            blockchain_tx_hash=tx_hash, status='Registered'
        )
      except Exception as e:
        print(f'Blockchain registration failed: {e}')

  def __str__(self):
    return f'{self.document_id} ({self.document_type})'


class Verification(models.Model):
  document = models.ForeignKey(Document, on_delete=models.CASCADE)
  verified_at = models.DateTimeField(auto_now_add=True)
  verifier = models.CharField(max_length=100, blank=True, null=True)
  submitted_hash = models.CharField(max_length=64)
  result = models.BooleanField()

  def __str__(self):
    status_text = 'Valid' if self.result else 'Tampered/Invalid'
    return f'Verification for {self.document.document_id} - {status_text}'