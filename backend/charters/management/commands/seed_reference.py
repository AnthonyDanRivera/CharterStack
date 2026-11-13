from django.core.management.base import BaseCommand

from charters.services import seed_reference


class Command(BaseCommand):
    help = "Load terminals, drivers, buses and ZIP codes from seed/seed_demo.json. Idempotent."

    def handle(self, *args, **options) -> None:
        counts = seed_reference()
        summary = ", ".join(f"{n} {kind.replace('_', ' ')}" for kind, n in counts.items())
        self.stdout.write(self.style.SUCCESS(f"Reference data loaded: {summary}."))
