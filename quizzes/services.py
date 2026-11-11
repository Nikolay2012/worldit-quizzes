import random
from django.db import IntegrityError
import base64
from io import BytesIO
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask


from .models import QuizSession, QuizAttempt


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