import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Chat, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user_group_name = None
        self.user = self.scope['user']
        self.joined_group = False
        
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        is_member = await self.is_chat_member()
        if not is_member:
            await self.close(code=4404)
            return

        self.user_group_name = f'user_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name,
        )
        
        self.joined_group = True
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if not getattr(self, 'joined_group', False):
            return
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )
        
        if self.user_group_name is not None:
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name,
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get('text', '').strip()
        
        if not text:
            return
        
        message = await self.create_message(text)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
              'type': 'message.created',
              'message': {
                  'id': message.id,
                  'sender': message.sender_id,
                  'sender_username': message.sender.username,
                  'text': message.text,
                  'created_at': message.created_at.isoformat(), 
              },  
            },
        )
    
    async def message_created(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_created',
            'message': event['message'],
        }))
    
    async def message_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_updated',
            'message': event['message'],
        }))
    
    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message': event['message'],
        }))
    
    async def read_updated(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_updated',
            'read': event['read'],
        }))
    
    @sync_to_async
    def is_chat_member(self):
        return Chat.objects.filter(
            id=self.chat_id,
            members__user=self.user,
        ).exists()
    
    @sync_to_async
    def create_message(self, text):
        return Message.objects.select_related('sender').create(
            chat_id=self.chat_id,
            sender=self.user,
            text=text,
        )
