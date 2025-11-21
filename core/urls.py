# core/urls.py
from django.urls import path, include
from rest_framework import routers
from . import views
from django.urls import get_resolver
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def debug_urls(request):
    """Debug view to see all available URLs"""
    resolver = get_resolver()
    url_patterns = []
    
    def list_urls(patterns, prefix=''):
        for pattern in patterns:
            if hasattr(pattern, 'url_patterns'):
                list_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                url_patterns.append({
                    'pattern': prefix + str(pattern.pattern),
                    'name': getattr(pattern, 'name', 'No name')
                })
    
    list_urls(resolver.url_patterns)
    return Response(url_patterns)

router = routers.DefaultRouter()
router.register(r'partylocations', views.PartyLocationViewSet, basename='partylocation')
router.register(r'videos', views.VideoViewSet, basename='video')
router.register(r'rankings', views.RankingViewSet, basename='ranking')
router.register(r'checkins', views.CheckInViewSet, basename='checkin')
router.register(r'stories', views.StoryViewSet, basename='story')
router.register(r'friendships', views.FriendshipViewSet, basename='friendship')
router.register(r'invites', views.EventInviteViewSet, basename='invite')
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'user-locations', views.UserLocationViewSet, basename='userlocation')
router.register(r'activity-feed', views.ActivityFeedViewSet, basename='activityfeed')

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('password_reset/', include('django.contrib.auth.urls')),


    # User Profile URL
    path('profile/', views.UserProfileView.as_view(), name='my-profile'),
    path('profile/<int:user_id>/', views.UserProfileView.as_view(), name='user-profile'),

    # Map Data API
    path('map-data/', views.MapDataAPIView.as_view(), name='map-data'),

    # Debug URL
    path('debug-urls/', debug_urls, name='debug-urls'),

    # COMPATIBILITY ENDPOINTS - FIX THE 404 ERRORS
    path('locations/', views.PartyLocationViewSet.as_view({'get': 'list'}), name='locations-legacy'),
    path('events/', views.EventViewSet.as_view({'get': 'list'}), name='events-legacy'),

    # Include Router URLs
    path('', include(router.urls)),
    path('external-events/', views.ExternalEventsAPIView.as_view(), name='external-events'),
    path('public/events/', views.PublicEventsAPIView.as_view(), name='public-events'),
    path('public/locations/', views.PublicLocationsAPIView.as_view(), name='public-locations'),
    path('ticketmaster-proxy/', views.ticketmaster_proxy, name='ticketmaster-proxy'),

]
