from django.contrib import admin
from .models import Chat, ChatMember, Message

# Register your models here.
class ChatMemberInline(admin.TabularInline):
    model = ChatMember
    extra = 1


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at', 'edited_at')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'chat_type', 'created_at')
    list_filter = ('chat_type', 'created_at')
    search_fields = ('title',)
    inlines = (ChatMemberInline, MessageInline)


@admin.register(ChatMember)
class ChatMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'user', 'joined_at')
    list_filter = ('joined_at',)
    search_fields = ('chat__title', 'user__username')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'short_text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'sender__username', 'chat__title')

    def short_text(self, obj):
        return obj.text[:50]
