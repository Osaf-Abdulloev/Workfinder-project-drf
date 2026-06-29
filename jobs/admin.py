from django.contrib import admin
from .models import (
    Employer, Seeker, Category, Skill, SkillCategory,
    Job, Application, Favorite, Chat, Message,
    Notification, ResumeAnalysis, JobMatch, Report, AdminLog
)


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'location', 'is_verified', 'is_banned', 'created_at']
    list_filter = ['is_verified', 'is_banned', 'created_at']
    search_fields = ['company_name', 'user__username', 'location']


@admin.register(Seeker)
class SeekerAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience', 'education', 'is_verified', 'is_banned', 'created_at']
    list_filter = ['is_verified', 'is_banned', 'created_at']
    search_fields = ['user__username', 'address', 'education']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'job_type', 'is_active', 'created_at']
    list_filter = ['job_type', 'workplace_type', 'is_active', 'is_deleted', 'created_at']
    search_fields = ['title', 'description', 'location']
    filter_horizontal = ['skills_required']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'job__title']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'created_at']
    search_fields = ['user__username', 'job__title']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'created_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title']


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ['seeker', 'experience_years', 'education_level', 'created_at']


@admin.register(JobMatch)
class JobMatchAdmin(admin.ModelAdmin):
    list_display = ['seeker', 'job', 'match_score', 'created_at']
    list_filter = ['created_at']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status', 'created_at']


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ['admin', 'action', 'created_at']
    list_filter = ['action', 'created_at']