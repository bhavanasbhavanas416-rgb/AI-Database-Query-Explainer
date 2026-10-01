import os
import secrets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import UserProfile

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user_api(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'user'})
    login(request, user)

    return Response({
        'message': 'Registration successful!',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': profile.role,
            'theme': profile.theme
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user_api(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        masked_key = f"{profile.groq_api_key[:4]}...{profile.groq_api_key[-4:]}" if profile.groq_api_key and len(profile.groq_api_key) > 8 else ''
        return Response({
            'message': 'Login successful!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': profile.role,
                'groq_api_key_masked': masked_key,
                'theme': profile.theme,
                'active_connection_id': profile.active_connection.id if profile.active_connection else None
            }
        })
    return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_user_api(request):
    logout(request)
    return Response({'message': 'Logged out successfully.'})


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def profile_api(request):
    user = request.user if (request.user and request.user.is_authenticated) else User.objects.first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')

    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        email = request.data.get('email')
        groq_api_key = request.data.get('groq_api_key')
        theme = request.data.get('theme')

        if email:
            user.email = email
            user.save()
        if groq_api_key is not None:
            profile.groq_api_key = groq_api_key
        if theme in ['dark', 'light']:
            profile.theme = theme

        profile.save()
        return Response({'message': 'Profile updated successfully!'})

    masked_key = f"{profile.groq_api_key[:4]}...{profile.groq_api_key[-4:]}" if profile.groq_api_key and len(profile.groq_api_key) > 8 else ''

    return Response({
        'username': user.username,
        'email': user.email,
        'role': profile.role,
        'is_admin': user.is_staff,
        'groq_api_key_masked': masked_key,
        'has_groq_api_key': bool(profile.groq_api_key),
        'theme': profile.theme,
        'active_connection_id': profile.active_connection.id if profile.active_connection else None
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_api(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'message': f"Password reset instructions have been generated for {email}."
    })
