import random
import string

def generate_account_number():
    """Generates a random 10-digit account number."""
    return ''.join(random.choices(string.digits, k=10))
