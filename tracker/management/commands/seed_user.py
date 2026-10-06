from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create a default demo user (admin / admin123)'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='admin')
        user.set_password('admin123')
        user.is_staff = True
        user.is_superuser = True
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created default user "admin" with password "admin123"'))
        else:
            self.stdout.write(self.style.SUCCESS('User "admin" already exists; password reset to "admin123"'))
