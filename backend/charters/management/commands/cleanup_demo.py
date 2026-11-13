from django.core.management.base import BaseCommand

from charters.services import cleanup_demo


class Command(BaseCommand):
    help = "Delete demo users (and their sandboxes) older than 24 hours. Run once a day."

    def handle(self, *args, **options) -> None:
        count = cleanup_demo()
        self.stdout.write(self.style.SUCCESS(f"Deleted {count} expired demo sandbox(es)."))
