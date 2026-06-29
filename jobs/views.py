import re
import fitz
import docx
from datetime import datetime

from django.db.models import Q
from django.contrib.auth.models import User
from django.core.paginator import Paginator

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import (
    Employer, Seeker, Category, Job, Application, Favorite, Chat, Message,
    Notification, Skill, ResumeAnalysis, JobMatch, Report, SearchQuery
)
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    EmployerSerializer, SeekerSerializer, CategorySerializer, JobSerializer,
    ApplicationSerializer, FavoriteSerializer, ChatSerializer, MessageSerializer,
    RegisterSerializer, NotificationSerializer, ResumeAnalysisSerializer,
    JobMatchSerializer, ReportSerializer, AdminStatsSerializer, RegisterResponseSerializer,
    JobSearchSerializer, MatchJobsResponseSerializer, ResumeAnalysisResponseSerializer,
    NotificationListResponseSerializer, ReportUserSerializer, ReportJobSerializer,
    MyTokenObtainPairSerializer, ChangePasswordSerializer
)


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class EmployerViewSet(viewsets.ModelViewSet):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'company_name', 'location', 'about']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Employer.objects.all()
        return Employer.objects.filter(
            Q(is_verified=True) | Q(user=user)
        )


class SeekerViewSet(viewsets.ModelViewSet):
    queryset = Seeker.objects.all()
    serializer_class = SeekerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'bio', 'address', 'education']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.filter(is_deleted=False)
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering = ['-created_at']
    filterset_fields = ['job_type', 'workplace_type', 'category', 'location', 'company']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        # Superusers see all non-deleted jobs
        if user.is_authenticated and user.is_superuser:
            queryset = Job.objects.filter(is_deleted=False)
        # Employers can see their own jobs (including inactive)
        elif user.is_authenticated and hasattr(user, 'employer_profile'):
            queryset = Job.objects.filter(is_deleted=False, company=user.employer_profile)
        # Seekers and unauthenticated users only see active jobs
        else:
            queryset = Job.objects.filter(is_deleted=False, is_active=True)

        min_salary = self.request.query_params.get('min_salary')
        max_salary = self.request.query_params.get('max_salary')
        min_experience = self.request.query_params.get('min_experience')

        if min_salary:
            queryset = queryset.filter(salary_min__gte=min_salary)
        if max_salary:
            queryset = queryset.filter(salary_max__lte=max_salary)
        if min_experience:
            queryset = queryset.filter(experience_required__lte=min_experience)

        return queryset.select_related('company', 'category').prefetch_related('skills_required')

    def perform_create(self, serializer):
        try:
            employer = self.request.user.employer_profile
        except Employer.DoesNotExist:
            raise serializers.ValidationError({"detail": "User must have an employer profile to post jobs."})
        serializer.save(company=employer)

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({'results': []})

        SearchQuery.objects.create(query=query, results_count=0)

        queryset = Job.objects.filter(is_deleted=False, is_active=True)
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query) |
            Q(category__name__icontains=query) |
            Q(skills_required__name__icontains=query)
        ).distinct()

        paginator = Paginator(queryset, 20)
        page = request.query_params.get('page', 1)
        results = paginator.get_page(page)

        SearchQuery.objects.filter(query=query).update(results_count=len(queryset))

        return Response({
            'results': JobSerializer(results, many=True).data,
            'total': queryset.count(),
            'page': int(page),
            'pages': paginator.num_pages
        })


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.filter(is_deleted=False)
    serializer_class = ApplicationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'job', 'user']
    ordering = ['-created_at']

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Application.objects.filter(is_deleted=False)
        if hasattr(user, 'employer_profile'):
            return Application.objects.filter(is_deleted=False, job__company=user.employer_profile)
        return Application.objects.filter(is_deleted=False, user=user)

    def perform_create(self, serializer):
        application = serializer.save(user=self.request.user)
        self.create_notification(application)

    def create_notification(self, application):
        Notification.objects.create(
            user=application.job.company.user,
            notification_type='application_new',
            title='New Application',
            message=f'{application.user.username} applied to your job: {application.job.title}',
            link=f'/jobs/{application.job.id}'
        )


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.filter(is_deleted=False)
    serializer_class = FavoriteSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user, is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['-created_at']

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(Q(user1=user) | Q(user2=user), is_active=True)

    def create(self, request, *args, **kwargs):
        user1_id = request.data.get('user1')
        user2_id = request.data.get('user2')
        if not user1_id or not user2_id:
            return Response({'error': 'Both user1 and user2 are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        chat = Chat.objects.filter(
            (Q(user1_id=user1_id) & Q(user2_id=user2_id)) |
            (Q(user1_id=user2_id) & Q(user2_id=user1_id))
        ).first()
        
        if chat:
            serializer = self.get_serializer(chat)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        return super().create(request, *args, **kwargs)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['chat']
    ordering = ['created_at']

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(chat__in=Chat.objects.filter(Q(user1=user) | Q(user2=user)))

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


@extend_schema(request=RegisterSerializer, responses=RegisterResponseSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        is_seeker = getattr(serializer, '_is_seeker', True)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': 'seeker' if is_seeker else 'employer',
                'is_seeker': is_seeker
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=ChangePasswordSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    if not user.check_password(serializer.validated_data['old_password']):
        return Response({'old_password': ['Current password is incorrect.']}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(serializer.validated_data['new_password'])
    user.save()
    return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


@extend_schema(request=SeekerSerializer, responses=SeekerSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_seeker_profile(request):
    user = request.user
    if Seeker.objects.filter(user=user).exists():
        return Response({'error': 'Profile already exists'}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()
    data['user'] = user.id
    data['is_created'] = True

    serializer = SeekerSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=EmployerSerializer, responses=EmployerSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_employer_profile(request):
    user = request.user
    if Employer.objects.filter(user=user).exists():
        return Response({'error': 'Profile already exists'}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()
    data['user'] = user.id
    data['is_created'] = True

    serializer = EmployerSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(responses=NotificationListResponseSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    return Response({
        'notifications': NotificationSerializer(notifications[:50], many=True).data,
        'unread_count': unread_count
    })


@extend_schema(responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'message': 'All notifications marked as read'})


@extend_schema(responses={200: None})
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, user=request.user)
        notification.delete()
        return Response({'message': 'Notification deleted'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(responses=ResumeAnalysisResponseSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_resume(request):
    if 'resume' not in request.FILES:
        return Response({'error': 'No resume file provided'}, status=status.HTTP_400_BAD_REQUEST)

    resume_file = request.FILES['resume']
    text_content = ''

    if resume_file.name.endswith('.pdf'):
        text_content = extract_pdf_text(resume_file)
    elif resume_file.name.endswith('.docx'):
        text_content = extract_docx_text(resume_file)
    elif resume_file.name.endswith('.txt'):
        text_content = resume_file.read().decode('utf-8')
    else:
        return Response({'error': 'Unsupported file format'}, status=status.HTTP_400_BAD_REQUEST)

    analysis = analyze_resume_content(text_content)

    seeker, _ = Seeker.objects.get_or_create(user=request.user)
    resume_analysis = ResumeAnalysis.objects.create(
        seeker=seeker,
        original_resume=resume_file,
        extracted_text=text_content[:5000],
        skills_found=analysis.get('skills', []),
        experience_years=analysis.get('experience_years', 0),
        education_level=analysis.get('education_level', ''),
        job_titles=analysis.get('job_titles', []),
        technologies=analysis.get('technologies', []),
        languages=analysis.get('languages', []),
        certifications=analysis.get('certifications', [])
    )

    experience_text = f"{analysis.get('experience_years', 0)} years"
    if analysis.get('job_titles'):
        experience_text += f" as {', '.join(analysis['job_titles'])}"

    return Response({
        'analysis_id': resume_analysis.id,
        'skills': analysis.get('skills', []),
        'experience_years': analysis.get('experience_years', 0),
        'education_level': analysis.get('education_level', ''),
        'experience': experience_text,
        'education': analysis.get('education_level', ''),
        'recommendations': [],
        'job_titles': analysis.get('job_titles', []),
        'technologies': analysis.get('technologies', []),
        'languages': analysis.get('languages', []),
        'certifications': analysis.get('certifications', [])
    })


def extract_pdf_text(file):
    doc = fitz.open(stream=file.read(), filetype='pdf')
    text = ''
    for page in doc:
        text += page.get_text()
    return text


def extract_docx_text(file):
    doc = docx.Document(file)
    text = ''
    for para in doc.paragraphs:
        text += para.text + '\n'
    return text


def analyze_resume_content(text):
    skills = []
    experience_years = 0
    education_level = ''
    job_titles = []
    technologies = []
    languages = []
    certifications = []

    tech_patterns = ['python', 'java', 'javascript', 'react', 'django', 'node.js', 'angular', 'vue', 'docker', 'kubernetes', 'aws', 'azure', 'sql', 'mongodb', 'postgresql', 'mysql']
    extracted_tech = [t for t in tech_patterns if t.lower() in text.lower()]
    technologies.extend(extracted_tech)

    skill_patterns = ['management', 'communication', 'leadership', 'teamwork', 'problem solving', 'analytical']
    extracted_skills = [s for s in skill_patterns if s.lower() in text.lower()]
    skills.extend(extracted_skills)

    exp_match = re.search(r'(\d+)\s*(?:years?|yrs?)\s*(?:of)?\s*experience', text, re.IGNORECASE)
    if exp_match:
        experience_years = int(exp_match.group(1))

    edu_patterns = ['bachelor', 'master', 'phd', 'degree', 'university', 'college']
    for pattern in edu_patterns:
        if pattern.lower() in text.lower():
            education_level = pattern.title()
            break

    lang_patterns = ['english', 'spanish', 'french', 'german', 'chinese', 'arabic']
    for lang in lang_patterns:
        if lang.lower() in text.lower():
            languages.append(lang.title())

    cert_patterns = ['certified', 'certificate', 'certification', 'aws certified', 'google certified', 'scrum master']
    for cert in cert_patterns:
        if cert.lower() in text.lower():
            certifications.append(cert)

    title_patterns = ['developer', 'engineer', 'manager', 'designer', 'analyst', 'consultant', 'architect']
    for title in title_patterns:
        if title.lower() in text.lower():
            job_titles.append(title.title())

    return {
        'skills': skills,
        'experience_years': experience_years,
        'education_level': education_level,
        'job_titles': job_titles,
        'technologies': technologies,
        'languages': languages,
        'certifications': certifications
    }


@extend_schema(responses=MatchJobsResponseSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def match_jobs(request):
    resume_content = request.data.get('resume_text', '')
    seeker, _ = Seeker.objects.get_or_create(user=request.user)

    if resume_content:
        analysis = analyze_resume_content(resume_content)
    else:
        latest_analysis = ResumeAnalysis.objects.filter(seeker=seeker).order_by('-created_at').first()
        if not latest_analysis:
            return Response({'matches': [], 'total_count': 0})
        analysis = {
            'skills': latest_analysis.skills_found,
            'experience_years': latest_analysis.experience_years,
            'technologies': latest_analysis.technologies,
        }

    matched_jobs = []
    all_jobs = Job.objects.filter(is_deleted=False, is_active=True).select_related('company', 'category')

    for job in all_jobs:
        score = calculate_match_score(analysis, job)
        if score > 30:
            matched_jobs.append({
                'job': job,
                'score': score,
                'missing_skills': get_missing_skills(analysis.get('skills', []), job.skills_required.all()),
            })

    matched_jobs.sort(key=lambda x: x['score'], reverse=True)

    for match in matched_jobs[:20]:
        JobMatch.objects.get_or_create(
            seeker=seeker,
            job=match['job'],
            defaults={
                'match_score': match['score'],
                'matching_skills': analysis.get('skills', []),
                'missing_skills': match['missing_skills'],
                'explanation': f"This job matches your profile with {match['score']:.1f}% compatibility based on skills and experience."
            }
        )

    return Response({
        'matches': [
            {
                'job_id': m['job'].id,
                'job_title': m['job'].title,
                'company': m['job'].company.company_name,
                'match_score': m['score'],
                'missing_skills': m['missing_skills'],
            }
            for m in matched_jobs[:10]
        ]
    })


def calculate_match_score(analysis, job):
    score = 0

    seeker_skills = set(s.lower() for s in analysis.get('skills', []))
    job_skills = set(s.name.lower() for s in job.skills_required.all())

    if seeker_skills and job_skills:
        skill_match = len(seeker_skills.intersection(job_skills)) / len(job_skills)
        score += skill_match * 50

    exp = analysis.get('experience_years', 0)
    if exp >= job.experience_required:
        score += 30
    elif exp >= job.experience_required * 0.5:
        score += 15

    seeker_tech = set(t.lower() for t in analysis.get('technologies', []))
    for skill in job.skills_required.all():
        if skill.name.lower() in seeker_tech:
            score += 5

    return min(score, 100)


def get_missing_skills(seeker_skills, job_skills):
    seeker_set = set(s.lower() for s in seeker_skills)
    return [s.name for s in job_skills if s.name.lower() not in seeker_set]


@extend_schema(responses=AdminStatsSerializer)
@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    return Response({
        'total_users': User.objects.count(),
        'total_employers': Employer.objects.count(),
        'total_seekers': Seeker.objects.count(),
        'total_jobs': Job.objects.filter(is_deleted=False).count(),
        'active_jobs': Job.objects.filter(is_deleted=False, is_active=True).count(),
        'total_applications': Application.objects.filter(is_deleted=False).count(),
        'new_users_today': User.objects.filter(date_joined__date=datetime.now().date()).count(),
    })


@extend_schema(request=ReportUserSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_user(request):
    reported_id = request.data.get('reported_user_id') or request.data.get('reported_user')
    reason = request.data.get('reason')

    if not reported_id or not reason:
        return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        reported_user = User.objects.get(id=reported_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    report = Report.objects.create(
        reporter=request.user,
        reported_user=reported_user,
        report_type='user_report',
        reason=reason
    )

    return Response({'message': 'Report submitted', 'report_id': report.id})


@extend_schema(request=ReportJobSerializer, responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_job(request):
    job_id = request.data.get('job')
    reason = request.data.get('reason')

    if not job_id or not reason:
        return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    report = Report.objects.create(
        reporter=request.user,
        job=job,
        reported_user=job.company.user,
        report_type='job_report',
        reason=reason
    )

    return Response({'message': 'Report submitted', 'report_id': report.id})