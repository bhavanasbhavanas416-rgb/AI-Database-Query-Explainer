from django.db import models
from django.contrib.auth.models import User

class AnalyticsReport(models.Model):
    CHART_CHOICES = (
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('line', 'Line Graph'),
        ('area', 'Area Chart'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_reports')
    title = models.CharField(max_length=200)
    chart_type = models.CharField(max_length=20, choices=CHART_CHOICES, default='bar')
    sql_query = models.TextField()
    chart_config = models.JSONField(default=dict)
    insights = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.chart_type})"
