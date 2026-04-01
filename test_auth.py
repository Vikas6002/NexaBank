from accounts.models import CustomUser
from django.contrib.auth import authenticate

user = CustomUser.objects.last()
print("Latest user:", user.email if user else "None")
if user:
    print("Is active:", user.is_active)
    print("Has usable password:", user.has_usable_password())
    # We don't know the password, but we can reset it to 'testpass123' and save
    user.set_password('testpass123')
    user.save()
    
    auth_user = authenticate(email=user.email, password='testpass123')
    print("Authenticate with testpass123:", auth_user)
