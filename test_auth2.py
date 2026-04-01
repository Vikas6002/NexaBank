import os
import sys
import django
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "NexaBank.settings")
django.setup()

from apps.accounts.models import CustomUser
from django.contrib.auth import authenticate
from apps.accounts.forms import LoginForm

user = CustomUser.objects.last()
if user:
    print(f"Testing user: {user.email}, is_active={user.is_active}, is_verified={user.is_verified}")
    user.set_password('TestPass123')
    user.save()
    
    auth_user = authenticate(email=user.email, password='TestPass123')
    print(f"Direct auth with TestPass123: {auth_user}")
    
    form = LoginForm(data={'email': user.email, 'password': 'TestPass123'})
    try:
        is_valid = form.is_valid()
        print(f"LoginForm valid: {is_valid}")
        print(f"LoginForm errors: {form.errors}")
    except Exception as e:
        print("EXCEPTION IN FORM:")
        traceback.print_exc()
