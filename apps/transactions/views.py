from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.core.decorators import role_required
from apps.banking.models import BankAccount
from .models import Transaction
from .services import perform_deposit, perform_withdraw, perform_transfer

@login_required
@role_required('TELLER', 'ADMIN')
def deposit_view(request):
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        amount = request.POST.get('amount')
        
        try:
            account = BankAccount.objects.get(pk=account_id)
            success, msg = perform_deposit(account, amount)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
        except BankAccount.DoesNotExist:
            messages.error(request, "Account not found or not authorized.")
            
        return redirect('transactions:deposit')

    # Teller / Admin can deposit into any user's account
    accounts = BankAccount.objects.select_related('user').all()
    return render(request, 'transactions/deposit.html', {'accounts': accounts})

@login_required
@role_required('CUSTOMER', 'TELLER', 'ADMIN')
def withdraw_view(request):
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        amount = request.POST.get('amount')
        
        try:
            if request.user.role in ['ADMIN', 'TELLER']:
                account = BankAccount.objects.get(pk=account_id)
            else:
                account = BankAccount.objects.get(pk=account_id, user=request.user)
                
            success, msg = perform_withdraw(account, amount)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
        except BankAccount.DoesNotExist:
            messages.error(request, "Account not found or not authorized.")
            
        return redirect('transactions:withdraw')

    if request.user.role in ['ADMIN', 'TELLER']:
        accounts = BankAccount.objects.select_related('user').all()
    else:
        accounts = BankAccount.objects.filter(user=request.user)
        
    return render(request, 'transactions/withdraw.html', {'accounts': accounts})

@login_required
@role_required('CUSTOMER', 'TELLER', 'ADMIN')
def transfer_view(request):
    if request.method == 'POST':
        from_account_id = request.POST.get('from_account_id')
        to_account_number = request.POST.get('to_account_number')
        amount = request.POST.get('amount')
        
        try:
            if request.user.role in ['ADMIN', 'TELLER']:
                from_account = BankAccount.objects.get(pk=from_account_id)
            else:
                from_account = BankAccount.objects.get(pk=from_account_id, user=request.user)
                
            to_account = BankAccount.objects.get(account_number=to_account_number)
            
            success, msg = perform_transfer(from_account, to_account, amount)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)
        except BankAccount.DoesNotExist:
            messages.error(request, "Invalid source or destination account.")
            
        return redirect('transactions:transfer')

    if request.user.role in ['ADMIN', 'TELLER']:
        accounts = BankAccount.objects.select_related('user').all()
    else:
        accounts = BankAccount.objects.filter(user=request.user)
        
    return render(request, 'transactions/transfer.html', {'accounts': accounts})

@login_required
@role_required('CUSTOMER', 'TELLER', 'ADMIN')
def transaction_history_view(request):
    # Fetch all transactions where the user's accounts are either the source or destination
    accounts = BankAccount.objects.filter(user=request.user)
    transactions = Transaction.objects.filter(Q(from_account__in=accounts) | Q(to_account__in=accounts)).order_by('-timestamp')
    
    return render(request, 'transactions/history.html', {'transactions': transactions})
