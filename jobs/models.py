from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Employer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_profile')
    company_name = models.CharField(max_length=100)
    about = models.TextField()
    logo = models.ImageField(upload_to='companylogos/', blank=True, null=True)
    location = models.CharField(max_length=100)
    website = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_created = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.company_name


class Seeker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seeker_profile')
    bio = models.TextField()
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    skills = models.ManyToManyField('Skill', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_created = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username}'


class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey('SkillCategory', on_delete=models.CASCADE, related_name='skills', null=True, blank=True)

    def __str__(self):
        return self.name


class SkillCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPE = [
        ('full_time', 'Full time'),
        ('part_time', 'Part time'),
        ('freelance', 'Freelance'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]

    WORKPLACE_TYPE = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site'),
    ]

    company = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=100)
    description = models.TextField()
    responsibilities = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=25, choices=JOB_TYPE)
    workplace_type = models.CharField(max_length=25, choices=WORKPLACE_TYPE, default='onsite')
    experience_required = models.PositiveIntegerField(default=0)
    skills_required = models.ManyToManyField(Skill, blank=True, related_name='jobs')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='jobs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deadline = models.DateField(null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('interview', 'Interview Scheduled'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='application_resumes/', blank=True, null=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['job', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.job.title}'


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'job']

    def __str__(self):
        return f'{self.user.username} - {self.job.title}'


class Chat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user1.username} - {self.user2.username}'


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=True)

    file = models.FileField(upload_to='message_files/', blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.text[:50]


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('application_new', 'New Application'),
        ('application_status', 'Application Status Update'),
        ('message', 'New Message'),
        ('job_invitation', 'Job Invitation'),
        ('job_update', 'Job Update'),
        ('profile_update', 'Profile Update'),
        ('ai_recommendation', 'AI Recommendation'),
        ('account_activity', 'Account Activity'),
        ('system', 'System Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.title}'


class ResumeAnalysis(models.Model):
    seeker = models.ForeignKey(Seeker, on_delete=models.CASCADE, related_name='resume_analyses')
    original_resume = models.FileField(upload_to='resume_analyses/')
    extracted_text = models.TextField()
    skills_found = models.JSONField()
    experience_years = models.PositiveIntegerField(null=True, blank=True)
    education_level = models.CharField(max_length=50, blank=True, null=True)
    job_titles = models.JSONField(blank=True, null=True)
    technologies = models.JSONField(blank=True, null=True)
    languages = models.JSONField(blank=True, null=True)
    certifications = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.seeker.user.username} - Analysis'


class JobMatch(models.Model):
    seeker = models.ForeignKey(Seeker, on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='matches')
    match_score = models.DecimalField(max_digits=5, decimal_places=2)
    matching_skills = models.JSONField()
    missing_skills = models.JSONField()
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-match_score']
        unique_together = ['seeker', 'job']

    def __str__(self):
        return f'{self.seeker.user.username} - {self.job.title} ({self.match_score}%)'


class AdminLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_logs')
    action = models.CharField(max_length=100)
    description = models.TextField()
    model_name = models.CharField(max_length=50, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.admin.username} - {self.action}'


class SearchQuery(models.Model):
    query = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    results_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.query


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.action}'


class Report(models.Model):
    REPORT_TYPES = [
        ('user_report', 'User Report'),
        ('job_report', 'Job Report'),
        ('application_report', 'Application Report'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('resolved', 'Resolved')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.report_type} - {self.reporter.username}'