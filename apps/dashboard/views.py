from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from apps.core.decorators import role_required
from apps.banking.models import BankAccount
from apps.transactions.models import Transaction
from apps.accounts.models import CustomUser
from apps.otp.models import OTP
from django.shortcuts import get_object_or_404
from django.contrib import messages
from apps.dashboard.models import AuditLog, SystemSettings

@login_required
@role_required('CUSTOMER')
def customer_dashboard_view(request):
    accounts = BankAccount.objects.filter(user=request.user)
    recent_transactions = Transaction.objects.filter(
        Q(from_account__in=accounts) | Q(to_account__in=accounts)
    ).order_by('-timestamp')[:5]
    
    return render(request, 'dashboard/customer.html', {
        'accounts': accounts,
        'recent_transactions': recent_transactions
    })

@login_required
@role_required('TELLER')
def teller_dashboard_view(request):
    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:20]
    return render(request, 'dashboard/teller_overview.html', {
        'recent_transactions': recent_transactions,
    })

@login_required
@role_required('TELLER')
def teller_accounts_view(request):
    all_accounts = BankAccount.objects.select_related('user').all()
    return render(request, 'dashboard/teller_accounts.html', {
        'all_accounts': all_accounts
    })

@login_required
@role_required('ADMIN')
def admin_dashboard_view(request):
    total_accounts = BankAccount.objects.count()
    total_transactions = Transaction.objects.count()
    total_users = CustomUser.objects.count()
    total_capital = BankAccount.objects.aggregate(total=Sum('balance'))['total'] or 0

    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:10]
    pending_transactions = Transaction.objects.filter(status='PENDING_APPROVAL').order_by('-timestamp')
    
    return render(request, 'dashboard/admin_overview.html', {
        'total_accounts': total_accounts,
        'total_transactions': total_transactions,
        'total_users': total_users,
        'total_capital': total_capital,
        'recent_transactions': recent_transactions,
        'pending_transactions': pending_transactions,
    })

@login_required
@role_required('ADMIN')
def admin_roles_view(request):
    all_users = CustomUser.objects.all().order_by('-created_at')
    return render(request, 'dashboard/admin_roles.html', {'all_users': all_users})

@login_required
@role_required('ADMIN')
def admin_accounts_view(request):
    all_accounts = BankAccount.objects.select_related('user').all()
    return render(request, 'dashboard/admin_accounts.html', {'all_accounts': all_accounts})

@login_required
@role_required('ADMIN')
def admin_security_view(request):
    sys_settings = SystemSettings.get_settings()
    audit_logs = AuditLog.objects.select_related('admin_user').all().order_by('-timestamp')[:50]
    otp_logs = OTP.objects.select_related('user').all().order_by('-created_at')[:50]
    flagged_transactions = Transaction.objects.filter(is_flagged=True).order_by('-timestamp')
    
    return render(request, 'dashboard/admin_security.html', {
        'sys_settings': sys_settings,
        'audit_logs': audit_logs,
        'otp_logs': otp_logs,
        'flagged_transactions': flagged_transactions,
    })

@login_required
@role_required('ADMIN')
def toggle_freeze_account_view(request, account_id):
    if request.method == "POST":
        account = get_object_or_404(BankAccount, id=account_id)
        account.is_frozen = not account.is_frozen
        account.save(update_fields=['is_frozen'])
        status = "frozen" if account.is_frozen else "unfrozen"
        
        # AUDIT LOGGING
        AuditLog.objects.create(
            admin_user=request.user,
            action='FREEZE_ACCOUNT' if account.is_frozen else 'UNFREEZE_ACCOUNT',
            target_account=account,
            details=f"Admin {request.user.email} marked account {account.account_number} as {status}."
        )
        
        messages.success(request, f"Account {account.account_number} is now {status}.")
    return redirect("dashboard:admin")

@login_required
@role_required('ADMIN')
def change_user_role_view(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(CustomUser, id=user_id)
        new_role = request.POST.get("role")
        if new_role in [role[0] for role in CustomUser.ROLE_CHOICES]:
            old_role = user.role
            user.role = new_role
            user.save(update_fields=['role'])
            
            # AUDIT LOGGING
            AuditLog.objects.create(
                admin_user=request.user,
                action='ROLE_CHANGE',
                target_user=user,
                details=f"Role changed from {old_role} to {new_role}."
            )
            
            messages.success(request, f"User {user.email} role updated to {new_role}.")
        else:
            messages.error(request, "Invalid role selection.")
    return redirect("dashboard:admin")

@login_required
@role_required('ADMIN')
def approve_transfer_view(request, transaction_id):
    if request.method == "POST":
        tx = get_object_or_404(Transaction, id=transaction_id)
        if tx.status != 'PENDING_APPROVAL':
            messages.error(request, "This transaction is not pending approval.")
            return redirect("dashboard:admin")
            
        action = request.POST.get("action")
        
        if action == 'approve':
            from django.db import transaction
            
            with transaction.atomic():
                from_acc = BankAccount.objects.select_for_update().get(pk=tx.from_account.pk)
                to_acc = BankAccount.objects.select_for_update().get(pk=tx.to_account.pk)
                
                if from_acc.balance < tx.amount:
                    tx.status = 'FAILED'
                    tx.flag_reason = "Insufficient funds at time of manual approval."
                    tx.save()
                    messages.error(request, "Sender no longer has sufficient bounds.")
                else:
                    from_acc.balance -= tx.amount
                    from_acc.save(update_fields=['balance'])
                    to_acc.balance += tx.amount
                    to_acc.save(update_fields=['balance'])
                    
                    tx.status = 'SUCCESS'
                    tx.save()
                    messages.success(request, f"Transfer of ₹{tx.amount} approved successfully.")
                    
                    # AUDIT LOGGING
                    AuditLog.objects.create(
                        admin_user=request.user,
                        action='APPROVE_TRANSFER',
                        target_transaction=tx,
                        details=f"Manually Approved transaction ID {tx.id}."
                    )
                    
        elif action == 'reject':
            tx.status = 'FAILED'
            tx.flag_reason = "Explicitly Rejected by Administrator."
            tx.save()
            messages.success(request, "Transfer successfully rejected.")
            
            # AUDIT LOGGING
            AuditLog.objects.create(
                admin_user=request.user,
                action='REJECT_TRANSFER',
                target_transaction=tx,
                details=f"Manually Rejected transaction ID {tx.id}."
            )
            
    return redirect("dashboard:admin")

@login_required
@role_required('ADMIN')
def update_settings_view(request):
    if request.method == "POST":
        min_balance = request.POST.get('minimum_balance')
        max_transfer = request.POST.get('max_transfer_limit')
        daily_with = request.POST.get('daily_withdrawal_limit')
        
        sys_settings = SystemSettings.get_settings()
        sys_settings.minimum_balance = min_balance
        sys_settings.max_transfer_limit = max_transfer
        sys_settings.daily_withdrawal_limit = daily_with
        sys_settings.updated_by = request.user
        sys_settings.save()
        
        # AUDIT LOGGING
        AuditLog.objects.create(
            admin_user=request.user,
            action='UPDATE_SETTINGS',
            details=f"Updated Global Settings: MinBal=₹{min_balance}, MaxTx=₹{max_transfer}, DailyWith=₹{daily_with}"
        )
        
        messages.success(request, "System Rules configured successfully.")
    return redirect("dashboard:admin")
