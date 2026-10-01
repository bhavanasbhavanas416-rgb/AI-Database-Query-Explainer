from django.db import models
from django.contrib.auth.models import User
from database_manager.models import DatabaseConnection

class QueryHistory(models.Model):
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('error', 'Error'),
        ('explained_only', 'Explained Only'),
        ('generated_only', 'Generated Only'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='query_histories')
    connection = models.ForeignKey(DatabaseConnection, on_delete=models.SET_NULL, null=True, blank=True)
    user_question = models.TextField(blank=True, null=True)
    generated_sql = models.TextField(blank=True, null=True)
    executed_sql = models.TextField(blank=True, null=True)
    execution_time_ms = models.FloatField(default=0.0)
    row_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        q = self.user_question or self.generated_sql or "Query"
        return f"History #{self.id} - {q[:40]}"

class QueryExplanation(models.Model):
    query_history = models.OneToOneField(QueryHistory, on_delete=models.CASCADE, related_name='explanation')
    purpose = models.TextField()
    tables_used = models.JSONField(default=list)
    sql_operations = models.JSONField(default=list)
    line_by_line = models.JSONField(default=list)
    clause_breakdown = models.JSONField(default=dict)
    technical_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class OptimizationReport(models.Model):
    query_history = models.OneToOneField(QueryHistory, on_delete=models.CASCADE, related_name='optimization')
    performance_score = models.IntegerField(default=100)  # 0 to 100
    optimization_suggestions = models.JSONField(default=list)
    index_recommendations = models.JSONField(default=list)
    query_complexity = models.CharField(max_length=50, default='Low')
    cost_reduction_tips = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
