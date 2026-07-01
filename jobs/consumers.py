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

        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'user_online',
                'user_id': user.id,
                'username': user.username,
            }
        )

    async def disconnect(self, close_code):
        user = self.scope.get('user')
        if user and not user.is_anonymous:
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'user_offline',
                    'user_id': user.id,
                    'username': user.username,
                }
            )
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
        elif message_type == 'read':
            await self.handle_read(data)

    async def handle_new_message(self, data):
        message_text = data.get('text', '').strip()
        sender_id = self.scope['user'].id

        if not message_text:
            return

        message = await self.create_message(sender_id, self.chat_id, message_text)

        await self.channel_layer.group_send(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message_id': message.id,
                'sender_id': sender_id,
                'sender_username': message.sender.username,
                'text': message_text,
                'created_at': message.created_at.isoformat(),
                'is_read': False,
            }
        )

        await self.update_chat_timestamp(self.chat_id)

        recipient = await self.get_recipient(self.chat_id, sender_id)
        if recipient:
            await self.create_notification(recipient.id, self.chat_id, message_text, sender_id)

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

    async def handle_read(self, data):
        user_id = self.scope['user'].id
        updated = await self.mark_messages_read(self.chat_id, user_id)
        if updated > 0:
            await self.channel_layer.group_send(
                self.chat_group_name,
                {
                    'type': 'messages_read',
                    'reader_id': user_id,
                    'count': updated,
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
            'is_read': event.get('is_read', False),
        }))

    async def typing_indicator(self, event):
        if event['user_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))

    async def messages_read(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read',
            'reader_id': event['reader_id'],
            'count': event['count'],
        }))

    async def user_online(self, event):
        if event['user_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'presence',
                'user_id': event['user_id'],
                'status': 'online',
            }))

    async def user_offline(self, event):
        if event['user_id'] != self.scope['user'].id:
            await self.send(text_data=json.dumps({
                'type': 'presence',
                'user_id': event['user_id'],
                'status': 'offline',
            }))

    @database_sync_to_async
    def has_chat_access(self, user_id, chat_id):
        return Chat.objects.filter(
            id=chat_id,
        ).filter(Q(user1_id=user_id) | Q(user2_id=user_id)).exists()

    @database_sync_to_async
    def create_message(self, sender_id, chat_id, text):
        chat = Chat.objects.get(id=chat_id)
        message = Message.objects.create(
            chat=chat,
            sender_id=sender_id,
            text=text
        )
        return message

    @database_sync_to_async
    def get_recipient(self, chat_id, sender_id):
        chat = Chat.objects.get(id=chat_id)
        return chat.user2 if chat.user1_id == sender_id else chat.user1

    @database_sync_to_async
    def create_notification(self, user_id, chat_id, message_text, sender_id):
        Notification.objects.create(
            user_id=user_id,
            notification_type='message',
            title='New Message',
            message=message_text[:100] if message_text else 'You have a new message',
            link=f'/messages?chat={chat_id}',
            data={'chat_id': chat_id, 'sender_id': sender_id}
        )

    @database_sync_to_async
    def update_chat_timestamp(self, chat_id):
        Chat.objects.filter(id=chat_id).update()

    @database_sync_to_async
    def mark_messages_read(self, chat_id, user_id):
        return Message.objects.filter(
            chat_id=chat_id,
            is_read=False,
        ).exclude(sender_id=user_id).update(is_read=True)


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
        if hasattr(self, 'user_group_name'):
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
