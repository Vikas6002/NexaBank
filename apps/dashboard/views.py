from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from apps.core.decorators import role_required
from apps.banking.models import BankAccount
from apps.transactions.models import Transaction

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
    recent_transactions = Transaction.objects.all().order_by('-timestamp')[:10]
    
    return render(request, 'dashboard/admin.html', {
        'total_accounts': total_accounts,
        'total_transactions': total_transactions,
        'recent_transactions': recent_transactions
    })
