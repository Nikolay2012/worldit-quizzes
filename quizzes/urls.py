from django.urls import path
from .views import StartRoomView, QuizLobbyView, JoinRoomView, StudentLobbyView

urlpatterns = [
    # Ментор
    path('mentor/<int:quiz_id>/start/', StartRoomView.as_view(), name="mentor_start"),
    path('mentor/room/<int:room_id>/lobby/', QuizLobbyView.as_view(), name="mentor_lobby"),

    # Учень
    path('student/join/<str:code>/', JoinRoomView.as_view(), name="student_join"),
    path('student/room/<int:room_id>/lobby/', StudentLobbyView.as_view(), name="student_lobby"),
]