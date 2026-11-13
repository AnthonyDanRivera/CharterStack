from django.utils import timezone

from .timeutil import request_timezone


class VisitorTimezoneMiddleware:
    """Activate the visitor's `X-Timezone` so datetimes render in their local time."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate(request_timezone(request))
        try:
            return self.get_response(request)
        finally:
            timezone.deactivate()
