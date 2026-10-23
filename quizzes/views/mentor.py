from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
from ..models import Quiz, QuizSession
from ..services import get_or_create_room


mentor_only = [
    login_required,
    required_type(["mentor", "admin"]),
]


@method_decorator(mentor_only, name="dispatch")
class StartRoomView(View):
    def get(self, request: HttpRequest, quiz_id: int):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        mentor = getattr(request.user, "profile_mentor", None)

        room = get_or_create_room(quiz, mentor)

        return redirect("mentor_lobby", room_id=room.id)


@method_decorator(mentor_only, name="dispatch")
class QuizLobbyView(TemplateView):
    template_name = "quizzes/mentor/lobby.html"

    def get(self, request: HttpRequest, room_id: int, *args, **kwargs):
        self.room = get_object_or_404(QuizSession, id=room_id)

        mentor = getattr(request.user, "profile_mentor", None)
        is_admin = "admin" in request.user.account_types

        if self.room.mentor != mentor and not is_admin:
            return redirect("debug_main")

        return super().get(request, room_id=room_id, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        quiz = self.room.quiz

        if quiz.course:
            subject = quiz.course.name
        else:
            subject = "Українська мова"

        context["quiz_title"] = quiz.title
        context["subject"] = subject
        context["questions_count"] = 10
        context["duration"] = "6 хв 45 с"
        context["join_code"] = f"{self.room.code[:3]} {self.room.code[3:]}"
        context["participants"] = [
            {"name": "Олена Коваль"},
            {"name": "Максим Бондар"},
        ]
        # об'єкт кімнати
        context["room"] = self.room

        return context