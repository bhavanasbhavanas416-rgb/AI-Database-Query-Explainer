from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from dashboard.views import dashboard_home
from authentication.views import (
    register_user_api, login_user_api, logout_user_api, profile_api, forgot_password_api
)
from database_manager.views import (
    connection_list_create_api, connection_set_active_api, connection_test_api, schema_explorer_api
)
from query_assistant.views import (
    generate_sql_api, explain_sql_api, optimize_sql_api, query_history_list_api, query_history_clear_api
)
from query_executor.views import (
    execute_sql_api, export_csv_api, export_excel_api
)
from analytics.views import (
    chart_data_api, analytics_reports_api, admin_metrics_api
)

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Dashboard Main View
    path('', dashboard_home, name='dashboard_home'),

    # Authentication API
    path('api/v1/auth/register/', register_user_api, name='api_register'),
    path('api/v1/auth/login/', login_user_api, name='api_login'),
    path('api/v1/auth/logout/', logout_user_api, name='api_logout'),
    path('api/v1/auth/profile/', profile_api, name='api_profile'),
    path('api/v1/auth/forgot-password/', forgot_password_api, name='api_forgot_password'),

    # Database Connection & Schema API
    path('api/v1/connections/', connection_list_create_api, name='api_connections'),
    path('api/v1/connections/<int:pk>/set-active/', connection_set_active_api, name='api_connection_set_active'),
    path('api/v1/connections/test/', connection_test_api, name='api_connection_test'),
    path('api/v1/schema/', schema_explorer_api, name='api_schema'),

    # AI Query Assistant API
    path('api/v1/query/generate/', generate_sql_api, name='api_generate_sql'),
    path('api/v1/query/explain/', explain_sql_api, name='api_explain_sql'),
    path('api/v1/query/optimize/', optimize_sql_api, name='api_optimize_sql'),
    path('api/v1/query/history/', query_history_list_api, name='api_query_history'),
    path('api/v1/query/history/clear/', query_history_clear_api, name='api_query_history_clear'),

    # Query Execution & Export API
    path('api/v1/query/execute/', execute_sql_api, name='api_execute_sql'),
    path('api/v1/export/csv/', export_csv_api, name='api_export_csv'),
    path('api/v1/export/excel/', export_excel_api, name='api_export_excel'),

    # Analytics API
    path('api/v1/analytics/chart/', chart_data_api, name='api_chart_data'),
    path('api/v1/analytics/reports/', analytics_reports_api, name='api_analytics_reports'),
    path('api/v1/admin/metrics/', admin_metrics_api, name='api_admin_metrics'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
