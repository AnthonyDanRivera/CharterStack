from rest_framework.throttling import SimpleRateThrottle


class DemoLoginThrottle(SimpleRateThrottle):
    """Demo login: 5 per hour per IP, logged in or not (DEMO_SANDBOX.md)."""

    scope = "demo_login"

    def get_cache_key(self, request, view) -> str:
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
