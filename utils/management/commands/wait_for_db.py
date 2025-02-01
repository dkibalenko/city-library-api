import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Wait for the database to become available"

    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        db_conn = None
        retry_count = 0
        max_retries = 20

        while not db_conn:
            if retry_count > max_retries:
                self.stdout.write(
                    self.style.ERROR(
                        f"Database is not available after {max_retries} "
                        f"retries, exiting"
                    )
                )
                return

            try:
                db_conn = connections["default"]
                db_conn.connect()
            except OperationalError:
                retry_count += 1
                self.stdout.write(
                    f"Database is not available, waiting 1 second and "
                    f"retry {retry_count}"
                )
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database is available!"))
