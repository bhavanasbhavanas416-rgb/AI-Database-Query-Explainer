from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    THEME_CHOICES = (
        ('dark', 'Dark Mode'),
        ('light', 'Light Mode'),
    )
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('user', 'Standard User'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    groq_api_key = models.CharField(max_length=255, blank=True, null=True, default='')
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='dark')
    active_connection = models.ForeignKey(
        'database_manager.DatabaseConnection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_users'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"
