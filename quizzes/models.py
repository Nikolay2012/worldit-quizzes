from django.db import models
from django.utils import timezone

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
    code = models.CharField(max_length=8, unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_LOBBY)
    current_question_index = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Кімната {self.code}"

    @property
    def code_display(self):
        if not self.code:
            return ""
        
        return f"{self.code[:3]} {self.code[3:]}"

    @property
    def active_attempts(self):
        attempts = self.attempts.filter(status=QuizAttempt.STATUS_IN_PROGRESS)
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