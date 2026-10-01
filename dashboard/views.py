from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def dashboard_home(request):
    """Renders the main enterprise single-page application dashboard."""
    return render(request, 'dashboard/index.html')
