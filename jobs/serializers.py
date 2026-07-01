from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from .models import (
    Employer, Seeker, Category, Job, Application, Favorite, Chat, Message,
    Notification, Skill, SkillCategory, ResumeAnalysis, JobMatch, Report, AdminLog
)


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class SkillSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        try:
            skill, created = Skill.objects.get_or_create(name=data)
            return skill
        except Exception:
            self.fail('invalid')


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
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Employer
        fields = [
            'id', 'user', 'company_name', 'about', 'logo', 'location',
            'website', 'created_at', 'is_created', 'is_verified', 'is_banned',
            'username', 'email', 'first_name', 'last_name',
        ]
        read_only_fields = ['is_created', 'is_verified', 'is_banned', 'created_at']

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else ''

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else ''

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request:
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            user = instance.user
            if user:
                if first_name is not None:
                    user.first_name = first_name
                if last_name is not None:
                    user.last_name = last_name
                user.save()
        return super().update(instance, validated_data)


class SeekerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    location = serializers.CharField(source='address', required=False, allow_blank=True)
    skills = SkillSlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Skill.objects.all(),
        required=False
    )
    skills_list = serializers.SlugRelatedField(
        source='skills',
        many=True,
        slug_field='name',
        read_only=True
    )

    class Meta:
        model = Seeker
        exclude = ['address']
        read_only_fields = ['is_created', 'is_verified', 'is_banned']

    def get_first_name(self, obj):
        return obj.user.first_name if obj.user else ''

    def get_last_name(self, obj):
        return obj.user.last_name if obj.user else ''

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request:
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            user = instance.user
            if user:
                if first_name is not None:
                    user.first_name = first_name
                if last_name is not None:
                    user.last_name = last_name
                user.save()
        return super().update(instance, validated_data)


class JobSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    company_logo = serializers.ImageField(source='company.logo', read_only=True)
    company_website = serializers.URLField(source='company.website', read_only=True)
    company_about = serializers.CharField(source='company.about', read_only=True)
    skills_required = SkillSlugRelatedField(
        many=True,
        slug_field='name',
        queryset=Skill.objects.all(),
        required=False
    )

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['company']


class JobSearchSerializer(serializers.Serializer):
    results = JobSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    pages = serializers.IntegerField()


class ApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    applicant_username = serializers.CharField(source='user.username', read_only=True)
    applicant_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['user']


class FavoriteSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company.company_name', read_only=True)
    job_location = serializers.CharField(source='job.location', read_only=True)

    class Meta:
        model = Favorite
        fields = '__all__'
        read_only_fields = ['user']


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
        read_only_fields = ['sender']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    user_type = serializers.ChoiceField(choices=['seeker', 'employer'], write_only=True)
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'user_type']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        validated_data.pop('password2')

        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()

        if user_type == 'employer':
            Employer.objects.create(user=user, company_name=user.username + " Company", is_created=True)
            self._is_seeker = False
        else:
            Seeker.objects.create(user=user, is_created=True)
            self._is_seeker = True

        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        
        user_type = 'seeker'
        if hasattr(user, 'seeker_profile'):
            user_type = 'seeker'
        elif hasattr(user, 'employer_profile'):
            user_type = 'employer'
        elif user.is_superuser:
            user_type = 'admin'
            
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': user_type
        }
        return data


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


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


class ReportUserSerializer(serializers.Serializer):
    reported_user_id = serializers.IntegerField()
    reason = serializers.CharField()
    reported_user = serializers.IntegerField(required=False)


class ReportJobSerializer(serializers.Serializer):
    job = serializers.IntegerField()
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
    experience = serializers.CharField()
    education = serializers.CharField()
    recommendations = serializers.ListField()
    job_titles = serializers.ListField()
    technologies = serializers.ListField()
    languages = serializers.ListField()
    certifications = serializers.ListField()