"""
Utility functions for sending real-time notifications
"""
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def send_notification(user_id, notification_type, title, message, link=''):
    """Send real-time notification to user via WebSocket"""
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user_id}',
            {
                'type': 'notification_message',
                'id': 0,
                'notification_type': notification_type,
                'title': title,
                'message': message,
            }
        )
    except Exception:
        pass