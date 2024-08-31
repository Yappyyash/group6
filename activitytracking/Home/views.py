import threading
import time
import json
import win32gui
import win32process
import psutil
from django.shortcuts import render
from django.middleware.csrf import get_token
from django.http import JsonResponse, HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import AccessToken
from .models import person_collection
from .hashing import hash_password, check_password
from .creatingToken import create_tokens
from .image_utils import *
from django.views.decorators.csrf import csrf_exempt

# Shared state for tracking
tracking_event = threading.Event()
tracked_applications = []
screenshot_thread = None
tracking_lock = threading.Lock()

# HTML views
def Home(request):
    return render(request, "Home/index.html")

def Dashboard(request):
    return render(request, "Dashboard/index.html")

def Auth(request):
    return render(request, "Auth/signin.html")

def Signup(request):
    return render(request, "Auth/signup.html")

def Front(request):
    return render(request, "Front/index.html")

def Activity(request):
    return render(request, "Activity/index.html")

def show_imgpage(request):
    return render(request, "show_images/index.html")

# DRF views for authentication
@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')

    if not username or not password or not email:
        return Response({'error': 'Please provide all required fields'}, status=status.HTTP_400_BAD_REQUEST)

    if person_collection.find_one({'username': username}):
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

    hashed_password = hash_password(password)

    # Store user in MongoDB
    person_collection.insert_one({
        'username': username,
        'email': email,
        'password': hashed_password,
    })

    # Generate JWT tokens
    user = {
        'username': username,
        'email': email,
    }
    access_token, refresh_token = create_tokens(user)
    fetched_user_data = person_collection.find_one({'username': username})

    return Response({
        'username': username,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user_id': str(fetched_user_data['_id'])
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Please provide both username and password'}, status=status.HTTP_400_BAD_REQUEST)

    user = person_collection.find_one({'username': username})
    if user and check_password(user['password'], password):
        access_token, refresh_token = create_tokens(user)
        request.session.access_token = str(access_token)
        return Response({
            'username': username,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': str(user['_id'])
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def protected_route(request):
    access_token = request.session.get('access_token')

    if not access_token:
        return Response({'error': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        token = AccessToken(access_token)
        return Response({"message": "You have access to this protected route."}, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Invalid token.'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout(request):
    return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)

# Activity Tracking
def get_active_window_name():
    window = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(window)

def get_active_process_name():
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None

def track_active_applications(user_id):
    global tracked_applications, screenshot_thread
    tracked_applications = []

    # Start screenshot capture
    screenshot_thread = threading.Thread(target=capture_screenshot_interval, args=(user_id, 10))
    screenshot_thread.start()

    while tracking_event.is_set():
        active_window_name = get_active_window_name()
        with tracking_lock:
            if active_window_name and (not tracked_applications or active_window_name != tracked_applications[-1]):
                tracked_applications.append(active_window_name)
        time.sleep(3)

    tracking_event.clear()

@api_view(['POST'])
def start_tracking(request):
    if not tracking_event.is_set():
        tracking_event.set()
        user_id = request.data.get('id')
        thread = threading.Thread(target=track_active_applications, args=(user_id,))
        thread.start()
    return Response({'status': 'started'})

@api_view(['POST'])
def stop_tracking(request):
    tracking_event.clear()  # Signal the thread to stop

    # Use a timeout to avoid blocking indefinitely if something goes wrong
    if screenshot_thread and screenshot_thread.is_alive():
        screenshot_thread.join(timeout=2)

    user_id = request.data.get('id')
    person_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"tracked_applications": tracked_applications}}
        )
     # Clear the tracked applications list
    tracked_applications.clear()

    return Response({'status': 'stopped'})


@api_view(['GET'])
def get_applications(request):
    return Response({'applications': tracked_applications})

@csrf_exempt
def get_my_images(request):
    if request.method == 'POST':
        try:
            request_data = json.loads(request.body)
            user_id = request_data.get('id')

            if not user_id:
                return JsonResponse({'error': 'User ID not provided'}, status=400)

            all_screenshots = get_all_screenshots(user_id)
            
            if isinstance(all_screenshots, HttpResponse):
                return all_screenshots

            return JsonResponse({'screenshots': all_screenshots})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return HttpResponse('Method Not Allowed', status=405)

def test_csrf_view(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})
