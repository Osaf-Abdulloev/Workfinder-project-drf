import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Chat, Message, Notification


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'

        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
            return

        has_access = await self.has_chat_access(user.id, self.chat_id)
        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'message':
            await self.handle_new_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)

    async def handle_new_message(self, data):
        message_text = data.get('text', '')
        sender_id = self.scope['user'].id
        file_name = data.get('file_name', '')

        message = await self.create_message(sender_id, self.chat_id, message_text, file_name)

        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message_id': message.id,
                'sender_id': sender_id,
                'sender_username': message.sender.username,
                'text': message_text,
                'created_at': message.created_at.isoformat(),
            }
        )

        await self.create_notification(sender_id, self.chat_id, message_text)

    async def handle_typing(self, data):
        is_typing = data.get('is_typing', False)
        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.scope['user'].id,
                'username': self.scope['user'].username,
                'is_typing': is_typing,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'text': event['text'],
            'created_at': event['created_at'],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))

    @database_sync_to_async
    def has_chat_access(self, user_id, chat_id):
        return Chat.objects.filter(id=chat_id, user1_id=user_id).exists() or \
               Chat.objects.filter(id=chat_id, user2_id=user_id).exists()

    @database_sync_to_async
    def create_message(self, sender_id, chat_id, text, file_name=''):
        chat = Chat.objects.get(id=chat_id)
        message = Message.objects.create(
            chat=chat,
            sender_id=sender_id,
            text=text
        )
        return message

    @database_sync_to_async
    def create_notification(self, sender_id, chat_id, message_text):
        chat = Chat.objects.get(id=chat_id)
        recipient = chat.user2 if chat.user1_id == sender_id else chat.user1
        Notification.objects.create(
            user=recipient,
            notification_type='message',
            title='New Message',
            message=message_text[:100] if message_text else 'You have a new message',
            link=f'/chats/{chat_id}'
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f'notifications_{user.id}'

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event['id'],
            'notification_type': event['notification_type'],
            'title': event['title'],
            'message': event['message'],
        }))