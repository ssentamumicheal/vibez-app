# core/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import time, timedelta
from django.utils import timezone
from django.db.models import Q # Used for CheckIn constraint


# --- 1. Custom User Model (MUST BE DEFINED FIRST) ---
class User(AbstractUser):
    """
    Custom user model to allow login with email address.
    """
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # Adding related_name to avoid conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',  # Avoid clashes with auth.User
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions_set',  # Avoid clashes with auth.User
        blank=True
    )

    def __str__(self):
        return self.email


# --- 2. Gamification Models ---
class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)  # Emoji or icon name
    points = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'achievement']


class UserReputation(models.Model):
    """Tracks user points and rank for gamification."""
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='reputation')
    points = models.IntegerField(default=0)
    current_tier = models.CharField(max_length=50, default='Newcomer')

    def __str__(self):
        return f'{self.user.username} - {self.points} Points'


class Badge(models.Model):
    """Defines and tracks user achievements."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon_url = models.URLField(blank=True, null=True)

    users = models.ManyToManyField('User', related_name='badges')

    def __str__(self):
        return self.name


# --- 3. Social Features ---
class Friendship(models.Model):
    from_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='following')
    to_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_user', 'to_user']


class EventInvite(models.Model):
    event = models.ForeignKey('PartyLocation', on_delete=models.CASCADE)
    from_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sent_invites')
    to_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='received_invites')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('DECLINED', 'Declined')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.username} invited {self.to_user.username} to {self.event.name}"


# --- 4. Party Location Model (Consolidated with Smart Filters) ---
class PartyLocation(models.Model):
    """
    Model for a party or event location, including smart filter fields.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100, default='Kampala')
    country = models.CharField(max_length=100, default='Uganda')

    # --- Smart Filter Fields ---
    GENRE_CHOICES = (
        ('HIPHOP', 'Hip Hop/R&B'),
        ('AFROBEAT', 'Afrobeat'),
        ('ELECTRONIC', 'Electronic/Dance'),
        ('ROCK', 'Rock'),
        ('OTHER', 'Other'),
    )
    PRICE_CHOICES = (
        ('$', 'Cheap'),
        ('$$', 'Moderate'),
        ('$$$', 'Expensive'),
    )

    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='OTHER')
    price_tier = models.CharField(max_length=3, choices=PRICE_CHOICES, default='$')

    # Operational Hours for 'Currently Open' filter
    opening_time = models.TimeField(default=time(18, 0))  # 6:00 PM
    closing_time = models.TimeField(default=time(2, 0))  # 2:00 AM

    # Real-time metrics
    current_crowd = models.IntegerField(default=0)  # 0-100 percentage
    vibe_level = models.CharField(max_length=20, choices=[
        ('CHILL', 'Chill'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High Energy')
    ], default='MEDIUM')
    average_rating = models.FloatField(default=4.0)
    total_checkins = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_open_now(self):
        """Check if the location is currently open"""
        now = timezone.now()
        current_time = now.time()

        # Handle locations that close after midnight
        if self.opening_time > self.closing_time:
            return current_time >= self.opening_time or current_time <= self.closing_time
        else:
            return self.opening_time <= current_time <= self.closing_time


# --- 5. Events Model ---
class Event(models.Model):
    """
    Model for events and parties happening at locations.
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    party_location = models.ForeignKey(PartyLocation, on_delete=models.CASCADE, related_name='events')

    # Event timing
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Event details
    CATEGORY_CHOICES = (
        ('MUSIC', 'Music'),
        ('FESTIVAL', 'Festival'),
        ('CLUB', 'Club Night'),
        ('CULTURAL', 'Cultural'),
        ('SPORTS', 'Sports'),
        ('OTHER', 'Other'),
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='MUSIC')

    PRICE_CHOICES = (
        ('$', 'Cheap (Under 20K)'),
        ('$$', 'Moderate (20K-50K)'),
        ('$$$', 'Expensive (50K+)'),
    )
    price_tier = models.CharField(max_length=3, choices=PRICE_CHOICES, default='$')

    # Event metrics
    expected_attendees = models.IntegerField(default=0)
    actual_attendees = models.IntegerField(default=0)
    is_popular = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name} at {self.party_location.name}"

    @property
    def is_live(self):
        """Check if event is currently happening"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    @property
    def is_upcoming(self):
        """Check if event is in the future"""
        return self.start_date > timezone.now()


# --- 6. Event RSVP Model ---
class EventRSVP(models.Model):
    """
    Track user RSVPs for events
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_rsvps')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    status = models.CharField(max_length=20, choices=[
        ('GOING', 'Going'),
        ('INTERESTED', 'Interested'),
        ('NOT_GOING', 'Not Going')
    ], default='INTERESTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'event']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.event.name} ({self.status})"


# --- 7. Core Functionality Models ---
class Video(models.Model):
    """
    Model for user-uploaded videos of party locations.
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='videos')
    party_location = models.ForeignKey(PartyLocation, on_delete=models.CASCADE, related_name='videos')
    video_file = models.FileField(upload_to='party_videos/')
    timestamp = models.DateTimeField(auto_now_add=True)
    caption = models.CharField(max_length=255, blank=True, null=True)
    is_live = models.BooleanField(default=False)

    def __str__(self):
        return f'Video by {self.user.username} at {self.party_location.name}'


class Ranking(models.Model):
    """
    Model for user rankings of party locations.
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    party_location = models.ForeignKey(PartyLocation, on_delete=models.CASCADE, related_name='rankings')
    score = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])  # Ranking from 1 to 5
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures a user can only rank a specific location once
        unique_together = ('user', 'party_location')

    def __str__(self):
        return f'{self.user.username} ranked {self.party_location.name} with a score of {self.score}'


class PartyChat(models.Model):
    """
    Model for chat messages specific to a party location.
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    party_location = models.ForeignKey(PartyLocation, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'[{self.party_location.name}] {self.user.username}: {self.message[:50]}'


# --- 8. Real-Time Presence and Stories (New Features) ---
class CheckIn(models.Model):
    """Tracks users who are currently checked in to a location."""
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='check_ins')
    party_location = models.ForeignKey(PartyLocation, on_delete=models.CASCADE, related_name='checkins')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  # User is currently checked in

    class Meta:
        # Custom constraint to prevent a user from having more than one active check-in globally
        constraints = [
            models.UniqueConstraint(fields=['user'], condition=Q(is_active=True), name='unique_active_check_in')
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.username} checked into {self.party_location.name} (Active: {self.is_active})'


class Story(models.Model):
    """Ephemeral media content tied to a location."""
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    party_location = models.ForeignKey(PartyLocation, on_delete=models.SET_NULL, null=True, related_name='stories')
    media_file = models.FileField(upload_to='stories/')
    caption = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # Stories expire after 24 hours
        return self.timestamp < (timezone.now() - timedelta(hours=24))

    def __str__(self):
        return f'Story by {self.user.username} at {self.party_location.name if self.party_location else "N/A"}'


# --- 9. User Location Tracking ---
class UserLocation(models.Model):
    """
    Track user locations for real-time party discovery
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(null=True, blank=True)  # GPS accuracy in meters
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} location at {self.timestamp}"


# --- 10. Live Activity Feed ---
class ActivityFeed(models.Model):
    """
    Real-time activity feed for the platform
    """
    ACTIVITY_TYPES = (
        ('CHECKIN', 'User Check-in'),
        ('VIDEO', 'Video Upload'),
        ('EVENT', 'New Event'),
        ('RSVP', 'Event RSVP'),
        ('REVIEW', 'Location Review'),
    )

    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    party_location = models.ForeignKey(PartyLocation, on_delete=models.CASCADE, null=True, blank=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.activity_type}: {self.message}"

class UpcomingParty(models.Model):
    """
    Model for upcoming party events.
    """
    party_location = models.ForeignKey(PartyLocation, on_delete=models.CASCADE, related_name='upcoming_parties')
    event_name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return f'{self.event_name} at {self.party_location.name}'



