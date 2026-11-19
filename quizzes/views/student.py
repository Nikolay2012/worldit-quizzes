from django.shortcuts import redirect, get_object_or_404
from django.http import HttpRequest, JsonResponse
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from WorldIT.decorators import required_type
from ..models import QuizSession, QuizAttempt, AttemptAnswer
from ..services import join_room, shuffle_answers, get_student_result, get_questions_list


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

        attempt = QuizAttempt.objects.filter(session = self.room, student = student).first()

        answers = []
        if question and attempt and not question.is_text:
            answers = shuffle_answers(question.answers.all(), attempt.id, question.id)

        context["question"] = question
        context["answers"] = answers
        context["attempt"] = attempt

        my_answer = None
        if attempt and question:
            my_answer = AttemptAnswer.objects.filter(attempt = attempt, question = question).first()

        context["my_answer"] = my_answer

        my_answer_ids = []

        if my_answer:
            if my_answer.answer_id:
                my_answer_ids.append(my_answer.answer_id)

            for selected in my_answer.selected_answers.all():
                my_answer_ids.append(selected.id)

        context["my_answer_ids"] = my_answer_ids

        if my_answer:
            # context["correct_text"] = question.correct_text

            if my_answer.is_correct:
                context["my_points"] = question.max_points
            else:
                context["my_points"] = 0

        return context

class StudentFinishView(StudentLobbyView):
    template_name = "quizzes/student/finish.html"

def can_see_results(room, student):
    is_member = QuizAttempt.objects.filter(session = room, student = student).exists()

    if not is_member:
        return False

    return room.status == QuizSession.STATUS_FINISHED


@method_decorator(student_only, name="dispatch")
class StudentResultDataView(View):
    def get(self, request: HttpRequest, room_id: int):
        room = get_object_or_404(QuizSession, id = room_id)
        student = request.user.profile_student

        if not can_see_results(room, student):
            return JsonResponse({"error": "Немає доступу"}, status = 403)

        return JsonResponse(get_student_result(room, student.id))


@method_decorator(student_only, name="dispatch")
class StudentQuestionsListView(View):
    def get(self, request: HttpRequest, room_id: int):
        room = get_object_or_404(QuizSession, id = room_id)
        student = request.user.profile_student

        if not can_see_results(room, student):
            return JsonResponse({"error": "Немає доступу"}, status = 403)

        return JsonResponse(get_questions_list(room, hide_names = True))