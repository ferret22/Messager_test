from django.db import models
from django.conf import settings

# Create your models here.
class Chat(models.Model):
    class ChatType(models.TextChoices):
        PRIVATE = 'private', 'Private'
        GROUP = 'group', 'Group'
    
    title = models.CharField(max_length=255, blank=True)
    chat_type = models.CharField(
        max_length=10,
        choices=ChatType.choices,
        default=ChatType.PRIVATE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title or f"Chat #{self.id}"


class ChatMember(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='members',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_memberships',
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('chat', 'user')
    
    def __str__(self):
        return f'{self.user} in {self.chat}'


class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
    )
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Message #{self.id} from {self.sender}'
