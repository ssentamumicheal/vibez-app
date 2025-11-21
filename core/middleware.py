# core/middleware.py
from django.http import HttpResponsePermanentRedirect

class DoubleSlashRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if path has double slashes
        if '//' in request.path:
            # Redirect to the correct path
            new_path = request.path.replace('//', '/')
            return HttpResponsePermanentRedirect(new_path)
        
        response = self.get_response(request)
        return response
