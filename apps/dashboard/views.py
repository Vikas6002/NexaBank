from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from apps.core.decorators import role_required
from apps.banking.models import BankAccount
from apps.transactions.models import Transaction
from apps.accounts.models import CustomUser
from django.shortcuts import get_object_or_404
from django.contrib import messages

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
    # Tellers can see all accounts and recent history or assist with transactions
    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:10]
    return render(request, 'dashboard/teller.html', {
        'recent_transactions': recent_transactions
    })

@login_required
@role_required('ADMIN')
def admin_dashboard_view(request):
    # Admins have full view of system metrics
    total_accounts = BankAccount.objects.count()
    total_transactions = Transaction.objects.count()
    total_users = CustomUser.objects.count()
    total_capital = BankAccount.objects.aggregate(total=Sum('balance'))['total'] or 0

    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:10]
    pending_transactions = Transaction.objects.filter(status='PENDING_APPROVAL').order_by('-timestamp')
    flagged_transactions = Transaction.objects.filter(is_flagged=True).order_by('-timestamp')
    
    all_users = CustomUser.objects.all().order_by('-created_at')
    all_accounts = BankAccount.objects.select_related('user').all()
    
    return render(request, 'dashboard/admin.html', {
        'total_accounts': total_accounts,
        'total_transactions': total_transactions,
        'total_users': total_users,
        'total_capital': total_capital,
        'recent_transactions': recent_transactions,
        'pending_transactions': pending_transactions,
        'flagged_transactions': flagged_transactions,
        'all_users': all_users,
        'all_accounts': all_accounts
    })

@login_required
@role_required('ADMIN')
def toggle_freeze_account_view(request, account_id):
    if request.method == "POST":
        account = get_object_or_404(BankAccount, id=account_id)
        account.is_frozen = not account.is_frozen
        account.save(update_fields=['is_frozen'])
        status = "frozen" if account.is_frozen else "unfrozen"
        messages.success(request, f"Account {account.account_number} is now {status}.")
    return redirect("dashboard:admin")

@login_required
@role_required('ADMIN')
def change_user_role_view(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(CustomUser, id=user_id)
        new_role = request.POST.get("role")
        if new_role in [role[0] for role in CustomUser.ROLE_CHOICES]:
            user.role = new_role
            user.save(update_fields=['role'])
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
                    
        elif action == 'reject':
            tx.status = 'FAILED'
            tx.flag_reason = "Explicitly Rejected by Administrator."
            tx.save()
            messages.success(request, "Transfer successfully rejected.")
            
    return redirect("dashboard:admin")
