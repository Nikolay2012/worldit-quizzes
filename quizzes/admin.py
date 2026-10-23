from django.contrib import admin
from .models import Quiz, QuizSession, QuizAttempt

# Register your models here.
admin.site.register(Quiz)
admin.site.register(QuizSession)
admin.site.register(QuizAttempt)