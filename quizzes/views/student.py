from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from WorldIT.decorators import required_type
from ..models import QuizSession, QuizAttempt, AttemptAnswer
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
        return context

class StudentQuestionView(StudentLobbyView):
    template_name = "quizzes/student/question.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question = self.room.current_question
        student = self.request.user.profile_student

        attempt = QuizAttempt.objects.filter(session=self.room, student=student).first()

        my_answer = None
        if attempt and question:
            my_answer = AttemptAnswer.objects.filter(attempt=attempt, question=question).first()

        context["my_answer"] = my_answer

        if my_answer:
            correct_answer = question.answers.filter(is_correct=True).first()

            if correct_answer:
                context["correct_text"] = correct_answer.text
            else:
                context["correct_text"] = ""

            if my_answer.is_correct:
                context["my_points"] = question.max_points
            else:
                context["my_points"] = 0

        student = self.request.user.profile_student
        context["attempt"] = QuizAttempt.objects.filter(session = context["room"], student = student).first()
        
        return context

class StudentFinishView(StudentLobbyView):
    template_name = "quizzes/student/finish.html"