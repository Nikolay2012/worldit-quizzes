from django.db import models
from django.utils import timezone
import math

from users.models import CustomUser, Mentor, Student
from courses.models import Course



class Quiz(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(
        to = CustomUser,
        on_delete = models.SET_NULL,
        null = True,
        related_name = "created_quizzes",
    )
    course = models.ForeignKey(
        to = Course,
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "quizzes",
    )
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return self.title

    @property
    def duration_display(self):
        result = self.questions.aggregate(total = models.Sum("time_limit"))
        total = result["total"]

        if total is None:
            total = 0

        minutes = total // 60   
        seconds = total % 60   

        if minutes and seconds:
            return f"{minutes} хв {seconds} с"
        if minutes:
            return f"{minutes} хв"
        return f"{seconds} с"

class Question(models.Model):
    TYPE_ONE = "one_answer"
    TYPE_MANY = "many_answers"
    TYPE_INPUT = "input_gap"

    TYPE_CHOICES = (
        (TYPE_ONE, "Запитання з однією правильною відповіддю"),
        (TYPE_MANY, "Запитання з кількома правильними відповідями"),
        (TYPE_INPUT, "Запитання з відповіддю, яку треба вписати"),
    )

    quiz = models.ForeignKey(to = Quiz, on_delete = models.CASCADE, related_name = "questions")
    text = models.TextField()
    image = models.ImageField(upload_to = "quizzes/questions/", blank = True, null = True)
    type = models.CharField(max_length = 20, choices = TYPE_CHOICES, default = TYPE_ONE)
    order_number = models.PositiveIntegerField(default = 1)
    time_limit = models.PositiveIntegerField(default = 30)
    max_points = models.PositiveIntegerField(default = 1000)

    class Meta:
        ordering = ["order_number"]

    def __str__(self):
        return f"{self.quiz.title}: {self.text[:40]}"

    @property
    def is_text(self):
        return self.type == Question.TYPE_INPUT

    @property
    def is_many(self):
        return self.type == Question.TYPE_MANY

    @property
    def correct_text(self):
        correct_answers = self.answers.filter(is_correct = True)

        texts = []
        for answer in correct_answers:
            texts.append(answer.text)

        return ", ".join(texts)

    


class Answer(models.Model):
    question = models.ForeignKey(to=Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="quizzes/answers/", blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    order_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order_number"]

    def __str__(self):
        return self.text



class QuizSession(models.Model):
    STATUS_LOBBY = "lobby"
    STATUS_STARTED = "started"
    STATUS_FINISHED = "finished"
    STATUS_CHOICES = (
        (STATUS_LOBBY, "Очікування"),
        (STATUS_STARTED, "Йде тест"),
        (STATUS_FINISHED, "Завершено"),
    )

    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE, related_name="sessions")
    mentor = models.ForeignKey(
        to=Mentor,
        on_delete=models.SET_NULL,
        null=True,
        related_name="quiz_sessions",
    )
    code = models.CharField(max_length = 8, unique = True, null = True, blank = True)
    status = models.CharField(max_length = 20, choices = STATUS_CHOICES, default = STATUS_LOBBY)
    current_question_index = models.PositiveIntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add = True)
    #час старту поточного питання
    question_started_at = models.DateTimeField(null=True, blank=True)
    #коли ментор поставив питання на паузу
    question_paused_at = models.DateTimeField(null = True, blank = True)
    question_opened_at = models.DateTimeField(null = True, blank = True)

    def __str__(self):
        return f"Кімната {self.code}"

    def get_end_moment(self):
        if self.all_answered:
            last_answer = AttemptAnswer.objects.filter(
                attempt__session = self,
                question = self.current_question,
            ).order_by("-answered_at").first()
            return last_answer.answered_at

        if self.question_paused_at is not None:
            return self.question_paused_at

        return timezone.now()

    @property
    def code_display(self):
        if not self.code:
            return ""
        
        return f"{self.code[:3]} {self.code[3:]}"

    @property
    def active_attempts(self):
        attempts = self.attempts.filter(status = QuizAttempt.STATUS_IN_PROGRESS)
        return attempts.select_related("student__user")

    @property
    def current_question(self):
        questions = list(self.quiz.questions.all())

        if self.current_question_index < len(questions):
            return questions[self.current_question_index]

        return None

    @property
    def question_number(self):
        return self.current_question_index + 1

    # id учнів, які вже відповіли на поточне питання
    @property
    def answered_student_ids(self):
        question = self.current_question

        if question is None:
            return []

        answers = AttemptAnswer.objects.filter(attempt__session=  self, question = question)

        return list(answers.values_list("attempt__student_id", flat = True))

    # Скільки відсотків учнів відповіли 
    @property
    def answered_percent(self):
        total = self.active_attempts.count()

        if total == 0:
            return 0

        return round(len(self.answered_student_ids) / total * 100)

    #скільки секунд лишилось на поточне питання
    @property
    def time_left(self):
        question = self.current_question

        if question is None or self.question_started_at is None:
            return 0

        passed = (self.get_end_moment() - self.question_started_at).total_seconds()
        left = question.time_limit - passed

        if left <= 0:
            return 0

        #ceil округлює вгору(наприкалд 29.4 на 30с)
        return math.ceil(left)

    #чи всі учні вже відповіли на поточне питання
    @property
    def all_answered(self):
        total = self.active_attempts.count()

        if total == 0:
            return False

        return len(self.answered_student_ids) >= total

    # Питання завершене, тобто усі відповіли або вийшов час
    @property
    def question_finished(self):
        if self.status != QuizSession.STATUS_STARTED:
            return False

        return self.all_answered or self.time_left == 0


class QuizAttempt(models.Model):
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_LEFT = "left"
    STATUS_CHOICES = (
        (STATUS_IN_PROGRESS, "У кімнаті"),
        (STATUS_LEFT, "Вийшов"),
    )

    quiz = models.ForeignKey(to=Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(to=Student, on_delete=models.CASCADE, related_name="quiz_attempts")
    session = models.ForeignKey(
        to=QuizSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_IN_PROGRESS)
    points = models.PositiveIntegerField(default=0)
    accuracy = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student} — {self.quiz}"

    @property
    def correct_count(self):
        return self.answers.filter(is_correct = True).count()

    @property
    def wrong_count(self):
        return self.answers.filter(is_correct = False).count()

    @property
    def skipped_count(self):
        room = self.session

        if room is None:
            return 0

        passed = room.current_question_index

        if room.status == QuizSession.STATUS_FINISHED:
            passed = room.quiz.questions.count()

        passed_ids = list(room.quiz.questions.values_list("id", flat = True)[:passed])
        answered = self.answers.filter(question_id__in = passed_ids).count()

        return passed - answered

    @property
    def accuracy_display(self):
        if self.answers.count() == 0:
            return "-"

        return f"{round(self.accuracy)}%"

    def get_stats(self):
        return {
            "correct": self.correct_count,
            "wrong": self.wrong_count,
            "skipped": self.skipped_count,
            "accuracy": self.accuracy_display,
            "points": self.points,
        }

class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(to=QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(to=Question, on_delete=models.CASCADE, related_name="student_answers")
    answer = models.ForeignKey(to=Answer, on_delete=models.SET_NULL, null=True, related_name="selections")
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)
    text_answer = models.CharField(max_length = 255, blank = True, null = True)
    selected_answers = models.ManyToManyField(to = Answer, related_name = "multi_selections", blank = True)
    time_spent = models.PositiveIntegerField(default = 0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="unique_answer_per_question"),
        ]