from django.db import models
from django.conf import settings
from apps.banking.models import BankAccount
from apps.transactions.models import Transaction

class SystemSettings(models.Model):
    # Ensures a Singleton pattern
    id = models.AutoField(primary_key=True)
    minimum_balance = models.DecimalField(max_digits=12, decimal_places=2, default=500.00)
    max_transfer_limit = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    daily_withdrawal_limit = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return "Global Banking Rules Engine"

class AuditLog(models.Model):
    ACTION_TYPES = (
        ('FREEZE_ACCOUNT', 'Freeze Account'),
        ('UNFREEZE_ACCOUNT', 'Unfreeze Account'),
        ('ROLE_CHANGE', 'Role Change'),
        ('APPROVE_TRANSFER', 'Approve Transfer'),
        ('REJECT_TRANSFER', 'Reject Transfer'),
        ('UPDATE_SETTINGS', 'Update Global Settings'),
        ('MANAGE_OTP', 'Manage OTP Access')
    )
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audit_actions")
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_targeted")
    target_account = models.ForeignKey(BankAccount, null=True, blank=True, on_delete=models.SET_NULL)
    target_transaction = models.ForeignKey(Transaction, null=True, blank=True, on_delete=models.SET_NULL)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.admin_user.email} - {self.action} at {self.timestamp}"
