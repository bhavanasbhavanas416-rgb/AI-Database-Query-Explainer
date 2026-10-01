import os
import secrets
import uuid
from pathlib import Path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from authentication.models import UserProfile
from .models import DatabaseConnection
from .services.schema_inspector import extract_database_schema, get_connection_cursor

def get_current_user_profile(request):
    user = request.user if (request.user and request.user.is_authenticated) else User.objects.first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return user, profile


def get_active_connection(request):
    _, profile = get_current_user_profile(request)
    if profile.active_connection:
        return profile.active_connection
    
    # Ensure default 100k+ sample DB connection exists in DB
    default_conn, _ = DatabaseConnection.objects.get_or_create(
        is_default_sample=True,
        defaults={
            'name': 'Enterprise Sample DB (100,000+ Records)',
            'engine': 'sqlite',
            'db_name': 'enterprise_sample_100k.db',
            'sqlite_file_path': os.path.join(settings.BASE_DIR, 'data', 'enterprise_sample_100k.db'),
            'is_active': True
        }
    )
    profile.active_connection = default_conn
    profile.save()
    return default_conn

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def connection_list_create_api(request):
    user, profile = get_current_user_profile(request)

    if request.method == 'POST':
        name = request.data.get('name')
        engine = request.data.get('engine', 'sqlite')
        host = request.data.get('host', 'localhost')
        port = request.data.get('port')
        db_name = request.data.get('db_name')
        username = request.data.get('username')
        password = request.data.get('password')

        if not name or not db_name:
            return Response({'error': 'Name and Database Name are required.'}, status=status.HTTP_400_BAD_REQUEST)

        sqlite_file_path = None
        if engine == 'sqlite' and 'sqlite_file' in request.FILES:
            uploaded_file = request.FILES['sqlite_file']
            extension = Path(uploaded_file.name).suffix.lower()
            if extension not in {'.db', '.sqlite', '.sqlite3'}:
                return Response({'error': 'Upload a .db, .sqlite, or .sqlite3 database file.'}, status=status.HTTP_400_BAD_REQUEST)
            if uploaded_file.size > 100 * 1024 * 1024:
                return Response({'error': 'SQLite database files must be 100 MB or smaller.'}, status=status.HTTP_400_BAD_REQUEST)
            uploaded_file.open()
            header = uploaded_file.read(16)
            uploaded_file.seek(0)
            if header != b'SQLite format 3\x00':
                return Response({'error': 'The uploaded file is not a valid SQLite database.'}, status=status.HTTP_400_BAD_REQUEST)

            save_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_dbs')
            os.makedirs(save_dir, exist_ok=True)
            sqlite_file_path = os.path.join(save_dir, f'{uuid.uuid4().hex}{extension}')
            with open(sqlite_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

        conn_obj = DatabaseConnection.objects.create(
            user=user,
            name=name,
            engine=engine,
            host=host,
            port=port if port else (5432 if engine == 'postgresql' else 3306),
            db_name=db_name,
            username=username,
            password=password,
            sqlite_file_path=sqlite_file_path
        )

        profile.active_connection = conn_obj
        profile.save()

        return Response({'message': 'Database connection created successfully!', 'id': conn_obj.id}, status=status.HTTP_201_CREATED)

    # List all connections
    get_active_connection(request)
    connections = DatabaseConnection.objects.filter(
        Q(user=user) | Q(is_default_sample=True)
    ).order_by('-created_at')
    
    results = []
    for c in connections:
        results.append({
            'id': c.id,
            'name': c.name,
            'engine': c.engine,
            'host': c.host,
            'port': c.port,
            'db_name': c.db_name,
            'is_default_sample': c.is_default_sample,
            'is_active': (profile.active_connection and profile.active_connection.id == c.id)
        })

    return Response({'connections': results})


@api_view(['POST'])
@permission_classes([AllowAny])
def connection_set_active_api(request, pk):
    user, profile = get_current_user_profile(request)
    try:
        conn_obj = DatabaseConnection.objects.get(
            Q(user=user) | Q(is_default_sample=True), pk=pk
        )
        profile.active_connection = conn_obj
        profile.save()
        return Response({'message': f"Active connection set to '{conn_obj.name}'."})
    except DatabaseConnection.DoesNotExist:
        return Response({'error': 'Connection not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def connection_test_api(request):
    user, _ = get_current_user_profile(request)
    conn_id = request.data.get('id')
    if conn_id:
        try:
            conn_obj = DatabaseConnection.objects.get(
                Q(user=user) | Q(is_default_sample=True), pk=conn_id
            )
        except DatabaseConnection.DoesNotExist:
            return Response({'error': 'Connection not found.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        conn_obj = get_active_connection(request)

    try:
        conn, cursor, engine = get_connection_cursor(conn_obj)
        conn.close()
        return Response({
            'status': 'success',
            'message': f"Successfully connected to {conn_obj.name} ({engine.upper()})!"
        })
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def schema_explorer_api(request):
    conn_obj = get_active_connection(request)
    search_query = request.GET.get('q', '').lower()

    try:
        schema = extract_database_schema(conn_obj)
        
        if search_query:
            filtered_tables = []
            for tbl in schema['tables']:
                if search_query in tbl['table_name'].lower() or any(search_query in c['name'].lower() for c in tbl['columns']):
                    filtered_tables.append(tbl)
            schema['tables'] = filtered_tables

        schema['connection_info'] = {
            'id': conn_obj.id,
            'name': conn_obj.name,
            'engine': conn_obj.engine,
            'db_name': conn_obj.db_name
        }

        return Response(schema)
    except Exception as e:
        return Response({'error': f"Failed to inspect database schema: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
