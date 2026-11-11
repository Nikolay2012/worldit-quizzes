from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest, JsonResponse
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from WorldIT.decorators import required_type
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone


from ..models import Quiz, QuizSession
from ..services import get_or_create_room, make_qr_image

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
        context["room"] = self.room

        if self.room.code:
            invite_url = self.request.build_absolute_uri(
                reverse("student_join", args=[self.room.code])
            )
            
            context["invite_url"] = invite_url
            context["qr_image"] = make_qr_image(invite_url)

        return context

@method_decorator(mentor_only, name="dispatch")
class StartQuizView(View):
    def post(self, request: HttpRequest, room_id: int):
        room = get_object_or_404(QuizSession, id=room_id)

        mentor = getattr(request.user, "profile_mentor", None)
        is_admin = "admin" in request.user.account_types

        if room.mentor != mentor and not is_admin:
            return JsonResponse({"success": False, "message": "Це не ваша кімната"}, status = 403)

        if not room.active_attempts.exists():
            return JsonResponse({"success": False, "message": "У кімнаті ще немає учасників"}, status = 400)

        room.status = QuizSession.STATUS_STARTED
        room.started_at = timezone.now()

        room.question_started_at = timezone.now()
        room.save()

        channel_layer = get_channel_layer()
        student_url = reverse("student_question", args=[room.id])

        async_to_sync(channel_layer.group_send)(
            f"room_{room.id}",
            {
                "type": "quiz_started",
                "url": student_url,
            }
        )

        question_url = reverse("mentor_question", args=[room.id])
        return JsonResponse({"success": True, "url": question_url})

class MentorQuestionView(QuizLobbyView):
    template_name = "quizzes/mentor/question.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question = self.room.current_question

        answers = []
        if question:
            answers = question.answers.all()

        context["question"] = question
        context["answers"] = answers

        return context


class MentorFinishView(QuizLobbyView):
    template_name = "quizzes/mentor/finish.html"


