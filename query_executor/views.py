from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from database_manager.views import get_current_user_profile, get_active_connection
from query_assistant.models import QueryHistory
from .services.query_runner import execute_sql_safely, export_query_results_csv, export_query_results_excel

@api_view(['POST'])
@permission_classes([AllowAny])
def execute_sql_api(request):
    """Executes a SQL query safely and records history."""
    sql_query = request.data.get('sql')
    page = int(request.data.get('page', 1))
    page_size = int(request.data.get('page_size', 50))
    history_id = request.data.get('history_id')

    if not sql_query:
        return Response({'error': 'SQL query is required.'}, status=status.HTTP_400_BAD_REQUEST)

    user, _ = get_current_user_profile(request)
    conn_obj = get_active_connection(request)

    try:
        res = execute_sql_safely(sql_query, db_conn_obj=conn_obj, page=page, page_size=page_size)

        if history_id:
            try:
                hist = QueryHistory.objects.get(pk=history_id, user=user)
                hist.executed_sql = sql_query
                hist.execution_time_ms = res['execution_time_ms']
                hist.row_count = res['total_rows']
                hist.status = 'success'
                hist.save()
            except QueryHistory.DoesNotExist:
                pass
        else:
            QueryHistory.objects.create(
                user=user,
                connection=conn_obj,
                user_question="Direct SQL Execution",
                generated_sql=sql_query,
                executed_sql=sql_query,
                execution_time_ms=res['execution_time_ms'],
                row_count=res['total_rows'],
                status='success'
            )

        return Response(res)

    except PermissionError as pe:
        return Response({'error': str(pe)}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def export_csv_api(request):
    """Downloads query execution result as CSV."""
    sql_query = request.data.get('sql')
    if not sql_query:
        return Response({'error': 'SQL query is required.'}, status=status.HTTP_400_BAD_REQUEST)

    conn_obj = get_active_connection(request)
    try:
        res = execute_sql_safely(sql_query, db_conn_obj=conn_obj, page=1, page_size=100000)
        csv_bytes = export_query_results_csv(res['columns'], res['rows'])

        response = HttpResponse(csv_bytes, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="query_results.csv"'
        return response
    except Exception as e:
        return Response({'error': f"Export failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def export_excel_api(request):
    """Downloads query execution result as Excel (.xlsx)."""
    sql_query = request.data.get('sql')
    if not sql_query:
        return Response({'error': 'SQL query is required.'}, status=status.HTTP_400_BAD_REQUEST)

    conn_obj = get_active_connection(request)
    try:
        res = execute_sql_safely(sql_query, db_conn_obj=conn_obj, page=1, page_size=100000)
        excel_bytes = export_query_results_excel(res['columns'], res['rows'])

        response = HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="query_results.xlsx"'
        return response
    except Exception as e:
        return Response({'error': f"Export failed: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
