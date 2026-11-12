import random


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