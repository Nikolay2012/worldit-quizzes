from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
import json
from .models import *
from django.urls import reverse

# Create your views here.

@require_http_methods(["GET", "POST"])
def render_login(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username = username, password = password)
        if user is not None:
            login(request, user)

            redirect_url = "/"

            account_types = user.account_types
            
            is_student = "student" in account_types
            is_mentor = "mentor" in account_types
            is_admin = "admin" in account_types

            if is_student and not is_mentor and not is_admin:
                redirect_url = reverse("student_join_page")

            return JsonResponse({'error': False, 'redirect_url': redirect_url})

        return JsonResponse({'error': 'Invalid login data'}, status = 401)

    return render(request, "users/login.html")

@require_GET
def logout_user(request: HttpRequest):
    logout(request)
    return redirect("login")


@require_GET
@login_required
# Порожня головна сторінка для тестування
def rendet_debug_main(request: HttpRequest):
    return render(request, "users/debug_main.html")