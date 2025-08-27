import os
import django

# Django settings load karo
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trainer_dashboard.settings")
django.setup()

from django.contrib.auth.models import User

# Trainer list (name + password)
trainers = [
    {"username": "abhishek", "password": "abhi"},
    {"username": "rahul", "password": "rahul123"},
    {"username": "sneha", "password": "sneha321"},
]

# Users create karna
for t in trainers:
    if not User.objects.filter(username=t["username"]).exists():
        User.objects.create_user(username=t["username"], password=t["password"])
        print(f'Trainer {t["username"]} created!')
    else:
        print(f'Trainer {t["username"]} already exists!')

print("All trainers ready for login!")
