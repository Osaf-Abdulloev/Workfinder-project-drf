from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from .models import (
    Employer, Seeker, Category, Job, Application, Favorite, Chat, Message,
    Notification, Skill, SkillCategory, ResumeAnalysis, JobMatch, Report, AdminLog
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category']


class SkillCategorySerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = SkillCategory
        fields = ['id', 'name', 'skills']


class CategorySerializer(serializers.ModelSerializer):
    jobs_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    @extend_schema_field(int)
    def get_jobs_count(self, obj):
        return getattr(obj, 'jobs_count', obj.jobs.count())


class EmployerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Employer
        fields = '__all__'


class SeekerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    skills_list = serializers.SlugRelatedField(
        source='skills',
        many=True,
        slug_field='name',
        read_only=True
    )

    class Meta:
        model = Seeker
        fields = '__all__'


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    skills_required = serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Skill.objects.all()
    )

    class Meta:
        model = Job
        fields = '__all__'


class JobSearchSerializer(serializers.Serializer):
    results = JobSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    pages = serializers.IntegerField()


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)

    class Meta:
        model = Application
        fields = '__all__'


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'


class ChatSerializer(serializers.ModelSerializer):
    user1_username = serializers.CharField(source='user1.username', read_only=True)
    user2_username = serializers.CharField(source='user2.username', read_only=True)

    class Meta:
        model = Chat
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    is_seeker = serializers.BooleanField(write_only=True, required=True)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'is_seeker']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        is_seeker = validated_data.pop('is_seeker')
        validated_data.pop('password2')

        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        return user, is_seeker


class RegisterResponseSerializer(serializers.Serializer):
    user = serializers.DictField()
    access = serializers.CharField()
    refresh = serializers.CharField()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class NotificationListResponseSerializer(serializers.Serializer):
    notifications = NotificationSerializer(many=True)
    unread_count = serializers.IntegerField()


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAnalysis
        fields = '__all__'
        read_only_fields = ['seeker', 'created_at']


class JobMatchSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)

    class Meta:
        model = JobMatch
        fields = '__all__'
        read_only_fields = ['seeker', 'created_at']


class JobMatchResultSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    company = serializers.CharField()
    match_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    missing_skills = serializers.ListField()


class MatchJobsResponseSerializer(serializers.Serializer):
    matches = JobMatchResultSerializer(many=True)


class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(source='reporter.username', read_only=True)
    reported_username = serializers.CharField(source='reported_user.username', read_only=True)

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['reporter', 'created_at']


class ReportUserSerializer(serializers.Serializer):
    reported_user_id = serializers.IntegerField()
    reason = serializers.CharField()


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_employers = serializers.IntegerField()
    total_seekers = serializers.IntegerField()
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    new_users_today = serializers.IntegerField()


class ResumeAnalysisResponseSerializer(serializers.Serializer):
    analysis_id = serializers.IntegerField()
    skills = serializers.ListField()
    experience_years = serializers.IntegerField()
    education_level = serializers.CharField()
    job_titles = serializers.ListField()
    technologies = serializers.ListField()
    languages = serializers.ListField()
    certifications = serializers.ListField()