import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Chat, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']
        self.joined_group = False
        
        if not self.user.is_authenticated:
            await self.close(code=4401)
            return

        is_member = await self.is_chat_member()
        if not is_member:
            await self.close(code=4404)
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
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
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get('text', '').strip()
        
        if not text:
            return
        
        message = await self.create_message(text)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
              'type': 'chat.message',
              'message': {
                  'id': message.id,
                  'sender': message.sender_id,
                  'sender_username': message.sender.username,
                  'text': message.text,
                  'created_at': message.created_at.isoformat(), 
              },  
            },
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
    
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
