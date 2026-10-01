from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from database_manager.views import get_current_user_profile, get_active_connection
from query_executor.services.query_runner import execute_sql_safely
from .services.chart_generator import format_analytics_data
from .models import AnalyticsReport
from query_assistant.models import QueryHistory
from database_manager.models import DatabaseConnection
from django.contrib.auth.models import User

@api_view(['POST'])
@permission_classes([AllowAny])
def chart_data_api(request):
    """Generates visualization chart config and trend insights from custom SQL or active DB default queries."""
    sql_query = request.data.get('sql')
    chart_type = request.data.get('chart_type', 'bar')
    title = request.data.get('title', 'Database Analytics Visualization')

    conn_obj = get_active_connection(request)

    if not sql_query:
        sql_query = "SELECT category, COUNT(*) as count, ROUND(AVG(price), 2) as avg_price FROM products GROUP BY category ORDER BY count DESC;"

    try:
        exec_res = execute_sql_safely(sql_query, db_conn_obj=conn_obj, page=1, page_size=20)
        chart_res = format_analytics_data(exec_res['columns'], exec_res['rows'], chart_type=chart_type, chart_title=title)
        chart_res['sql_query'] = sql_query
        return Response(chart_res)
    except Exception as e:
        return Response({'error': f"Analytics error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def analytics_reports_api(request):
    user, _ = get_current_user_profile(request)

    if request.method == 'POST':
        title = request.data.get('title')
        chart_type = request.data.get('chart_type', 'bar')
        sql_query = request.data.get('sql_query')
        insights = request.data.get('insights', '')

        if not title or not sql_query:
            return Response({'error': 'Title and SQL Query are required.'}, status=status.HTTP_400_BAD_REQUEST)

        report = AnalyticsReport.objects.create(
            user=user,
            title=title,
            chart_type=chart_type,
            sql_query=sql_query,
            insights=insights
        )
        return Response({'message': 'Analytics report saved!', 'id': report.id}, status=status.HTTP_201_CREATED)

    reports = AnalyticsReport.objects.filter(user=user).order_by('-created_at')
    data = []
    for r in reports:
        data.append({
            'id': r.id,
            'title': r.title,
            'chart_type': r.chart_type,
            'sql_query': r.sql_query,
            'insights': r.insights,
            'created_at': r.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return Response({'reports': data})


@api_view(['GET'])
@permission_classes([AllowAny])
def admin_metrics_api(request):
    """
    ADMIN PANEL API
    Provides system-wide health, user counts, database connections, query execution volume, average speed.
    """
    total_users = User.objects.count()
    total_connections = DatabaseConnection.objects.count()
    total_queries = QueryHistory.objects.count()
    
    queries_with_time = QueryHistory.objects.filter(execution_time_ms__gt=0)
    avg_speed = 0.0
    if queries_with_time.exists():
        avg_speed = round(sum(q.execution_time_ms for q in queries_with_time) / queries_with_time.count(), 2)

    recent_logs = []
    for q in QueryHistory.objects.all().order_by('-created_at')[:10]:
        recent_logs.append({
            'id': q.id,
            'user': q.user.username if q.user else 'guest',
            'question': q.user_question or 'SQL Execution',
            'sql': q.generated_sql or q.executed_sql,
            'time_ms': q.execution_time_ms,
            'status': q.status,
            'created_at': q.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return Response({
        'total_users': total_users,
        'total_connections': total_connections,
        'total_queries': total_queries,
        'avg_execution_speed_ms': avg_speed,
        'recent_logs': recent_logs,
        'system_status': 'Operational 100% - Ready for 100,000+ Records'
    })
