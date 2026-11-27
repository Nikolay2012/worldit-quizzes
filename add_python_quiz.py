import os
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WorldIT.settings")
django.setup()


from users.models import CustomUser
from quizzes.models import Quiz, Question, Answer


QUIZ_TITLE = "Python для початківців"
AUTHOR_USERNAME = "vova"

QUESTIONS = [
    {
        "text": "Яким символом починається однорядковий коментар у Python?",
        "type": Question.TYPE_ONE,
        "time_limit": 30,
        "answers": [("#", True), ("//", False), ("--", False), ("/*", False)],
    },
    {
        "text": "Що виведе print(2 ** 3)?",
        "type": Question.TYPE_ONE,
        "time_limit": 30,
        "answers": [("6", False), ("8", True), ("9", False), ("5", False)],
    },
    {
        "text": "Яка функція перетворює рядок \"42\" на ціле число?",
        "type": Question.TYPE_INPUT,
        "time_limit": 40,
        "answers": [("int", True), ("int()", True)],
    },
    {
        "text": "Що поверне вираз 10 % 3?",
        "type": Question.TYPE_ONE,
        "time_limit": 40,
        "answers": [("3", False), ("1", True), ("0", False), ("3.33", False)],
    },
    {
        "text": "Які з цих імен змінних допустимі в Python?",
        "type": Question.TYPE_MANY,
        "time_limit": 50,
        "answers": [("my_name", True), ("2name", False), ("_count", True), ("my-name", False)],
    },
    {
        "text": "Якого типу значення True?",
        "type": Question.TYPE_ONE,
        "time_limit": 30,
        "answers": [("str", False), ("int", False), ("bool", True), ("None", False)],
    },
    {
        "text": "Яке ключове слово означає «інакше» після умови if?",
        "type": Question.TYPE_INPUT,
        "time_limit": 40,
        "answers": [("else", True)],
    },
    {
        "text": "Які з цих циклів є в Python?",
        "type": Question.TYPE_MANY,
        "time_limit": 45,
        "answers": [("for", True), ("while", True), ("repeat", False), ("do-while", False)],
    },
    {
        "text": "Який індекс має перший елемент списку? Впишіть число.",
        "type": Question.TYPE_INPUT,
        "time_limit": 40,
        "answers": [("0", True)],
    },
    {
        "text": "Які з цих методів є в рядків (str)?",
        "type": Question.TYPE_MANY,
        "time_limit": 50,
        "answers": [("upper()", True), ("lower()", True), ("append()", False), ("push()", False)],
    },
]


def add_quiz():
    author = CustomUser.objects.filter(username = AUTHOR_USERNAME).first()

    if author is None:
        print(f"Користувача {AUTHOR_USERNAME} не знайдено")
        return

    already_exists = Quiz.objects.filter(title = QUIZ_TITLE, author = author).exists()

    if already_exists:
        print("Тест уже є в базі, нічого не додано")
        return

    quiz = Quiz.objects.create(title = QUIZ_TITLE, author = author)

    for question_number, item in enumerate(QUESTIONS, start = 1):
        question = Question.objects.create(
            quiz = quiz,
            text = item["text"],
            type = item["type"],
            order_number = question_number,
            time_limit = item["time_limit"],
            max_points = 1000,
        )

        for answer_number, (answer_text, is_correct) in enumerate(item["answers"], start = 1):
            Answer.objects.create(
                question = question,
                text = answer_text,
                is_correct = is_correct,
                order_number = answer_number,
            )

    print(f"Тест «{QUIZ_TITLE}» додано, id = {quiz.id}")


add_quiz()