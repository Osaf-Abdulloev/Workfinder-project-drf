import json
import logging
from datetime import datetime

from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .models import (
    Job, Seeker, ResumeAnalysis, JobMatch, Skill, Category
)
from .serializers import JobSerializer
from .ai_service import analyze_with_ai, match_jobs_with_ai
from .views import extract_pdf_text, extract_docx_text

logger = logging.getLogger(__name__)


@extend_schema(responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_analyze_profile(request):
    """AI-powered profile analysis from resume upload or text description."""
    text_content = ''
    input_type = 'text'
    resume_file = None

    if 'resume' in request.FILES:
        resume_file = request.FILES['resume']
        input_type = 'resume'

        if resume_file.name.endswith('.pdf'):
            text_content = extract_pdf_text(resume_file)
        elif resume_file.name.endswith('.docx'):
            text_content = extract_docx_text(resume_file)
        elif resume_file.name.endswith('.txt'):
            text_content = resume_file.read().decode('utf-8')
        else:
            return Response(
                {'error': 'Unsupported file format. Please upload PDF, DOCX, or TXT.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    elif request.data.get('text'):
        text_content = request.data.get('text', '').strip()
        input_type = 'text'
    else:
        return Response(
            {'error': 'Please provide either a resume file or a text description of your skills and experience.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not text_content:
        return Response(
            {'error': 'Could not extract text from the provided input.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    ai_result = analyze_with_ai(text_content, input_type)

    if not ai_result:
        return Response(
            {'error': 'AI analysis failed. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    seeker, _ = Seeker.objects.get_or_create(user=request.user)

    skills_list = ai_result.get('skills', []) + ai_result.get('technologies', [])
    existing_skills = []
    for skill_name in skills_list:
        skill_obj, _ = Skill.objects.get_or_create(name=skill_name.lower().strip())
        existing_skills.append(skill_obj)
    seeker.skills.set(existing_skills)

    resume_analysis = ResumeAnalysis.objects.create(
        seeker=seeker,
        original_resume=resume_file if resume_file else None,
        extracted_text=text_content[:5000],
        skills_found=ai_result.get('skills', []),
        experience_years=ai_result.get('experience_years', 0),
        education_level=ai_result.get('education', [{}])[0].get('degree', '') if ai_result.get('education') else '',
        job_titles=ai_result.get('job_titles', []),
        technologies=ai_result.get('technologies', []),
        languages=ai_result.get('languages', []),
        certifications=ai_result.get('certifications', []),
    )

    return Response({
        'analysis_id': resume_analysis.id,
        'profile': {
            'full_name': ai_result.get('full_name', ''),
            'email': ai_result.get('email', ''),
            'phone': ai_result.get('phone', ''),
            'location': ai_result.get('location', ''),
            'summary': ai_result.get('summary', ''),
        },
        'skills': ai_result.get('skills', []),
        'technologies': ai_result.get('technologies', []),
        'soft_skills': ai_result.get('soft_skills', []),
        'experience_years': ai_result.get('experience_years', 0),
        'experience_level': ai_result.get('experience_level', 'mid'),
        'education': ai_result.get('education', []),
        'job_titles': ai_result.get('job_titles', []),
        'languages': ai_result.get('languages', []),
        'certifications': ai_result.get('certifications', []),
        'projects': ai_result.get('projects', []),
        'inferred_skills': ai_result.get('inferred_skills', []),
        'recommended_job_categories': ai_result.get('recommended_job_categories', []),
        'search_keywords': ai_result.get('search_keywords', []),
        'career_strengths': ai_result.get('career_strengths', []),
        'areas_for_growth': ai_result.get('areas_for_growth', []),
        'input_type': input_type,
    })


@extend_schema(responses={200: None})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_match_jobs(request):
    """AI-powered job matching with compatibility scores."""
    seeker, _ = Seeker.objects.get_or_create(user=request.user)

    analysis_id = request.data.get('analysis_id')
    filters = request.data.get('filters', {})

    if analysis_id:
        try:
            analysis = ResumeAnalysis.objects.get(id=analysis_id, seeker=seeker)
            candidate_profile = {
                'skills': analysis.skills_found,
                'technologies': analysis.technologies,
                'experience_years': analysis.experience_years,
                'education_level': analysis.education_level,
                'job_titles': analysis.job_titles,
                'languages': analysis.languages,
                'certifications': analysis.certifications,
            }
        except ResumeAnalysis.DoesNotExist:
            return Response(
                {'error': 'Analysis not found. Please run analysis first.'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        latest = ResumeAnalysis.objects.filter(seeker=seeker).order_by('-created_at').first()
        if not latest:
            return Response(
                {'error': 'No analysis found. Please analyze your profile first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        candidate_profile = {
            'skills': latest.skills_found,
            'technologies': latest.technologies,
            'experience_years': latest.experience_years,
            'education_level': latest.education_level,
            'job_titles': latest.job_titles,
            'languages': latest.languages,
            'certifications': latest.certifications,
        }

    jobs_query = Job.objects.filter(
        is_deleted=False, is_active=True
    ).select_related('company', 'category').prefetch_related('skills_required')

    if filters.get('workplace_type'):
        jobs_query = jobs_query.filter(workplace_type=filters['workplace_type'])
    if filters.get('job_type'):
        jobs_query = jobs_query.filter(job_type=filters['job_type'])
    if filters.get('category'):
        jobs_query = jobs_query.filter(category_id=filters['category'])
    if filters.get('location'):
        jobs_query = jobs_query.filter(location__icontains=filters['location'])
    if filters.get('min_salary'):
        jobs_query = jobs_query.filter(salary_min__gte=filters['min_salary'])
    if filters.get('max_salary'):
        jobs_query = jobs_query.filter(salary_max__lte=filters['max_salary'])
    if filters.get('experience_level'):
        exp_map = {'junior': (0, 2), 'mid': (2, 5), 'senior': (5, 10), 'lead': (8, 999)}
        exp_range = exp_map.get(filters['experience_level'], (0, 999))
        jobs_query = jobs_query.filter(experience_required__gte=exp_range[0], experience_required__lte=exp_range[1])

    if not jobs_query.exists():
        return Response({
            'matches': [],
            'total_jobs': 0,
            'summary': 'No jobs found matching your filters.',
            'top_skills': [],
            'suggested_improvements': [],
        })

    ai_result = match_jobs_with_ai(candidate_profile, list(jobs_query))

    if not ai_result:
        jobs_list = list(jobs_query[:20])
        basic_matches = []
        seeker_skills = set(s.lower() for s in candidate_profile.get('skills', []) + candidate_profile.get('technologies', []))

        for job in jobs_list:
            job_skills = set(s.name.lower() for s in job.skills_required.all())
            if job_skills:
                overlap = seeker_skills.intersection(job_skills)
                score = int((len(overlap) / len(job_skills)) * 80) + 10
            else:
                score = 50

            if score >= 30:
                basic_matches.append({
                    'job_id': job.id,
                    'job_title': job.title,
                    'company': job.company.company_name if job.company else '',
                    'match_score': min(score, 100),
                    'match_reasons': list(overlap) if job_skills else [],
                    'missing_skills': [s.name for s in job.skills_required.all() if s.name.lower() not in seeker_skills],
                    'explanation': f"Matches {len(overlap)} of your skills" if job_skills else "No specific skill requirements listed",
                    'recommendation': 'strong_match' if score >= 80 else ('good_match' if score >= 50 else 'potential_match'),
                })

        basic_matches.sort(key=lambda x: x['match_score'], reverse=True)
        return Response({
            'matches': basic_matches[:20],
            'total_jobs': jobs_query.count(),
            'summary': f'Found {len(basic_matches)} potential matches based on skills analysis.',
            'top_skills': candidate_profile.get('skills', [])[:5],
            'suggested_improvements': [],
        })

    ai_matches = ai_result.get('matches', [])
    valid_match_ids = {m['job_id'] for m in ai_matches}
    for job in jobs_query:
        if job.id not in valid_match_ids:
            continue

    for match in ai_matches:
        try:
            job = Job.objects.get(id=match['job_id'])
            JobMatch.objects.update_or_create(
                seeker=seeker,
                job=job,
                defaults={
                    'match_score': match.get('match_score', 0),
                    'matching_skills': match.get('match_reasons', []),
                    'missing_skills': match.get('missing_skills', []),
                    'explanation': match.get('explanation', ''),
                }
            )
        except Job.DoesNotExist:
            continue

    return Response({
        'matches': ai_matches[:20],
        'total_jobs': jobs_query.count(),
        'summary': ai_result.get('overall_summary', ''),
        'top_skills': ai_result.get('top_skills', []),
        'suggested_improvements': ai_result.get('suggested_improvements', []),
    })


@extend_schema(responses={200: None})
@api_view(['GET'])
@permission_classes([AllowAny])
def smart_job_filters(request):
    """Return available filter options for jobs."""
    categories = Category.objects.all().values('id', 'name')
    locations = Job.objects.filter(
        is_deleted=False, is_active=True
    ).values_list('location', flat=True).distinct().order_by('location')

    return Response({
        'categories': list(categories),
        'locations': [loc for loc in locations if loc],
        'workplace_types': [
            {'value': 'remote', 'label': 'Remote'},
            {'value': 'hybrid', 'label': 'Hybrid'},
            {'value': 'onsite', 'label': 'On-site'},
        ],
        'job_types': [
            {'value': 'full_time', 'label': 'Full-time'},
            {'value': 'part_time', 'label': 'Part-time'},
            {'value': 'freelance', 'label': 'Freelance'},
            {'value': 'contract', 'label': 'Contract'},
            {'value': 'internship', 'label': 'Internship'},
        ],
        'experience_levels': [
            {'value': 'junior', 'label': 'Junior (0-2 years)'},
            {'value': 'mid', 'label': 'Mid-level (2-5 years)'},
            {'value': 'senior', 'label': 'Senior (5-10 years)'},
            {'value': 'lead', 'label': 'Lead (8+ years)'},
        ],
    })
