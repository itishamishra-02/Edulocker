import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from .models import Document, Student


class StudentLockerApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='student',
            email='student@example.com',
            password='test-password-123',
        )
        self.student = Student.objects.create(
            student_id='STU-001',
            name='Test Student',
            email='student@example.com',
            course='Computer Science',
            year=2026,
        )
        self.media_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_directory.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

    def test_home_renders_selected_frontend_and_csrf_cookie(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EduChain Student DApp')
        self.assertContains(response, '/static/locker.js')
        self.assertIn('csrftoken', self.client.cookies)

    def test_locker_requires_authentication(self):
        response = self.client.get(reverse('student_locker_api'))

        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {'error': 'Authentication is required.'},
        )

    def test_document_assets_require_authentication(self):
        response = self.client.get(
            reverse(
                'document_asset_api',
                kwargs={'document_id': 'DOC-001', 'asset_type': 'file'},
            )
        )

        self.assertEqual(response.status_code, 401)

    def test_verify_link_opens_the_frontend_verification_page(self):
        response = self.client.get(
            reverse('verify_document'),
            {'document_id': 'DOC-001'},
        )

        self.assertRedirects(
            response,
            '/?page=verify&document_id=DOC-001',
            fetch_redirect_response=False,
        )

    def test_verification_api_reports_unknown_document_ids(self):
        response = self.client.get(
            reverse('document_verification_api'),
            {'document_id': 'DOC-UNKNOWN'},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'error': 'Document not found.'})

    def test_login_and_locker_return_only_the_signed_in_students_profile(self):
        response = self.client.post(
            reverse('api_login'),
            {'username': 'student', 'password': 'test-password-123'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['authenticated'])

        response = self.client.get(reverse('student_locker_api'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'student': {
                    'student_id': self.student.student_id,
                    'name': self.student.name,
                    'email': self.student.email,
                    'course': self.student.course,
                    'year': self.student.year,
                },
                'documents': [],
            },
        )

    def test_locker_does_not_expose_an_unlinked_students_records(self):
        self.user.email = 'unlinked@example.com'
        self.user.save(update_fields=['email'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('student_locker_api'))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {'error': 'No student profile is linked to this account.'},
        )

    def test_locker_returns_document_metadata_and_protected_download(self):
        with patch(
            'documents.blockchain_utils.register_document_on_blockchain',
            side_effect=RuntimeError('Blockchain is offline.'),
        ):
            document = Document.objects.create(
                document_id='DOC-001',
                student=self.student,
                document_type='Marksheet',
                file=SimpleUploadedFile(
                    'marksheet.pdf',
                    b'sample document contents',
                    content_type='application/pdf',
                ),
            )
        self.client.force_login(self.user)

        response = self.client.get(reverse('student_locker_api'))

        self.assertEqual(response.status_code, 200)
        document_data = response.json()['documents'][0]
        self.assertEqual(document_data['document_id'], document.document_id)
        self.assertEqual(document_data['original_filename'], 'marksheet.pdf')
        self.assertEqual(document_data['sha256_hash'], document.sha256_hash)
        self.assertEqual(
            document_data['file_url'],
            reverse(
                'document_asset_api',
                kwargs={'document_id': document.document_id, 'asset_type': 'file'},
            ),
        )

        response = self.client.get(document_data['file_url'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'sample document contents')
