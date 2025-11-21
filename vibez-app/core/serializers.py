# core/serializers.py
from rest_framework import serializers
from .models import PartyLocation, Video, Ranking, User, PartyChat, CheckIn, Story, \
    UserReputation, Friendship, EventInvite, Event, EventRSVP, UserLocation, ActivityFeed
from django.db.models import Avg, Count
from django.contrib.auth import authenticate
from django.utils import timezone


# --- Event Serializers ---
class EventSerializer(serializers.ModelSerializer):
    party_location_name = serializers.CharField(source='party_location.name', read_only=True)
    party_location_address = serializers.CharField(source='party_location.address', read_only=True)
    party_location_lat = serializers.DecimalField(source='party_location.latitude', read_only=True, max_digits=9,
                                                  decimal_places=6)
    party_location_lng = serializers.DecimalField(source='party_location.longitude', read_only=True, max_digits=9,
                                                  decimal_places=6)
    is_live = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    rsvp_count = serializers.SerializerMethodField()
    user_rsvp_status = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'description', 'party_location', 'party_location_name',
            'party_location_address', 'party_location_lat', 'party_location_lng',
            'start_date', 'end_date', 'category', 'price_tier', 'expected_attendees',
            'actual_attendees', 'is_popular', 'is_trending', 'is_live', 'is_upcoming',
            'rsvp_count', 'user_rsvp_status', 'created_by', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'actual_attendees']

    def get_rsvp_count(self, obj):
        return obj.rsvps.filter(status='GOING').count()

    def get_user_rsvp_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rsvp = obj.rsvps.filter(user=request.user).first()
            return rsvp.status if rsvp else None
        return None

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class EventRSVPSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)

    class Meta:
        model = EventRSVP
        fields = ['id', 'user', 'event', 'event_name', 'status', 'created_at']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# --- User Location Serializer ---
class UserLocationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = UserLocation
        fields = ['id', 'user', 'latitude', 'longitude', 'accuracy', 'timestamp']
        read_only_fields = ['user', 'timestamp']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# --- Activity Feed Serializer ---
class ActivityFeedSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    party_location_name = serializers.CharField(source='party_location.name', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)

    class Meta:
        model = ActivityFeed
        fields = ['id', 'activity_type', 'user', 'party_location', 'party_location_name',
                  'event', 'event_name', 'message', 'timestamp']
        read_only_fields = ['timestamp']


# --- Enhanced PartyLocation Serializer ---
class PartyLocationSerializer(serializers.ModelSerializer):
    average_ranking = serializers.SerializerMethodField()
    current_attendees = serializers.SerializerMethodField()
    distance_km = serializers.FloatField(read_only=True, required=False)
    is_open_now = serializers.BooleanField(read_only=True)
    upcoming_events_count = serializers.SerializerMethodField()
    live_events_count = serializers.SerializerMethodField()

    class Meta:
        model = PartyLocation
        fields = [
            'id', 'name', 'description', 'latitude', 'longitude', 'address', 'city', 'country',
            'genre', 'price_tier', 'opening_time', 'closing_time',
            'current_crowd', 'vibe_level', 'average_rating', 'total_checkins',
            'average_ranking', 'current_attendees', 'distance_km', 'is_open_now',
            'upcoming_events_count', 'live_events_count', 'last_updated'
        ]

    def get_average_ranking(self, obj):
        avg = obj.rankings.aggregate(Avg('score'))['score__avg']
        return round(avg, 2) if avg else None

    def get_current_attendees(self, obj):
        return obj.checkins.filter(is_active=True).count()

    def get_upcoming_events_count(self, obj):
        return obj.events.filter(start_date__gt=timezone.now()).count()

    def get_live_events_count(self, obj):
        now = timezone.now()
        return obj.events.filter(start_date__lte=now, end_date__gte=now).count()


# --- Enhanced CheckIn Serializer ---
class CheckInSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    location_name = serializers.CharField(source='party_location.name', read_only=True)

    class Meta:
        model = CheckIn
        fields = ['id', 'user', 'username', 'party_location', 'location_name',
                  'timestamp', 'is_active']
        read_only_fields = ['user', 'timestamp', 'is_active']


# --- Other existing serializers remain the same ---
class StorySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Story
        fields = ['id', 'user', 'username', 'party_location', 'media_file', 'caption', 'timestamp']
        read_only_fields = ['user', 'timestamp']


class UserProfileSerializer(serializers.ModelSerializer):
    reputation_points = serializers.IntegerField(source='reputation.points', read_only=True)
    badges = serializers.StringRelatedField(many=True, read_only=True)
    current_checkin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio', 'avatar', 'reputation_points',
                  'badges', 'current_checkin']
        read_only_fields = ['email']

    def get_current_checkin(self, obj):
        active_checkin = obj.check_ins.filter(is_active=True).first()
        if active_checkin:
            return {
                'location_id': active_checkin.party_location.id,
                'location_name': active_checkin.party_location.name,
                'checked_in_at': active_checkin.timestamp
            }
        return None


class VideoSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    location_name = serializers.CharField(source='party_location.name', read_only=True)

    class Meta:
        model = Video
        fields = ['id', 'user', 'username', 'party_location', 'location_name',
                  'video_file', 'caption', 'is_live', 'timestamp']
        read_only_fields = ['user', 'timestamp']


class RankingSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Ranking
        fields = ['id', 'user', 'username', 'party_location', 'score', 'timestamp']
        read_only_fields = ['user', 'timestamp']


class PartyChatSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = PartyChat
        fields = ['user', 'message', 'timestamp']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'bio']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect credentials.")


class FriendshipSerializer(serializers.ModelSerializer):
    from_user = serializers.StringRelatedField()
    to_user = serializers.StringRelatedField()

    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'created_at']


class EventInviteSerializer(serializers.ModelSerializer):
    from_user = serializers.StringRelatedField()
    to_user = serializers.StringRelatedField()
    event_name = serializers.CharField(source='event.name', read_only=True)

    class Meta:
        model = EventInvite
        fields = ['id', 'event', 'event_name', 'from_user', 'to_user', 'message', 'status', 'created_at']



