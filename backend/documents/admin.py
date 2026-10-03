from django.contrib import admin
from .models import Document, Student, Verification


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
  list_display = ('student_id', 'name', 'email', 'course', 'year')
  search_fields = ('student_id', 'name', 'email')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
  list_display = (
      'document_id',
      'student',
      'document_type',
      'status',
      'uploaded_at',
  )
  list_filter = ('document_type', 'status', 'uploaded_at')
  search_fields = (
      'document_id',
      'student__student_id',
      'student__name',
      'sha256_hash',
  )
  readonly_fields = (
      'sha256_hash',
      'blockchain_tx_hash',
      'status',
      'qr_code_preview',
  )

  def qr_code_preview(self, obj):
    if obj.qr_code:
      return f'<img src="{obj.qr_code.url}" width="150" height="150" />'
    return 'QR Code will be generated upon save.'

  qr_code_preview.allow_tags = True
  qr_code_preview.short_description = 'Generated QR Code'


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
  list_display = ('document', 'verifier', 'result', 'verified_at')
  list_filter = ('result', 'verified_at')
  search_fields = ('document__document_id', 'verifier')