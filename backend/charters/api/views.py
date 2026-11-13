from django.conf import settings
from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import BaseThrottle

from charters.models import DemoSession
from charters.services import create_demo_session
from charters.timeutil import request_timezone

from .throttles import DemoLoginThrottle

DEMO_USER_LABEL = "Demo User"

SessionInfo = inline_serializer(
    "SessionInfo",
    {
        "user": serializers.CharField(),
        "session_id": serializers.CharField(),
        "started_at": serializers.DateTimeField(),
        "server": serializers.CharField(),
    },
)


def session_info(demo: DemoSession, request: Request) -> dict:
    """The session object shared by demo-login and session (docs/API.md)."""
    started = timezone.localtime(demo.created_at, request_timezone(request))
    return {
        "user": DEMO_USER_LABEL,
        "session_id": demo.short_id,
        "started_at": started.isoformat(timespec="seconds"),
        "server": settings.DEMO_SERVER_NAME,
    }


def current_demo_session(request: Request) -> DemoSession | None:
    if not request.user.is_authenticated:
        return None
    return DemoSession.objects.filter(user=request.user).first()


@extend_schema(
    summary="Health check",
    responses=inline_serializer("Health", {"status": serializers.CharField()}),
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([])
def health(request: Request) -> Response:
    """Uptime check. Public, no session needed (docs/API.md)."""
    return Response({"status": "ok"})


@extend_schema(
    summary="Start a demo session",
    description=(
        "Creates a demo user with a private copy of the sample data, dated around today, "
        "and logs the browser in. Returns the existing session if one is already active. "
        "Throttled to 5 per hour per IP."
    ),
    request=None,
    responses={201: SessionInfo, 200: SessionInfo, 429: OpenApiResponse(description="Throttled")},
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([DemoLoginThrottle])
def demo_login(request: Request) -> Response:
    # DRF only checks CSRF for logged-in users; check it here too so another site
    # can't silently log a visitor into a sandbox.
    SessionAuthentication().enforce_csrf(request)

    existing = current_demo_session(request)
    if existing:
        return Response(session_info(existing, request))

    demo = create_demo_session(ip=BaseThrottle().get_ident(request), tz=request_timezone(request))
    login(request._request, demo.user, backend="django.contrib.auth.backends.ModelBackend")
    return Response(session_info(demo, request), status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Current session",
    description="The current demo session, or 401 when not logged in. Also sets the CSRF cookie.",
    responses={200: SessionInfo, 401: OpenApiResponse(description="Not logged in")},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def session(request: Request) -> Response:
    get_token(request._request)  # make sure the browser has a CSRF cookie for later POSTs
    demo = current_demo_session(request)
    if demo is None:
        return Response({"detail": "Not logged in."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(session_info(demo, request))


@extend_schema(
    summary="Log out",
    description="Ends the browser session. The sandbox is left for the cleanup job.",
    request=None,
    responses={204: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request: Request) -> Response:
    logout(request._request)
    return Response(status=status.HTTP_204_NO_CONTENT)
