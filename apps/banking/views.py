from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.core.utils import generate_account_number
from apps.core.decorators import role_required
from .models import BankAccount

@login_required
@role_required('CUSTOMER', 'TELLER', 'ADMIN')
def create_account_view(request):
    if request.method == 'POST':
        account_type = request.POST.get('account_type')
        if account_type not in ['SAVINGS', 'CURRENT']:
            messages.error(request, 'Invalid account type selected.')
            return redirect('banking:create-account')
            
        # Ensure account number is unique
        account_number = generate_account_number()
        while BankAccount.objects.filter(account_number=account_number).exists():
            account_number = generate_account_number()
            
        account = BankAccount.objects.create(
            user=request.user,
            account_number=account_number,
            account_type=account_type
        )
        messages.success(request, f'Account {account_number} created successfully!')
        return redirect('banking:account-list')

    return render(request, 'banking/create_account.html')

@login_required
@role_required('CUSTOMER', 'TELLER', 'ADMIN')
def account_list_view(request):
    accounts = BankAccount.objects.filter(user=request.user)
    return render(request, 'banking/account_list.html', {'accounts': accounts})

@login_required
@role_required('CUSTOMER', 'TELLER', 'ADMIN')
def account_detail_view(request, pk):
    account = get_object_or_404(BankAccount, pk=pk, user=request.user)
    return render(request, 'banking/account_detail.html', {'account': account})
