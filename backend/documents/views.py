from urllib.parse import urlencode

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import FileResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from .blockchain_utils import verify_document_on_blockchain
from .models import Document, Student, Verification


@ensure_csrf_cookie
def home_view(request):
    return render(request, 'index1.html')


@require_POST
def api_login_view(request):
    form = AuthenticationForm(request, data=request.POST)
    if not form.is_valid():
        return JsonResponse(
            {'error': 'Invalid username or password.'},
            status=400,
        )

    login(request, form.get_user())
    return JsonResponse({'authenticated': True})


@require_POST
def api_logout_view(request):
    logout(request)
    return JsonResponse({'authenticated': False})


@require_GET
def student_locker_api_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication is required.'}, status=401)

    student = Student.objects.filter(email=request.user.email).first()
    if student is None:
        return JsonResponse(
            {'error': 'No student profile is linked to this account.'},
            status=404,
        )

    documents = Document.objects.filter(student=student).order_by(
        '-uploaded_at'
    )
    return JsonResponse(
        {
            'student': {
                'student_id': student.student_id,
                'name': student.name,
                'email': student.email,
                'course': student.course,
                'year': student.year,
            },
            'documents': [
                {
                    'document_id': document.document_id,
                    'document_type': document.document_type,
                    'original_filename': document.original_filename,
                    'uploaded_at': document.uploaded_at.isoformat(),
                    'status': document.status,
                    'sha256_hash': document.sha256_hash,
                    'blockchain_tx_hash': document.blockchain_tx_hash,
                    'file_url': (
                        reverse(
                            'document_asset_api',
                            kwargs={
                                'document_id': document.document_id,
                                'asset_type': 'file',
                            },
                        )
                        if document.file
                        else None
                    ),
                    'qr_code_url': (
                        reverse(
                            'document_asset_api',
                            kwargs={
                                'document_id': document.document_id,
                                'asset_type': 'qr',
                            },
                        )
                        if document.qr_code
                        else None
                    ),
                }
                for document in documents
            ],
        }
    )


@require_GET
def document_asset_api_view(request, document_id, asset_type):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication is required.'}, status=401)

    document = Document.objects.filter(
        document_id=document_id,
        student__email=request.user.email,
    ).first()
    if document is None:
        return JsonResponse({'error': 'Document not found.'}, status=404)

    if asset_type == 'file' and document.file:
        return FileResponse(
            document.file.open('rb'),
            as_attachment=True,
            filename=document.original_filename or document.file.name.rsplit('/', 1)[-1],
        )
    if asset_type == 'qr' and document.qr_code:
        return FileResponse(
            document.qr_code.open('rb'),
            content_type='image/png',
        )
    return JsonResponse({'error': 'Document asset not found.'}, status=404)


@require_GET
def document_verification_api_view(request):
    document_id = request.GET.get('document_id', '').strip()
    if not document_id:
        return JsonResponse({'error': 'A document ID is required.'}, status=400)

    document = Document.objects.filter(document_id=document_id).first()
    if document is None:
        return JsonResponse({'error': 'Document not found.'}, status=404)

    result = verify_document_on_blockchain(document_hash=document.sha256_hash)
    is_valid = result.get('isValid', False)
    Verification.objects.create(
        document=document,
        submitted_hash=document.sha256_hash,
        result=is_valid,
        verifier='Public Portal',
    )
    return JsonResponse(
        {
            'document_id': document.document_id,
            'is_valid': is_valid,
            'error': result.get('error'),
        }
    )


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirect based on user role or default to dashboard
            if user.is_staff:
                return redirect('upload_document')
            else:
                return redirect('student_dashboard')
        else:
            return render(
                request,
                'login.html',
                {'form': form, 'error': 'Invalid username or password.'},
            )
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


def verify_document_view(request):
    document_id = request.POST.get('document_id') or request.GET.get(
        'document_id'
    )
    query = urlencode(
        {'page': 'verify', 'document_id': document_id}
        if document_id
        else {'page': 'verify'}
    )
    return redirect(f'{reverse("home")}?{query}')


@login_required(login_url='/login/')
def student_dashboard_view(request):
    student_id = request.GET.get('student_id', '001')
    student = Student.objects.filter(student_id=student_id).first()
    documents = Document.objects.filter(student=student) if student else []

    context = {
        'student': student,
        'documents': documents,
    }
    return render(request, 'student-dashboard.html', context)


@login_required(login_url='/login/')
def upload_document_view(request):
    students = Student.objects.all()
    context = {'students': students}

    if request.method == 'POST':
        document_id = request.POST.get('document_id')
        student_id = request.POST.get('student_id')
        document_type = request.POST.get('document_type')
        file = request.FILES.get('file')

        if not document_id or not student_id or not file:
            context['error'] = 'All fields are required.'
            return render(request, 'admin-dashboard.html', context)

        if Document.objects.filter(document_id=document_id).exists():
            context['error'] = f"Document ID '{document_id}' already exists."
            return render(request, 'admin-dashboard.html', context)

        try:
            student = Student.objects.get(student_id=student_id)
            # Creating the document automatically triggers hashing, QR generation, and blockchain registration via models.py save()
            Document.objects.create(
                document_id=document_id,
                student=student,
                document_type=document_type,
                file=file,
            )
            context['success'] = (
                'Document successfully issued and anchored on the blockchain!'
            )
        except Exception as e:
            context['error'] = f'Issuance failed: {e}'

    return render(request, 'admin-dashboard.html', context)