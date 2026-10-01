from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from authentication.models import UserProfile
from database_manager.views import get_current_user_profile, get_active_connection
from .models import QueryHistory, QueryExplanation, OptimizationReport
from .services.groq_service import generate_sql_from_nl
from .services.sql_explainer import explain_sql_query
from .services.sql_optimizer import analyze_and_optimize_sql
from database_manager.services.schema_inspector import extract_database_schema

@api_view(['POST'])
@permission_classes([AllowAny])
def generate_sql_api(request):
    """
    Accepts natural language prompt, sends to Groq API (or schema-aware rule engine),
    returns generated SQL, line-by-line explanation, and performance optimization report.
    """
    user_prompt = request.data.get('prompt')
    if not user_prompt:
        return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)

    user, profile = get_current_user_profile(request)
    conn_obj = get_active_connection(request)

    try:
        result = generate_sql_from_nl(user_prompt, user_profile=profile, db_connection=conn_obj)
        
        history = QueryHistory.objects.create(
            user=user,
            connection=conn_obj,
            user_question=user_prompt,
            generated_sql=result['generated_sql'],
            status='generated_only'
        )

        exp = result['explanation']
        QueryExplanation.objects.create(
            query_history=history,
            purpose=exp['purpose'],
            tables_used=exp['tables_used'],
            sql_operations=exp['sql_operations'],
            line_by_line=exp['line_by_line'],
            clause_breakdown=exp['clause_breakdown'],
            technical_description=exp['technical_description']
        )

        opt = result['optimization']
        OptimizationReport.objects.create(
            query_history=history,
            performance_score=opt['performance_score'],
            optimization_suggestions=opt['optimization_suggestions'],
            index_recommendations=opt['index_recommendations'],
            query_complexity=opt['query_complexity'],
            cost_reduction_tips=opt['cost_reduction_tips']
        )

        result['history_id'] = history.id
        return Response(result)

    except Exception as e:
        return Response({'error': f"Generation error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def explain_sql_api(request):
    """Explains a manually pasted SQL query."""
    sql_query = request.data.get('sql')
    if not sql_query:
        return Response({'error': 'SQL query is required.'}, status=status.HTTP_400_BAD_REQUEST)

    user, _ = get_current_user_profile(request)
    conn_obj = get_active_connection(request)

    try:
        schema_data = extract_database_schema(conn_obj)
        explanation = explain_sql_query(sql_query, schema_data)

        history = QueryHistory.objects.create(
            user=user,
            connection=conn_obj,
            user_question="Paste & Explain SQL",
            generated_sql=sql_query,
            status='explained_only'
        )

        QueryExplanation.objects.create(
            query_history=history,
            purpose=explanation['purpose'],
            tables_used=explanation['tables_used'],
            sql_operations=explanation['sql_operations'],
            line_by_line=explanation['line_by_line'],
            clause_breakdown=explanation['clause_breakdown'],
            technical_description=explanation['technical_description']
        )

        explanation['history_id'] = history.id
        return Response(explanation)

    except Exception as e:
        return Response({'error': f"Explanation error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def optimize_sql_api(request):
    """Analyzes performance and generates index recommendations for a pasted SQL query."""
    sql_query = request.data.get('sql')
    if not sql_query:
        return Response({'error': 'SQL query is required.'}, status=status.HTTP_400_BAD_REQUEST)

    conn_obj = get_active_connection(request)

    try:
        schema_data = extract_database_schema(conn_obj)
        optimization = analyze_and_optimize_sql(sql_query, schema_data)
        return Response(optimization)
    except Exception as e:
        return Response({'error': f"Optimization error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def query_history_list_api(request):
    """Lists query history records with pagination and search."""
    user, _ = get_current_user_profile(request)
    histories = QueryHistory.objects.filter(user=user).select_related('connection', 'explanation', 'optimization').order_by('-created_at')[:100]

    items = []
    for h in histories:
        exp = getattr(h, 'explanation', None)
        opt = getattr(h, 'optimization', None)

        items.append({
            'id': h.id,
            'user_question': h.user_question,
            'generated_sql': h.generated_sql,
            'executed_sql': h.executed_sql,
            'execution_time_ms': h.execution_time_ms,
            'row_count': h.row_count,
            'status': h.status,
            'connection_name': h.connection.name if h.connection else 'Default DB',
            'created_at': h.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'performance_score': opt.performance_score if opt else None,
            'purpose': exp.purpose if exp else None
        })

    return Response({'history': items})


@api_view(['DELETE', 'POST'])
@permission_classes([AllowAny])
def query_history_clear_api(request):
    user, _ = get_current_user_profile(request)
    QueryHistory.objects.filter(user=user).delete()
    return Response({'message': 'Query history cleared successfully.'})
