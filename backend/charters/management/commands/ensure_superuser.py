import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Create or update the admin superuser from DJANGO_SUPERUSER_USERNAME, "
        "DJANGO_SUPERUSER_PASSWORD and DJANGO_SUPERUSER_EMAIL. Safe to run on every deploy; "
        "does nothing when the variables are not set."
    )

    def handle(self, *args, **options) -> None:
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        if not username and not password:
            self.stdout.write("No superuser variables set; skipping.")
            return
        if not username or not password:
            raise CommandError("Set both DJANGO_SUPERUSER_USERNAME and DJANGO_SUPERUSER_PASSWORD.")
        if username.startswith("demo_"):
            raise CommandError(
                "The admin username can't start with demo_ (reserved for sandboxes)."
            )

        user, created = get_user_model().objects.get_or_create(
            username=username, defaults={"email": email}
        )
        user.is_staff = True
        user.is_superuser = True
        if email:
            user.email = email
        user.set_password(password)  # keeps the password in sync with the env var
        user.save()
        self.stdout.write(
            self.style.SUCCESS(f"Superuser {username} {'created' if created else 'updated'}.")
        )
