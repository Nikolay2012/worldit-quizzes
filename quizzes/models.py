from django.db import models
from django.utils import timezone

from users.models import CustomUser, Mentor, Student
from courses.models import Course


class Quiz(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(
        to=CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_quizzes",
    )

    course = models.ForeignKey(
        to=Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quizzes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Кімната {self.code}"


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
    started_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student} — {self.quiz}"