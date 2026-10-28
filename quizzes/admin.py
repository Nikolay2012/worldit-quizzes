from django.contrib import admin
from .models import Quiz, Question, Answer, QuizSession, QuizAttempt


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4  


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]


# Register your models here.
admin.site.register(QuizSession)
admin.site.register(QuizAttempt)