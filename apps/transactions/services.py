from django.db import transaction
from .models import Transaction
from decimal import Decimal

def perform_deposit(account, amount):
    try:
        amount = Decimal(str(amount))
    except Exception:
        return False, "Invalid deposit amount."
        
    if amount <= 0:
        return False, "Deposit amount must be greater than zero."
        
    try:
        with transaction.atomic():
            # Refresh from db to avoid race conditions
            account.refresh_from_db(fields=['balance'])
            account.balance += Decimal(amount)
            account.save(update_fields=['balance'])
            
            Transaction.objects.create(
                to_account=account,
                amount=amount,
                type='DEPOSIT',
                status='SUCCESS'
            )
        return True, "Deposit successful."
    except Exception as e:
        return False, f"Deposit failed: {str(e)}"

def perform_withdraw(account, amount):
    try:
        amount = Decimal(str(amount))
    except Exception:
        return False, "Invalid withdrawal amount."
        
    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero."
        
    try:
        with transaction.atomic():
            account.refresh_from_db(fields=['balance'])
            if account.balance < Decimal(amount):
                # Optionally record a failed transaction here
                Transaction.objects.create(
                    from_account=account,
                    amount=amount,
                    type='WITHDRAW',
                    status='FAILED'
                )
                return False, "Insufficient balance."
                
            account.balance -= Decimal(amount)
            account.save(update_fields=['balance'])
            
            Transaction.objects.create(
                from_account=account,
                amount=amount,
                type='WITHDRAW',
                status='SUCCESS'
            )
        return True, "Withdrawal successful."
    except Exception as e:
        return False, f"Withdrawal failed: {str(e)}"

def perform_transfer(from_account, to_account, amount):
    try:
        amount = Decimal(str(amount))
    except Exception:
        return False, "Invalid transfer amount."
        
    if amount <= 0:
        return False, "Transfer amount must be greater than zero."
    if from_account == to_account:
        return False, "Cannot transfer to the same account."
        
    try:
        with transaction.atomic():
            # Lock both rows using select_for_update to prevent race conditions (double-click)
            from_acc = type(from_account).objects.select_for_update().get(pk=from_account.pk)
            to_acc = type(to_account).objects.select_for_update().get(pk=to_account.pk)
            
            if from_acc.balance < Decimal(amount):
                Transaction.objects.create(
                    from_account=from_acc,
                    to_account=to_acc,
                    amount=amount,
                    type='TRANSFER',
                    status='FAILED'
                )
                return False, "Insufficient balance for transfer."
                
            from_acc.balance -= Decimal(amount)
            from_acc.save(update_fields=['balance'])
            
            to_acc.balance += Decimal(amount)
            to_acc.save(update_fields=['balance'])
            
            Transaction.objects.create(
                from_account=from_acc,
                to_account=to_acc,
                amount=amount,
                type='TRANSFER',
                status='SUCCESS'
            )
        return True, "Transfer successful."
    except Exception as e:
        return False, f"Transfer failed: {str(e)}"
