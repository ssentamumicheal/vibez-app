# core/views.py
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout

# core/views.py
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import F, Avg, Case, When, Value, BooleanField, Count, Q
from datetime import datetime, time, timedelta
from math import radians, sin, cos, sqrt, atan2
from django.utils import timezone

# IMPORT ALL MODELS INCLUDING NEW ONES
from .models import PartyLocation, Video, Ranking, CheckIn, Story, User, UserReputation, Friendship, EventInvite, Event, \
    EventRSVP, UserLocation, ActivityFeed
from .serializers import (
    PartyLocationSerializer, VideoSerializer, RankingSerializer,
    UserRegistrationSerializer, UserLoginSerializer, CheckInSerializer,
    StorySerializer, UserProfileSerializer, FriendshipSerializer, EventInviteSerializer,
    EventSerializer, EventRSVPSerializer, UserLocationSerializer, ActivityFeedSerializer
)
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout
import requests
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests

@csrf_exempt
def ticketmaster_proxy(request):
    """Proxy for Ticketmaster API to avoid CORS issues"""
    if request.method == 'GET':
        try:
            # Get parameters from request
            city = request.GET.get('city', 'Kampala')
            genre = request.GET.get('genre', 'Music')
            size = request.GET.get('size', '20')

            # Make request to Ticketmaster
            params = {
                'apikey': settings.TICKETMASTER_API_KEY,
                'city': city,
                'classificationName': genre,
                'size': size,
                'sort': 'date,asc'
            }

            response = requests.get(
                'https://app.ticketmaster.com/discovery/v2/events.json',
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return JsonResponse(data)
            else:
                return JsonResponse({'error': 'Ticketmaster API error'}, status=500)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


class PublicEventsAPIView(APIView):
    """Public events endpoint that doesn't require authentication"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Get events without authentication"""
        # Return sample events or events from your database
        events = Event.objects.filter(start_date__gte=timezone.now())[:10]
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data)


class PublicLocationsAPIView(APIView):
    """Public locations endpoint that doesn't require authentication"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Get locations without authentication"""
        locations = PartyLocation.objects.all()[:20]
        serializer = PartyLocationSerializer(locations, many=True, context={'request': request})
        return Response(serializer.data)


class ExternalEventsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticketmaster_service = TicketMasterService()

    def get(self, request):
        """Get external events from Ticketmaster"""
        city = request.query_params.get('city', 'Kampala')
        genre = request.query_params.get('genre', 'Music')
        limit = int(request.query_params.get('limit', 20))

        events = self.ticketmaster_service.search_events(
            city=city,
            classification_name=genre,
            size=limit
        )

        return Response({
            'events': events,
            'source': 'ticketmaster',
            'city': city,
            'genre': genre,
            'total_count': len(events)
        })

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Event.objects.all()

        # Your existing filtering logic here...
        # ... keep all your existing filters

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to include Ticketmaster events"""
        # Get local events
        local_events = self.filter_queryset(self.get_queryset())
        local_serializer = self.get_serializer(local_events, many=True)
        local_events_data = local_serializer.data

        # Get Ticketmaster events if requested
        include_external = request.query_params.get('include_external', 'true').lower() == 'true'
        external_events = []

        if include_external:
            try:
                # Get Ticketmaster events
                tm_events = self.ticketmaster_service.search_events(
                    city=request.query_params.get('city', 'Kampala'),
                    classification_name=request.query_params.get('genre', 'Music'),
                    size=request.query_params.get('external_limit', 10)
                )
                external_events = tm_events
            except Exception as e:
                print(f"Error fetching external events: {e}")

        # Combine events
        all_events = {
            'local_events': local_events_data,
            'external_events': external_events,
            'total_count': len(local_events_data) + len(external_events)
        }

        return Response(all_events)


class TicketMasterService:
    def __init__(self):
        self.api_key = '7mmwork/OAxGbYB4OxyI0C6jGtHexVOxy'  # Your consumer key
        self.base_url = 'https://app.ticketmaster.com/discovery/v2/'

    def search_events(self, city='Kampala', classification_name='Music', size=20):
        """Fetch events from Ticketmaster API"""
        try:
            params = {
                'apikey': self.api_key,
                'city': city,
                'classificationName': classification_name,
                'size': size,
                'sort': 'date,asc'
            }

            response = requests.get(f"{self.base_url}events.json", params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._parse_events(data)
            else:
                print(f"Ticketmaster API error: {response.status_code}")
                return []

        except requests.RequestException as e:
            print(f"Error fetching from Ticketmaster: {e}")
            return []

    def _parse_events(self, data):
        """Parse Ticketmaster events into our format"""
        events = []

        if '_embedded' in data and 'events' in data['_embedded']:
            for event_data in data['_embedded']['events']:
                try:
                    # Extract venue information
                    venue = event_data.get('_embedded', {}).get('venues', [{}])[0]

                    # Parse date
                    start_date = event_data['dates']['start']['dateTime']

                    event = {
                        'id': f"tm_{event_data['id']}",
                        'name': event_data['name'],
                        'description': event_data.get('info', ''),
                        'start_date': start_date,
                        'venue_name': venue.get('name', ''),
                        'venue_address': f"{venue.get('address', {}).get('line1', '')}, {venue.get('city', {}).get('name', '')}",
                        'venue_lat': venue.get('location', {}).get('latitude'),
                        'venue_lng': venue.get('location', {}).get('longitude'),
                        'images': [img['url'] for img in event_data.get('images', []) if img.get('url')],
                        'url': event_data.get('url', ''),
                        'price_range': event_data.get('priceRanges', [{}])[0],
                        'source': 'ticketmaster'
                    }
                    events.append(event)

                except (KeyError, IndexError) as e:
                    print(f"Error parsing event: {e}")
                    continue

        return events


    # Frontend view
def index(request):
    return render(request, 'index.html')


# Utility for Haversine Distance (1. Proximity Search)
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points on Earth using Haversine formula."""
    R = 6371  # Earth radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# --- 1. Enhanced PartyLocationViewSet with Real-Time Features ---
class PartyLocationViewSet(viewsets.ModelViewSet):
    queryset = PartyLocation.objects.all()
    serializer_class = PartyLocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = PartyLocation.objects.all()

        # --- Proximity Search ---
        user_lat = self.request.query_params.get('user_lat')
        user_lon = self.request.query_params.get('user_lon')
        radius_km = self.request.query_params.get('radius_km', 10)  # Default 10km

        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                radius_km = float(radius_km)

                # Filter by distance using Haversine
                locations_with_distance = []
                for location in queryset:
                    distance = haversine_distance(user_lat, user_lon, location.latitude, location.longitude)
                    if distance <= radius_km:
                        location.distance_km = round(distance, 2)
                        locations_with_distance.append(location)

                queryset = locations_with_distance

            except ValueError:
                pass

        # --- Smart Filters ---
        # Filter by Vibe Level
        vibe_level = self.request.query_params.get('vibe_level')
        if vibe_level:
            queryset = queryset.filter(vibe_level=vibe_level.upper())

        # Filter by Crowd Level
        min_crowd = self.request.query_params.get('min_crowd')
        max_crowd = self.request.query_params.get('max_crowd')
        if min_crowd:
            queryset = queryset.filter(current_crowd__gte=min_crowd)
        if max_crowd:
            queryset = queryset.filter(current_crowd__lte=max_crowd)

        # Filter by Average Rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)

        # Filter by Genre
        genre = self.request.query_params.get('genre')
        if genre:
            queryset = queryset.filter(genre__iexact=genre)

        # Filter by Price Tier
        price_tier = self.request.query_params.get('price_tier')
        if price_tier:
            queryset = queryset.filter(price_tier=price_tier)

        # Filter by 'Currently Open'
        if self.request.query_params.get('is_open') == 'true':
            queryset = queryset.filter(is_open_now=True)

        # Filter by Live Events
        if self.request.query_params.get('has_live_events') == 'true':
            now = timezone.now()
            queryset = queryset.filter(events__start_date__lte=now, events__end_date__gte=now).distinct()

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # If the queryset is a list of objects (from the Haversine logic), sort it by distance
        if isinstance(queryset, list) and queryset and hasattr(queryset[0], 'distance_km'):
            queryset = sorted(queryset, key=lambda x: x.distance_km)
        # If it's a Django QuerySet, we apply default sorting
        elif hasattr(queryset, 'order_by'):
            sort_by = request.query_params.get('sort_by', '-last_updated')
            if sort_by in ['distance', '-distance', 'crowd', '-crowd', 'rating', '-rating']:
                if sort_by == 'distance':
                    queryset = sorted(queryset, key=lambda x: getattr(x, 'distance_km', 0))
                elif sort_by == '-distance':
                    queryset = sorted(queryset, key=lambda x: getattr(x, 'distance_km', 0), reverse=True)
                elif sort_by == 'crowd':
                    queryset = queryset.order_by('current_crowd')
                elif sort_by == '-crowd':
                    queryset = queryset.order_by('-current_crowd')
                elif sort_by == 'rating':
                    queryset = queryset.order_by('average_rating')
                elif sort_by == '-rating':
                    queryset = queryset.order_by('-average_rating')
            else:
                queryset = queryset.order_by(sort_by)

        # Pagination logic remains the same
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_crowd_level(self, request, pk=None):
        """Update crowd level for a location"""
        location = self.get_object()
        crowd_level = request.data.get('crowd_level')

        if crowd_level is not None:
            try:
                crowd_level = int(crowd_level)
                if 0 <= crowd_level <= 100:
                    location.current_crowd = crowd_level
                    location.save()

                    # Create activity feed entry
                    ActivityFeed.objects.create(
                        activity_type='CHECKIN',
                        user=request.user,
                        party_location=location,
                        message=f"Crowd level updated to {crowd_level}% at {location.name}"
                    )

                    return Response({'message': 'Crowd level updated successfully'})
                else:
                    return Response({'error': 'Crowd level must be between 0 and 100'},
                                    status=status.HTTP_400_BAD_REQUEST)
            except ValueError:
                return Response({'error': 'Invalid crowd level'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'error': 'Crowd level is required'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def trending_locations(self, request):
        """Get trending locations based on check-ins and activity"""
        trending_locations = PartyLocation.objects.annotate(
            recent_checkins=Count('checkins', filter=Q(checkins__timestamp__gte=timezone.now() - timedelta(hours=24))),
            recent_videos=Count('videos', filter=Q(videos__timestamp__gte=timezone.now() - timedelta(hours=24)))
        ).order_by('-recent_checkins', '-recent_videos')[:10]

        serializer = self.get_serializer(trending_locations, many=True)
        return Response(serializer.data)


# --- 2. Events ViewSet ---
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Event.objects.all()

        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category.upper())

        # Filter by time frame
        time_frame = self.request.query_params.get('time_frame', 'upcoming')
        now = timezone.now()

        if time_frame == 'live':
            queryset = queryset.filter(start_date__lte=now, end_date__gte=now)
        elif time_frame == 'today':
            tomorrow = now + timedelta(days=1)
            queryset = queryset.filter(start_date__date=now.date())
        elif time_frame == 'weekend':
            # Get upcoming weekend
            days_until_saturday = (5 - now.weekday() + 7) % 7
            saturday = now + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            queryset = queryset.filter(start_date__date__range=[saturday.date(), sunday.date()])
        elif time_frame == 'week':
            next_week = now + timedelta(days=7)
            queryset = queryset.filter(start_date__range=[now, next_week])
        elif time_frame == 'month':
            next_month = now + timedelta(days=30)
            queryset = queryset.filter(start_date__range=[now, next_month])
        else:  # upcoming (default)
            queryset = queryset.filter(start_date__gte=now)

        # Filter by location proximity
        user_lat = self.request.query_params.get('user_lat')
        user_lon = self.request.query_params.get('user_lon')
        radius_km = self.request.query_params.get('radius_km', 50)  # Default 50km

        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                radius_km = float(radius_km)

                events_with_distance = []
                for event in queryset:
                    distance = haversine_distance(user_lat, user_lon,
                                                  float(event.party_location.latitude),
                                                  float(event.party_location.longitude))
                    if distance <= radius_km:
                        event.distance_km = round(distance, 2)
                        events_with_distance.append(event)

                queryset = events_with_distance
            except ValueError:
                pass

        # Sort events
        sort_by = self.request.query_params.get('sort_by', 'start_date')
        if sort_by == 'popularity':
            queryset = queryset.order_by('-is_popular', '-is_trending', '-expected_attendees')
        elif sort_by == 'distance':
            if hasattr(queryset, '__iter__') and not isinstance(queryset, type(Event.objects.all())):
                queryset = sorted(queryset, key=lambda x: getattr(x, 'distance_km', 0))
        else:  # date
            queryset = queryset.order_by('start_date')

        return queryset

    def perform_create(self, serializer):
        event = serializer.save(created_by=self.request.user)

        # Create activity feed entry
        ActivityFeed.objects.create(
            activity_type='EVENT',
            user=self.request.user,
            event=event,
            party_location=event.party_location,
            message=f"New event created: {event.name}"
        )

    @action(detail=True, methods=['post'])
    def rsvp(self, request, pk=None):
        """RSVP to an event"""
        event = self.get_object()
        status = request.data.get('status', 'INTERESTED')

        if status not in ['GOING', 'INTERESTED', 'NOT_GOING']:
            return Response({'error': 'Invalid RSVP status'}, status=status.HTTP_400_BAD_REQUEST)

        # Update or create RSVP
        rsvp, created = EventRSVP.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={'status': status}
        )

        # Update event attendees count
        if status == 'GOING':
            event.actual_attendees = event.rsvps.filter(status='GOING').count()
            event.save()

        # Create activity feed entry
        ActivityFeed.objects.create(
            activity_type='RSVP',
            user=request.user,
            event=event,
            message=f"RSVP'd {status.lower()} to {event.name}"
        )

        serializer = EventRSVPSerializer(rsvp)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_rsvps(self, request):
        """Get events the user has RSVP'd to"""
        rsvps = EventRSVP.objects.filter(user=request.user).select_related('event')
        serializer = EventRSVPSerializer(rsvps, many=True)
        return Response(serializer.data)


    # --- 3. Enhanced CheckIn System ---
class CheckInViewSet(viewsets.ModelViewSet):
    queryset = CheckIn.objects.all()
    serializer_class = CheckInSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']

    def get_queryset(self):
        # Shows active check-ins for a location, or the user's active check-ins
        location_id = self.request.query_params.get('location_id')
        if location_id:
            return CheckIn.objects.filter(party_location_id=location_id, is_active=True).select_related('user')

        return CheckIn.objects.filter(user=self.request.user, is_active=True).select_related('user')

    def perform_create(self, serializer):
        # Check if user already has an active check-in
        active_checkin = CheckIn.objects.filter(user=self.request.user, is_active=True).first()
        if active_checkin:
            # Auto-checkout from previous location
            active_checkin.is_active = False
            active_checkin.save()

            # Update previous location crowd level
            self.update_location_crowd(active_checkin.party_location, -1)

        checkin = serializer.save(user=self.request.user)

        # Update location crowd level
        self.update_location_crowd(checkin.party_location, 1)

        # Update user reputation
        reputation, created = UserReputation.objects.get_or_create(user=self.request.user)
        reputation.points += 5  # Award 5 points for check-in
        reputation.save()

        # Create activity feed entry
        ActivityFeed.objects.create(
            activity_type='CHECKIN',
            user=self.request.user,
            party_location=checkin.party_location,
            message=f"Checked in at {checkin.party_location.name}"
        )

    def update_location_crowd(self, location, change):
        """Update crowd level based on check-in/check-out"""
        new_crowd = location.current_crowd + change
        location.current_crowd = max(0, min(100, new_crowd))
        location.total_checkins += 1 if change > 0 else 0
        location.save()

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        """Custom action to allow a user to check out of a location."""
        location_id = request.data.get('party_location')
        if not location_id:
            return Response({'detail': 'party_location ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            check_in = CheckIn.objects.get(user=request.user, party_location_id=location_id, is_active=True)
            check_in.is_active = False
            check_in.save()

            # Update location crowd level
            self.update_location_crowd(check_in.party_location, -1)

            # Award points on check-out
            reputation, created = UserReputation.objects.get_or_create(user=request.user)
            reputation.points += 10
            reputation.save()

            return Response({'message': 'Checked out successfully. You earned 10 points!'}, status=status.HTTP_200_OK)
        except CheckIn.DoesNotExist:
            return Response({'detail': 'No active check-in found for this user and location.'},
                            status=status.HTTP_404_NOT_FOUND)


    # --- 4. User Location Tracking ---
class UserLocationViewSet(viewsets.ModelViewSet):
    queryset = UserLocation.objects.all()
    serializer_class = UserLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserLocation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        location = serializer.save(user=self.request.user)

        # Find nearby parties and events
        self.find_nearby_parties(location)

        return location

    def find_nearby_parties(self, user_location):
        """Find and suggest nearby parties based on user location"""
        nearby_locations = []
        for location in PartyLocation.objects.all():
            distance = haversine_distance(
                float(user_location.latitude), float(user_location.longitude),
                float(location.latitude), float(location.longitude)
            )
            if distance <= 5:  # Within 5km
                nearby_locations.append({
                    'location': location,
                    'distance': distance
                })

        # Could send notifications about nearby parties here
        return nearby_locations


    # --- 5. Activity Feed ViewSet ---
class ActivityFeedViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityFeed.objects.all()
    serializer_class = ActivityFeedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get activities for locations and events the user might be interested in
        user = self.request.user

        # Get user's checked-in location
        user_checkin = CheckIn.objects.filter(user=user, is_active=True).first()

        if user_checkin:
            # Show activities from current location and nearby locations
            current_location = user_checkin.party_location
            queryset = ActivityFeed.objects.filter(
                Q(party_location=current_location) |
                Q(party_location__city=current_location.city)
            )
        else:
            # Show popular activities in the user's city (default to Kampala)
            queryset = ActivityFeed.objects.filter(party_location__city='Kampala')

        # Filter by activity type if specified
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type.upper())

        return queryset.order_by('-timestamp')[:50]  # Limit to 50 most recent


    # --- 6. Real-Time Map Data API ---
class MapDataAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        """Get comprehensive map data including locations, events, and user activity"""
        user_lat = request.query_params.get('lat')
        user_lon = request.query_params.get('lon')
        radius_km = request.query_params.get('radius', 20)

        map_data = {
            'locations': [],
            'events': [],
            'user_activity': [],
            'trending_locations': []
        }

        # Get locations within radius
        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                radius_km = float(radius_km)

                locations = []
                for location in PartyLocation.objects.all():
                    distance = haversine_distance(user_lat, user_lon,
                                                  float(location.latitude),
                                                  float(location.longitude))
                    if distance <= radius_km:
                        location_data = PartyLocationSerializer(location, context={'request': request}).data
                        location_data['distance_km'] = round(distance, 2)
                        locations.append(location_data)

                map_data['locations'] = sorted(locations, key=lambda x: x['distance_km'])

            except ValueError:
                map_data['locations'] = PartyLocationSerializer(
                    PartyLocation.objects.all()[:20],
                    many=True,
                    context={'request': request}
                ).data
        else:
            map_data['locations'] = PartyLocationSerializer(
                PartyLocation.objects.all()[:20],
                many=True,
                context={'request': request}
            ).data

        # Get live and upcoming events
        now = timezone.now()
        live_events = Event.objects.filter(start_date__lte=now, end_date__gte=now)
        upcoming_events = Event.objects.filter(start_date__gt=now, start_date__lte=now + timedelta(days=7))

        map_data['events'] = EventSerializer(
            list(live_events) + list(upcoming_events),
            many=True,
            context={'request': request}
        ).data

        # Get recent user activity
        map_data['user_activity'] = ActivityFeedSerializer(
            ActivityFeed.objects.all()[:10],
            many=True,
            context={'request': request}
        ).data

        # Get trending locations
        trending_locations = PartyLocation.objects.annotate(
            recent_activity=Count('checkins', filter=Q(checkins__timestamp__gte=timezone.now() - timedelta(hours=6)))
        ).order_by('-recent_activity', '-current_crowd')[:5]

        map_data['trending_locations'] = PartyLocationSerializer(
            trending_locations,
            many=True,
            context={'request': request}
        ).data

        return Response(map_data)


    # --- 7. Existing Views (Keep these from your original code) ---
class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        time_limit = timezone.now() - timedelta(hours=24)
        queryset = Story.objects.filter(timestamp__gte=time_limit).order_by('-timestamp')

        location_id = self.request.query_params.get('location_id')
        if location_id:
            queryset = queryset.filter(party_location_id=location_id)

        return queryset.select_related('user', 'party_location')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id=None):
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user

        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all().order_by('-timestamp')
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        video = serializer.save(user=self.request.user)

        # Create activity feed entry
        ActivityFeed.objects.create(
            activity_type='VIDEO',
            user=self.request.user,
            party_location=video.party_location,
            message=f"Uploaded a video at {video.party_location.name}"
        )


class RankingViewSet(viewsets.ModelViewSet):
    queryset = Ranking.objects.all().order_by('-timestamp')
    serializer_class = RankingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        ranking = serializer.save(user=self.request.user)

        # Update location average rating
        location = ranking.party_location
        avg_rating = location.rankings.aggregate(Avg('score'))['score__avg']
        location.average_rating = round(avg_rating, 2) if avg_rating else 4.0
        location.save()

        # Create activity feed entry
        ActivityFeed.objects.create(
            activity_type='REVIEW',
            user=self.request.user,
            party_location=location,
            message=f"Rated {location.name} {ranking.score} stars"
        )


class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            if user:
                token = Token.objects.create(user=user)
                json_data = serializer.data
                json_data['token'] = token.key
                return Response(json_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'username': user.username}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class FriendshipViewSet(viewsets.ModelViewSet):
    queryset = Friendship.objects.all()
    serializer_class = FriendshipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Friendship.objects.filter(from_user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)


class EventInviteViewSet(viewsets.ModelViewSet):
    queryset = EventInvite.objects.all()
    serializer_class = EventInviteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EventInvite.objects.filter(to_user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)



class ExternalEventsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticketmaster_service = TicketMasterService()

    def get(self, request):
        """Get external events from Ticketmaster"""
        city = request.query_params.get('city', 'Kampala')
        genre = request.query_params.get('genre', 'Music')
        limit = int(request.query_params.get('limit', 20))
        
        events = self.ticketmaster_service.search_events(
            city=city,
            classification_name=genre,
            size=limit
        )
        
        return Response({
            'events': events,
            'source': 'ticketmaster',
            'city': city,
            'genre': genre,
            'total_count': len(events)
        })
