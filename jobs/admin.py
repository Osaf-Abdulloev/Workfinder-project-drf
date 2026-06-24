from django.contrib import admin
from .models import Employer, Seeker, Category, Job, Application, Favorite, Chat, Message


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'location', 'created_at']
    search_fields = ['company_name', 'location']


@admin.register(Seeker)
class SeekerAdmin(admin.ModelAdmin):
    list_display = ['user', 'education', 'experience', 'address']
    search_fields = ['user__username', 'education']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'job_type', 'salary', 'created_at']
    list_filter = ['job_type', 'category', 'created_at']
    search_fields = ['title', 'description', 'location']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['job', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['job__title', 'user__username']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'created_at']
    search_fields = ['user__username', 'job__title']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'created_at']
    search_fields = ['user1__username', 'user2__username']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['chat', 'sender', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['text']
