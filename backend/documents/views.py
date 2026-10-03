from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from .blockchain_utils import verify_document_on_blockchain
from .models import Document, Student, Verification


def home_view(request):
    return render(request, 'index.html')


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
    context = {}
    document_id = request.POST.get('document_id') or request.GET.get(
        'document_id'
    )

    if document_id:
        document = Document.objects.filter(document_id=document_id).first()

        if document:
            try:
                result = verify_document_on_blockchain(
                    document_hash=document.sha256_hash,
                )
                context['success'] = True
                context['result'] = result
                context['document'] = document

                Verification.objects.create(
                    document=document,
                    submitted_hash=document.sha256_hash,
                    result=result.get('isValid', False),
                    verifier='Public Portal',
                )
            except Exception as e:
                context['error'] = f'Blockchain verification error: {e}'
        else:
            context['error'] = (
                f"No document found with ID '{document_id}'. Please check and try"
                ' again.'
            )

    return render(request, 'verify.html', context)


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