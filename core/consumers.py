# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import PartyChat, PartyLocation, User
from django.contrib.auth.models import AnonymousUser
# Add at the top with other imports
from channels.db import database_sync_to_async


class PartyChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Add authentication
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

class PartyChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user_id = text_data_json.get('user_id')

        user = await self.get_user(user_id)
        if isinstance(user, AnonymousUser) or not user:
             # Handle unauthenticated user gracefully
             return
        
        party_location = await self.get_party_location(self.room_name)
        if party_location:
            # Save message to database
            await self.save_message(user, party_location, message)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user': user.username,
                    'timestamp': str(PartyChat.timestamp)
                }
            )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user
        }))
    
    @sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()

    @sync_to_async
    def get_party_location(self, name):
        try:
            return PartyLocation.objects.get(name=name)
        except PartyLocation.DoesNotExist:
            return None
    
    @sync_to_async
    def save_message(self, user, party_location, message):
        PartyChat.objects.create(user=user, party_location=party_location, message=message)

