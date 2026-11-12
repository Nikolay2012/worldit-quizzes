from django.urls import path
from .views import *

urlpatterns = [
    # Ментор
    path('mentor/<int:quiz_id>/start/', StartRoomView.as_view(), name="mentor_start"),
    path('mentor/room/<int:room_id>/lobby/', QuizLobbyView.as_view(), name="mentor_lobby"),
    path('mentor/room/<int:room_id>/start-quiz/', StartQuizView.as_view(), name="mentor_start_quiz"),
    path('mentor/room/<int:room_id>/question/', MentorQuestionView.as_view(), name="mentor_question"),
    path('mentor/room/<int:room_id>/stats/', QuestionStatsView.as_view(), name="mentor_question_stats"),
    path('mentor/room/<int:room_id>/finish/', MentorFinishView.as_view(), name="mentor_finish"),
    path('mentor/room/<int:room_id>/finish-stats/', FinishStatsView.as_view(), name="mentor_finish_stats"),
    

    # Учень
    path('student/join/<str:code>/', JoinRoomView.as_view(), name="student_join"),
    path('student/room/<int:room_id>/lobby/', StudentLobbyView.as_view(), name="student_lobby"),
    path('student/room/<int:room_id>/question/', StudentQuestionView.as_view(), name="student_question"),
    path('student/room/<int:room_id>/finish/', StudentFinishView.as_view(), name="student_finish"),
]