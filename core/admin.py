# core/admin.py
from django.contrib import admin
from .models import (
    User, PartyLocation, Event, EventRSVP, Video, Ranking,
    CheckIn, Story, UserReputation, Achievement, UserAchievement,
    Friendship, EventInvite, UserLocation, ActivityFeed
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'date_joined']
    search_fields = ['email', 'username']

@admin.register(PartyLocation)
class PartyLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'current_crowd', 'average_rating', 'is_open_now']
    list_filter = ['city', 'genre', 'price_tier', 'vibe_level']
    search_fields = ['name', 'address']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'party_location', 'start_date', 'category', 'is_live', 'is_upcoming']
    list_filter = ['category', 'is_popular', 'is_trending', 'start_date']
    search_fields = ['name', 'description']

@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'status', 'created_at']
    list_filter = ['status', 'created_at']

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['user', 'party_location', 'timestamp', 'is_live']
    list_filter = ['is_live', 'timestamp']

@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ['user', 'party_location', 'timestamp', 'is_active']
    list_filter = ['is_active', 'timestamp']

@admin.register(ActivityFeed)
class ActivityFeedAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'user', 'timestamp', 'message']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['message']

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ['user', 'latitude', 'longitude', 'timestamp']
    list_filter = ['timestamp']

# Register other models
admin.site.register(Ranking)
admin.site.register(Story)
admin.site.register(UserReputation)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
admin.site.register(Friendship)
admin.site.register(EventInvite)
