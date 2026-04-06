import os
import django
import random
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NexaBank.settings')
django.setup()

from apps.accounts.models import CustomUser
from apps.banking.models import BankAccount
import decimal

def get_rand_acc():
    return ''.join(random.choices('0123456789', k=10))

users_data = [
    ('alice.smith@example.com', [('Savings', 12500, False)]),
    ('bob.johnson@example.com', [('Current', 4500, False)]),
    ('charlie.brown@example.com', [('Savings', 8900, False)]),
    ('diana.prince@example.com', [('Savings', 152000, False), ('Current', 500, False)]),
    ('ethan.hunt@example.com', [('Current', 100, True)])
]

added_count = 0
for email, accounts in users_data:
    if not CustomUser.objects.filter(email=email).exists():
        user = CustomUser(
            email=email,
            role='CUSTOMER',
            is_verified=True
        )
        user.set_password('Password123!')
        user.save()
        
        for acc_type, bal, frozen in accounts:
            while True:
                try:
                    BankAccount.objects.create(
                        user=user, 
                        account_type=acc_type, 
                        balance=decimal.Decimal(bal), 
                        is_frozen=frozen,
                        account_number=get_rand_acc()
                    )
                    break
                except Exception as e:
                    print("Retrying account number generation...")
                    pass
        added_count += 1

print(f'SUCCESSFULLY ADDED {added_count} USERS')
