import random
from django.db import IntegrityError
from .models import QuizSession, QuizAttempt


def generate_code():
    while True:
        str_code = ''
        for num in range(6):
            random_num = random.randint(0, 9)
            str_code += str(random_num)

        check_room = QuizSession.objects.filter(code= str_code).first()

        if not check_room:
            break

    return str_code


def get_or_create_room(quiz, mentor):
    room = QuizSession.objects.filter(quiz=quiz, mentor=mentor, status="lobby").first()

    if room:
        return room

    while True:
        try:
            room = QuizSession.objects.create(quiz = quiz, mentor = mentor, code = generate_code())
            return room
        except IntegrityError:
            continue

def join_room(code, student):
    clean_code = code.replace(" ", "")
    room = QuizSession.objects.filter(code=clean_code, status="lobby").first()

    if not room:
        return None

    attempt = QuizAttempt.objects.filter(session=room, student=student).first()

    if not attempt:
        QuizAttempt.objects.create(quiz=room.quiz, student=student, session=room)

    return room