from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest, HttpResponseNotFound
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
from ..models import QuizSession, QuizAttempt
from ..services import join_room


student_only = [
    login_required,
    required_type(["student"]),
]


@method_decorator(student_only, name="dispatch")
class JoinRoomView(View):
    def get(self, request: HttpRequest, code: str):
        student = request.user.profile_student

        room = join_room(code, student)

        if not room:
            return redirect("debug_main")

        return redirect("student_lobby", room_id=room.id)


@method_decorator(student_only, name="dispatch")
class StudentLobbyView(TemplateView):
    template_name = "quizzes/student/lobby.html"

    def get(self, request: HttpRequest, room_id: int, *args, **kwargs):
        self.room = get_object_or_404(QuizSession, id=room_id)

        is_member = QuizAttempt.objects.filter(
            session=self.room,
            student=request.user.profile_student,
        ).exists()

        if not is_member:
            return redirect("debug_main")

        return super().get(request, room_id=room_id, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["room"] = self.room
        context["quiz_title"] = self.room.quiz.title
        return context