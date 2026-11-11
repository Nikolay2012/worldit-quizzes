import json
from django.utils import timezone
from datetime import timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


from .models import Answer, AttemptAnswer, Question, QuizAttempt, QuizSession
from .services import check_text_answer, shuffle_answers


# Скільки секунд додає кнопка "+15"
ADD_SECONDS = 15


class RoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.is_mentor = False
        
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"room_{self.room_id}"

        if not self.user.is_authenticated:
            await self.close()
            return

        has_access = await self.check_access()
        if not has_access:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.set_status("in_progress")
        await self.send_participants_to_group()

    async def disconnect(self, code):
        if not self.user.is_authenticated:
            return

        await self.set_status("left")
        await self.send_participants_to_group()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_participants_to_group(self):
        participants = await self.get_participants()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "participants_update",
                "participants": participants,
            }
        )

    async def participants_update(self, event):
        await self.send(text_data = json.dumps({
            "action": "participants",
            "participants": event["participants"],
        }))

    # Виконується в кожного учасника групи, коли ментор запустив вікторину
    async def quiz_started(self, event):
        await self.send(text_data = json.dumps({
            "action": "quiz_started",
            "url": event["url"],
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "answer":
            result = await self.save_answer(data.get("answer_id"), data.get("text"), data.get("answer_ids"))

            if result is None:
                return

            # Результат тільки цьому учню (self.send іде лише в його сокет)
            await self.send(text_data = json.dumps({
                "action": "answer_result",
                "is_correct": result["is_correct"],
                "points": result["points"],
                "correct_text": result["correct_text"],
                "stats": result["stats"],
            }))

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "student_answered",
                    "student_id": result["student_id"],
                    "answered": result["answered"],
                    "total": result["total"],
                    "total_points": result["total_points"],
                    "accuracy": result["accuracy"],
                }
            )

        elif action in ["next_question", "finish"]:
            result = await self.change_question(finish = (action == "finish"))

            if result == "next":
                await self.channel_layer.group_send(self.group_name, {"type": "question_changed"})
            elif result == "finished":
                await self.channel_layer.group_send(self.group_name, {"type": "quiz_finished"})

        elif action in ["pause", "add_time"]:
            result = await self.change_time(action)

            if result is None:
                return

            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "time_changed",
                    "time_left": result["time_left"],
                    "paused": result["paused"],
                }
            )

    async def student_answered(self, event):
        data = {
            "action": "answered",
            "student_id": event["student_id"],
            "answered": event["answered"],
            "total": event["total"],
        }

        if self.is_mentor:
            data["total_points"] = event["total_points"]
            data["accuracy"] = event["accuracy"]

        await self.send(text_data = json.dumps(data))

    async def quiz_finished(self, event):
        await self.send(text_data = json.dumps({"action": "finished"}))

    async def time_changed(self, event):
        await self.send(text_data = json.dumps({
            "action": "time_changed",
            "time_left": event["time_left"],
            "paused": event["paused"],
        }))

    #ментор перемкнув питання і кожному надсилаємо дані нового питання
    async def question_changed(self, event):
        data = await self.get_question_data()

        await self.send(text_data = json.dumps({
            "action": "next_question",
            "number": data["number"],
            "total": data["total"],
            "text": data["text"],
            "type": data["type"],
            "answers": data["answers"],
            "participants_total": data["participants_total"],
            "time_left": data["time_left"],
            "stats": data["stats"],
            "is_text": data["is_text"],
            "is_many": data["is_many"],
        }))

    # Дані поточного питання для цього підключення
    @database_sync_to_async
    def get_question_data(self):
        room = QuizSession.objects.get(id = self.room_id)
        question = room.current_question

        mentor = getattr(self.user, "profile_mentor", None)
        is_mentor = self.user.is_superuser or (mentor is not None and room.mentor_id == mentor.id)

        question_answers = list(question.answers.all())

        student = getattr(self.user, "profile_student", None)
        attempt = None

        if student is not None:
            attempt = QuizAttempt.objects.filter(session = room, student = student).first()

        if not is_mentor and attempt is not None:
            question_answers = shuffle_answers(question_answers, attempt.id, question.id)

        answers = []
        for answer in question_answers:
            item = {
                "id": answer.id,
                "text": answer.text,
            }
            if is_mentor:
                item["is_correct"] = answer.is_correct
            answers.append(item)

        if question.is_text and not is_mentor:
            answers = []

        data = {
            "number": room.question_number,
            "total": room.quiz.questions.count(),
            "text": question.text,
            "type": question.get_type_display(),
            "answers": answers,
            "participants_total": room.active_attempts.count(),
            "time_left": room.time_left,
            "stats": None,
            "is_text": question.is_text,
            "is_many": question.is_many,
        }

        if attempt is not None:
            data["stats"] = attempt.get_stats()

        return data

    # Зберігаємо відповідь учня
    @database_sync_to_async
    def save_answer(self, answer_id, text, answer_ids):
        # Відповідати може тільки учень
        student = getattr(self.user, "profile_student", None)
        if student is None:
            return None

        room = QuizSession.objects.get(id = self.room_id)

        # Відповідати можна тільки поки йде тест
        if room.status != QuizSession.STATUS_STARTED:
            return None

        if room.time_left <= 0:
            return None

        question = room.current_question

        attempt = QuizAttempt.objects.filter(session = room, student = student).first()
        if attempt is None:
            return None

        already = AttemptAnswer.objects.filter(attempt = attempt, question = question).exists()
        if already:
            return None

        chosen_answers = []

        if question.is_text:
            if not text or not text.strip():
                return None

            answer = None
            text_answer = text.strip()
            is_correct = check_text_answer(question, text_answer)

        elif question.is_many:
            if not answer_ids:
                return None

            chosen_answers = list(Answer.objects.filter(id__in = answer_ids, question = question))

            if len(chosen_answers) != len(set(answer_ids)):
                return None

            chosen_ids = set()
            for chosen in chosen_answers:
                chosen_ids.add(chosen.id)

            correct_ids = set(question.answers.filter(is_correct = True).values_list("id", flat = True))

            is_correct = chosen_ids == correct_ids

            answer = None
            text_answer = None

        else:
            answer = Answer.objects.filter(id = answer_id, question = question).first()
            if answer is None:
                return None

            text_answer = None
            is_correct = answer.is_correct

        attempt_answer = AttemptAnswer.objects.create(
            attempt = attempt,
            question = question,
            answer = answer,
            text_answer = text_answer,
            is_correct = is_correct,
        )

        if chosen_answers:
            attempt_answer.selected_answers.set(chosen_answers)

        # Бали за це питання
        if is_correct:
            points = question.max_points
        else:
            points = 0

        attempt.points += points

        total_answers = attempt.answers.count()
        correct_answers = attempt.answers.filter(is_correct = True).count()
        attempt.accuracy = round(correct_answers / total_answers * 100)

        attempt.save()

        answered = AttemptAnswer.objects.filter(attempt__session = room, question = question).count()
        total = room.active_attempts.count()

        correct_text = question.correct_text

        return {
            "student_id": student.id,
            "answered": answered,
            "total": total,
            "is_correct": is_correct,
            "points": points,
            "correct_text": correct_text,
            "total_points": attempt.points,
            "accuracy": attempt.accuracy,
            "stats": attempt.get_stats(),
        }

    @database_sync_to_async
    def change_time(self, action):
        if not self.is_mentor:
            return None

        room = QuizSession.objects.get(id = self.room_id)

        if room.status != QuizSession.STATUS_STARTED:
            return None

        if room.all_answered:
            return None

        now = timezone.now()

        if action == "pause":
            if room.question_paused_at is None:
                room.question_paused_at = now
            else:
                paused_for = now - room.question_paused_at
                room.question_started_at = room.question_started_at + paused_for
                room.question_paused_at = None

        elif action == "add_time":
            new_left = room.time_left + ADD_SECONDS

            if room.question_paused_at is not None:
                end_moment = room.question_paused_at
            else:
                end_moment = now

            time_limit = room.current_question.time_limit
            room.question_started_at = end_moment - timedelta(seconds = time_limit - new_left)

        room.save()

        return {
            "time_left": room.time_left,
            "paused": room.question_paused_at is not None,
        }

    # Наступне питання або завершення (тільки ментор кімнати чи адмін)
    @database_sync_to_async
    def change_question(self, finish):
        room = QuizSession.objects.get(id = self.room_id)

        mentor = getattr(self.user, "profile_mentor", None)
        if room.mentor != mentor and not self.user.is_superuser:
            return None

        questions_count = room.quiz.questions.count()
        is_last = room.current_question_index >= questions_count - 1

        if not finish and not is_last:
            room.current_question_index += 1
            room.question_started_at = timezone.now()
            room.question_paused_at = None
            room.save()
            return "next"

        room.status = QuizSession.STATUS_FINISHED
        room.code = None
        room.finished_at = timezone.now()
        room.save()
        return "finished"

    @database_sync_to_async
    def set_status(self, status):
        student = getattr(self.user, "profile_student", None)
        if student is None:
            return

        attempts = QuizAttempt.objects.filter(session_id = self.room_id, student = student)

        if status == QuizAttempt.STATUS_LEFT:
            attempts = attempts.filter(session__status = QuizSession.STATUS_LOBBY)

        attempts.update(status = status)

    @database_sync_to_async
    def get_participants(self):
        attempts = QuizAttempt.objects.filter(session_id = self.room_id, status = "in_progress").select_related("student__user")

        participants = []
        for attempt in attempts:
            participants.append({
                "id": attempt.student.id,
                "name": attempt.student.user.full_name,
            })

        return participants

    @database_sync_to_async
    def check_access(self):
        room = QuizSession.objects.filter(id = self.room_id).first()

        if room is None:
            return False

        if self.user.is_superuser:
            self.is_mentor = True
            return True

        mentor = getattr(self.user, "profile_mentor", None)
        if mentor is not None and room.mentor_id == mentor.id:
            self.is_mentor = True
            return True

        student = getattr(self.user, "profile_student", None)
        if student is not None:
            return QuizAttempt.objects.filter(session = room, student = student).exists()

        return False