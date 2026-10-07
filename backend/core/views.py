from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Certificate, StudentProfile
from .blockchain import generate_sha256, register_hash_on_chain

@csrf_exempt
def upload_certificate_api(request):
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_id')
            title = request.POST.get('title')
            category = request.POST.get('category')
            uploaded_file = request.FILES.get('file')

            if not all([student_id, title, category, uploaded_file]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Get student profile (ensure student exists first)
            try:
                student = StudentProfile.objects.get(student_id=student_id)
            except StudentProfile.DoesNotExist:
                return JsonResponse({'error': 'Student ID not found in database'}, status=404)

            # 1. Generate SHA-256 Hash
            doc_hash = generate_sha256(uploaded_file)

            # 2. Save certificate locally in Django database
            certificate = Certificate.objects.create(
                student=student,
                title=title,
                category=category,
                file_path=uploaded_file,
                document_hash=doc_hash
            )

            # 3. Record Hash on Blockchain via Ganache
            receipt = register_hash_on_chain(doc_hash, student_id, title)

            return JsonResponse({
                'message': 'Document uploaded and registered on blockchain successfully!',
                'document_hash': doc_hash,
                'transaction_hash': receipt.transactionHash.hex()
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)
from .blockchain import verify_hash_on_chain

@csrf_exempt
def verify_certificate_api(request):
    if request.method == 'POST':
        try:
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return JsonResponse({'error': 'No file provided for verification'}, status=400)

            # 1. Generate hash from the submitted verification file
            doc_hash = generate_sha256(uploaded_file)

            # 2. Check authenticity on the blockchain
            chain_data = verify_hash_on_chain(doc_hash)

            if chain_data["is_authentic"]:
                return JsonResponse({
                    'status': 'Authentic',
                    'message': 'Document is verified and matches the blockchain record!',
                    'document_hash': doc_hash,
                    'student_id': chain_data["student_id"],
                    'document_title': chain_data["document_title"],
                    'issuer': chain_data["issuer"],
                    'timestamp': chain_data["timestamp"]
                }, status=200)
            else:
                return JsonResponse({
                    'status': 'Not Verified',
                    'message': 'Document hash does not exist on the blockchain or has been tampered with.',
                    'document_hash': doc_hash
                }, status=404)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)
from django.http import JsonResponse

def home_view(request):
    return JsonResponse({
        "project": "EduLocker API",
        "status": "Running",
        "endpoints": {
            "upload": "/api/upload-certificate/",
            "verify": "/api/verify-certificate/"
        }
    })
    
@csrf_exempt
def register_student(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')
            full_name = data.get('full_name')
            email = data.get('email')
            course = data.get('course')
            college = data.get('college')
            admission_year = data.get('admission_year')
            password = data.get('password')

            if not all([student_id, full_name, email, password]):
                return JsonResponse({'error': 'Missing required registration fields'}, status=400)

            if StudentProfile.objects.filter(student_id=student_id).exists():
                return JsonResponse({'error': 'Student ID already exists'}, status=400)

            StudentProfile.objects.create(
                student_id=student_id,
                full_name=full_name,
                email=email,
                course=course,
                college=college,
                admission_year=admission_year,
                password=password
            )

            return JsonResponse({'message': 'Student registered successfully in database!'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            student = StudentProfile.objects.filter(email=email, password=password).first()
            if student:
                return JsonResponse({'message': 'Login successful', 'student_id': student.student_id}, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid HTTP method'}, status=405)