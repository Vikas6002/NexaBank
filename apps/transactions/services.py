from django.db import transaction
from .models import Transaction
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

def perform_deposit(account, amount):
    try:
        amount = Decimal(str(amount))
    except Exception:
        return False, "Invalid deposit amount."
        
    if amount <= 0:
        return False, "Deposit amount must be greater than zero."
    if account.is_frozen:
        return False, "This account is frozen. Transactions are blocked."
        
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
    if account.is_frozen:
        return False, "This account is frozen. Transactions are blocked."
        
    try:
        with transaction.atomic():
            account.refresh_from_db(fields=['balance'])
            
            from apps.dashboard.models import SystemSettings
            from django.db import models
            sys_settings = SystemSettings.get_settings()

            if (account.balance - Decimal(amount)) < sys_settings.minimum_balance:
                Transaction.objects.create(
                    from_account=account,
                    amount=amount,
                    type='WITHDRAW',
                    status='FAILED'
                )
                return False, f"Withdrawal violates minimum balance constraint of ₹{sys_settings.minimum_balance}."
                
            from django.utils import timezone
            
            today = timezone.now().date()
            daily_withdrawals = Transaction.objects.filter(
                from_account=account,
                type='WITHDRAW',
                status='SUCCESS',
                timestamp__date=today
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            if (daily_withdrawals + Decimal(amount)) > sys_settings.daily_withdrawal_limit:
                Transaction.objects.create(
                    from_account=account,
                    amount=amount,
                    type='WITHDRAW',
                    status='FAILED'
                )
                return False, f"Exceeds daily withdrawal limit of ₹{sys_settings.daily_withdrawal_limit}."

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
    if from_account.is_frozen or to_account.is_frozen:
        return False, "One of the accounts is frozen. Transfer blocked."
        
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
                
            # FRAUD RULES - Velocity Check (Anti-Spam)
            five_mins_ago = timezone.now() - timedelta(minutes=5)
            recent_transfers = Transaction.objects.filter(
                from_account=from_acc,
                type='TRANSFER',
                timestamp__gte=five_mins_ago
            ).count()
            
            is_flagged = recent_transfers >= 3
            flag_reason = "High velocity transfers detected (Anti-Spam)" if is_flagged else None
            
            # FRAUD RULES - Amount Threshold (Dynamic)
            from apps.dashboard.models import SystemSettings
            sys_settings = SystemSettings.get_settings()
            
            requires_approval = Decimal(amount) > sys_settings.max_transfer_limit
            
            # Constraint: Minimum Balance
            if (from_acc.balance - Decimal(amount)) < sys_settings.minimum_balance:
                Transaction.objects.create(
                    from_account=from_acc,
                    to_account=to_acc,
                    amount=amount,
                    type='TRANSFER',
                    status='FAILED',
                    flag_reason=f"Violates minimum balance ₹{sys_settings.minimum_balance}"
                )
                return False, f"Transfer violated Minimum Balance protocol."
            
            if requires_approval:
                flag_reason = f"Transfer exceeds max limit of ₹{sys_settings.max_transfer_limit}."
                is_flagged = True
                
                Transaction.objects.create(
                    from_account=from_acc,
                    to_account=to_acc,
                    amount=amount,
                    type='TRANSFER',
                    status='PENDING_APPROVAL',
                    is_flagged=is_flagged,
                    flag_reason=flag_reason
                )
                return True, f"Transfer over limit flagged for Admin Review."
                
            from_acc.balance -= Decimal(amount)
            from_acc.save(update_fields=['balance'])
            
            to_acc.balance += Decimal(amount)
            to_acc.save(update_fields=['balance'])
            
            Transaction.objects.create(
                from_account=from_acc,
                to_account=to_acc,
                amount=amount,
                type='TRANSFER',
                status='SUCCESS',
                is_flagged=is_flagged,
                flag_reason=flag_reason
            )
        return True, "Transfer successful."
    except Exception as e:
        return False, f"Transfer failed: {str(e)}"
