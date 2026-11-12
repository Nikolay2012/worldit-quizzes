import random
from django.db import IntegrityError
import base64
from io import BytesIO
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask


from .models import AttemptAnswer, QuizSession, QuizAttempt


QR_COLOR = (54, 39, 54)
QR_BACKGROUND = (255, 255, 255)

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



def make_qr_image(url):
    qr = qrcode.QRCode(
        error_correction = qrcode.constants.ERROR_CORRECT_H,
        box_size = 20,
        border = 0,
    )

    qr.add_data(url)

    image = qr.make_image(
        image_factory = StyledPilImage,
        module_drawer = RoundedModuleDrawer(),
        eye_drawer = RoundedModuleDrawer(radius_ratio = 1),
        color_mask = SolidFillColorMask(back_color = QR_BACKGROUND, front_color = QR_COLOR),
    )

    buffer = BytesIO()
    image.save(buffer, format = "PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{encoded}"

def normalize_text(text):
    text = text.strip().lower()

    for symbol in ["’", "ʼ", "‘", "`"]:
        text = text.replace(symbol, "'")

    words = text.split()
    text = " ".join(words)

    return text


def check_text_answer(question, text):
    student_text = normalize_text(text)

    correct_answers = question.answers.filter(is_correct = True)

    for answer in correct_answers:
        if normalize_text(answer.text) == student_text:
            return True

    return False

def shuffle_answers(answers, attempt_id, question_id):
    shuffled = list(answers)

    seed = f"{attempt_id}-{question_id}"

    generator = random.Random(seed)
    generator.shuffle(shuffled)

    return shuffled

# Статистика поточного питання 
def get_question_stats(room):
    question = room.current_question
    attempts = list(room.active_attempts)
    total = len(attempts)

    answers_by_student = {}
    question_answers = AttemptAnswer.objects.filter(
        attempt__session = room,
        question = question,
    ).select_related("attempt").prefetch_related("selected_answers")

    for attempt_answer in question_answers:
        answers_by_student[attempt_answer.attempt.student_id] = attempt_answer

    correct = 0
    wrong = 0
    students = []
    text_answers = []

    for attempt in attempts:
        attempt_answer = answers_by_student.get(attempt.student_id)

        if attempt_answer is None:
            status = "none"
        elif attempt_answer.is_correct:
            status = "correct"
            correct += 1
        else:
            status = "wrong"
            wrong += 1

        students.append({
            "student_id": attempt.student_id,
            "status": status,
        })

        if question.is_text and attempt_answer is not None:
            text_answers.append({
                "name": attempt.student.user.full_name,
                "text": attempt_answer.text_answer,
                "is_correct": attempt_answer.is_correct,
            })

    no_answer = total - correct - wrong

    choices = []
    letters = ["A", "B", "C", "D", "E", "F", "G", "H"]

    if not question.is_text:
        for index, answer in enumerate(question.answers.all()):
            count = 0

            for attempt_answer in answers_by_student.values():
                if attempt_answer.answer_id == answer.id:
                    count += 1
                elif answer in attempt_answer.selected_answers.all():
                    count += 1

            choices.append({
                "letter": letters[index],
                "text": answer.text,
                "is_correct": answer.is_correct,
                "count": count,
            })

    accuracy_by_question = []
    all_questions = list(room.quiz.questions.all())

    for passed_question in all_questions[:room.question_number]:
        correct_count = AttemptAnswer.objects.filter(
            attempt__session = room,
            question = passed_question,
            is_correct = True,
        ).count()

        if total == 0:
            accuracy_by_question.append(0)
        else:
            accuracy_by_question.append(round(correct_count / total * 100))

    return {
        "question_text": question.text,
        "number": room.question_number,
        "questions_total": len(all_questions),
        "is_text": question.is_text,
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "no_answer": no_answer,
        "choices": choices,
        "text_answers": text_answers,
        "students": students,
        "accuracy_by_question": accuracy_by_question,
        "is_last": room.question_number >= len(all_questions)
    }


ACCURACY_GROUPS = [
    {"label": "100%", "min": 100, "max": 100},
    {"label": "80–99%", "min": 80, "max": 99},
    {"label": "60–79%", "min": 60, "max": 79},
    {"label": "40–59%", "min": 40, "max": 59},
    {"label": "Менше 40%", "min": 0, "max": 39},
]

def get_finish_stats(room):
    questions = list(room.quiz.questions.all())
    questions_count = len(questions)

    attempts = list(room.attempts.select_related("student__user"))

    results_map = {}
    all_answers = AttemptAnswer.objects.filter(attempt__session = room)

    for attempt_answer in all_answers:
        key = (attempt_answer.attempt_id, attempt_answer.question_id)
        results_map[key] = attempt_answer.is_correct

    students = []
    total_correct = 0

    for attempt in attempts:
        results = []
        correct_count = 0

        for question in questions:
            is_correct = results_map.get((attempt.id, question.id))

            if is_correct is None:
                results.append("none")
            elif is_correct:
                results.append("correct")
                correct_count += 1
            else:
                results.append("wrong")

        if questions_count == 0:
            accuracy = 0
        else:
            accuracy = round(correct_count / questions_count * 100)

        total_correct += correct_count

        students.append({
            "student_id": attempt.student_id,
            "name": attempt.student.user.full_name,
            "results": results,
            "points": attempt.points,
            "accuracy": accuracy,
        })

    students.sort(key = lambda student: student["points"], reverse = True)

    groups = []
    for group in ACCURACY_GROUPS:
        count = 0

        for student in students:
            if group["min"] <= student["accuracy"] <= group["max"]:
                count += 1

        groups.append({
            "label": group["label"],
            "count": count,
        })

    total_answers = len(students) * questions_count

    if total_answers == 0:
        total_percent = 0
    else:
        total_percent = round(total_correct / total_answers * 100)

    if room.quiz.course:
        course_name = room.quiz.course.name
    else:
        course_name = ""

    return {
        "course_name": course_name,
        "questions_count": questions_count,
        "students_count": len(students),
        "students": students,
        "groups": groups,
        "total_correct": total_correct,
        "total_answers": total_answers,
        "total_percent": total_percent,
    }