from django.db import models
from django.contrib.auth.models import User


class Employer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=50)
    about = models.TextField()
    logo = models.ImageField(upload_to='companylogos/', blank=True, null=True)
    location = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    is_created = models.BooleanField(default=False, null=True, blank=True)
    
    def __str__(self):
        return self.company_name


class Seeker(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seeker_profile')
    bio = models.TextField()
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    experience = models.PositiveIntegerField()
    education = models.CharField(max_length=50)
    birth_date = models.DateField()
    address = models.CharField(max_length=50)
    is_created = models.BooleanField(default=False, null=True, blank=True)
    
    def __str__(self):
        return f'{self.user.username} || {self.bio}'


class Category(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPE = [
        ('full_time', 'Full time'),
        ('part_time', 'Part time'),
        ('freelance', 'Freelance')
    ]
    
    company = models.ForeignKey(Employer, on_delete=models.CASCADE)
    title = models.CharField(max_length=25)
    description = models.TextField()
    salary = models.PositiveIntegerField()
    location = models.CharField(max_length=50)
    job_type = models.CharField(max_length=25, choices=JOB_TYPE)
    experience_required = models.PositiveIntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
    
    def __str__(self):
        return self.title


class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cover_letter = models.TextField()
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
    
    def __str__(self):
        return self.job.title


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()
    
    def __str__(self):
        return f'{self.user.username} || {self.job.title}'


class Chat(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user1.username} - {self.user2.username}'


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return self.text
