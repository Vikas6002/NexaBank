from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from apps.core.decorators import role_required
from apps.banking.models import BankAccount
from apps.transactions.models import Transaction
from .pdf_generator import generate_account_statement_pdf

@login_required
@role_required('CUSTOMER', 'TELLER', 'ADMIN')
def download_statement_view(request, account_id):
    account = get_object_or_404(BankAccount, pk=account_id, user=request.user)
    transactions = Transaction.objects.filter(
        Q(from_account=account) | Q(to_account=account)
    ).order_by('-timestamp')
    
    pdf_buffer = generate_account_statement_pdf(account, transactions)
    
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="statement_{account.account_number}.pdf"'
    
    return response
