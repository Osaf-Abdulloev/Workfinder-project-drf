from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Application, Message, Job, Notification
from .notification_utils import send_notification


@receiver(post_save, sender=Application)
def application_created(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.job.company.user,
            notification_type='application_new',
            title='New Application',
            message=f'{instance.user.username} applied to your job: {instance.job.title}',
            link=f'/jobs/{instance.job.id}'
        )
        send_notification(
            instance.job.company.user.id,
            'application_new',
            'New Application',
            f'{instance.user.username} applied to your job: {instance.job.title}'
        )


@receiver(post_save, sender=Message)
def message_created(sender, instance, created, **kwargs):
    if created:
        chat = instance.chat
        recipient = chat.user2 if instance.sender == chat.user1 else chat.user1
        
        Notification.objects.create(
            user=recipient,
            notification_type='message',
            title='New Message',
            message=f'{instance.sender.username} sent you a message',
            link=f'/chats/{chat.id}'
        )
        send_notification(
            recipient.id,
            'message',
            'New Message',
            f'{instance.sender.username} sent you a message'
        )


@receiver(post_save, sender=Job)
def job_created(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            user=instance.company.user,
            notification_type='job_update',
            title='Job Posted',
            message=f'Your job "{instance.title}" has been posted successfully',
            link=f'/jobs/{instance.id}'
        )