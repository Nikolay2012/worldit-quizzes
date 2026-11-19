from ..models import AttemptAnswer


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

        if question.is_text:
            text = ""
            if attempt_answer is not None:
                text = attempt_answer.text_answer

            text_answers.append({
                "name": attempt.student.user.full_name,
                "text": text,
                "status": status,
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


def get_answer_text(question, attempt_answer):
    if question.is_text:
        return attempt_answer.text_answer or ""

    if question.is_many:
        texts = []
        for answer in attempt_answer.selected_answers.all():
            texts.append(answer.text)
        return ", ".join(texts)

    if attempt_answer.answer is not None:
        return attempt_answer.answer.text

    return ""


def get_student_result(room, student_id):
    attempt = room.attempts.select_related("student__user").filter(student_id = student_id).first()

    if attempt is None:
        return None

    questions = list(room.quiz.questions.all())
    questions_count = len(questions)

    answers_map = {}
    attempt_answers = attempt.answers.select_related("answer").prefetch_related("selected_answers")

    for attempt_answer in attempt_answers:
        answers_map[attempt_answer.question_id] = attempt_answer

    rows = []
    correct = 0
    wrong = 0
    no_answer = 0
    max_points = 0
    times = []

    for index, question in enumerate(questions):
        max_points += question.max_points
        attempt_answer = answers_map.get(question.id)

        if attempt_answer is None:
            status = "none"
            answer_text = ""
            no_answer += 1
        else:
            if attempt_answer.is_correct:
                status = "correct"
                correct += 1
            else:
                status = "wrong"
                wrong += 1

            answer_text = get_answer_text(question, attempt_answer)

            if attempt_answer.time_spent > 0:
                times.append(attempt_answer.time_spent)

        rows.append({
            "number": index + 1,
            "question": question.text,
            "answer": answer_text,
            "status": status,
        })

    if questions_count == 0:
        accuracy = 0
    else:
        accuracy = round(correct / questions_count * 100)

    if times:
        average_time = round(sum(times) / len(times))
    else:
        average_time = None

    accuracy_by_question = []
    correct_so_far = 0

    for index, row in enumerate(rows):
        if row["status"] == "correct":
            correct_so_far += 1

        accuracy_by_question.append(round(correct_so_far / (index + 1) * 100))

    if room.quiz.course:
        course_name = room.quiz.course.name
    else:
        course_name = ""

    return {
        "student_id": attempt.student_id,
        "name": attempt.student.user.full_name,
        "course_name": course_name,
        "points": attempt.points,
        "max_points": max_points,
        "accuracy": accuracy,
        "average_time": average_time,
        "correct": correct,
        "wrong": wrong,
        "no_answer": no_answer,
        "rows": rows,
        "accuracy_by_question": accuracy_by_question,
    }

def get_questions_list(room, hide_names = False):
    questions = list(room.quiz.questions.prefetch_related("answers"))
    attempts = list(room.attempts.select_related("student__user"))

    students_count = len(attempts)
    questions_count = len(questions)

    answers_by_question = {}
    all_answers = AttemptAnswer.objects.filter(
        attempt__session = room,
    ).select_related("attempt__student__user").prefetch_related("selected_answers")

    for attempt_answer in all_answers:
        if attempt_answer.question_id not in answers_by_question:
            answers_by_question[attempt_answer.question_id] = []

        answers_by_question[attempt_answer.question_id].append(attempt_answer)

    items = []
    total_correct = 0
    max_points = 0

    for index, question in enumerate(questions):
        max_points += question.max_points
        question_answers = answers_by_question.get(question.id, [])

        correct = 0
        wrong = 0

        for attempt_answer in question_answers:
            if attempt_answer.is_correct:
                correct += 1
            else:
                wrong += 1

        no_answer = students_count - correct - wrong
        total_correct += correct

        if students_count == 0:
            percent = 0
        else:
            percent = round(correct / students_count * 100)

        options = []
        text_answers = []

        if question.is_text:
            answers_by_attempt = {}
            for attempt_answer in question_answers:
                answers_by_attempt[attempt_answer.attempt_id] = attempt_answer

            for attempt in attempts:
                attempt_answer = answers_by_attempt.get(attempt.id)

                if attempt_answer is None:
                    status = "none"
                    text = ""
                elif attempt_answer.is_correct:
                    status = "correct"
                    text = attempt_answer.text_answer or ""
                else:
                    status = "wrong"
                    text = attempt_answer.text_answer or ""

                if hide_names:
                    name = ""
                else:
                    name = attempt.student.user.full_name

                text_answers.append({
                    "name": name,
                    "text": text,
                    "status": status,
                })
        else:
            for answer in question.answers.all():
                count = 0

                for attempt_answer in question_answers:
                    if attempt_answer.answer_id == answer.id:
                        count += 1
                    elif answer in attempt_answer.selected_answers.all():
                        count += 1

                options.append({
                    "text": answer.text,
                    "is_correct": answer.is_correct,
                    "count": count,
                })

        items.append({
            "number": index + 1,
            "text": question.text,
            "is_text": question.is_text,
            "correct": correct,
            "wrong": wrong,
            "no_answer": no_answer,
            "percent": percent,
            "options": options,
            "text_answers": text_answers,
            "correct_text": question.correct_text,
        })

    points_sum = 0
    for attempt in attempts:
        points_sum += attempt.points

    total_answers = students_count * questions_count

    if total_answers == 0:
        total_percent = 0
    else:
        total_percent = round(total_correct / total_answers * 100)

    return {
        "students_count": students_count,
        "questions_count": questions_count,
        "total_percent": total_percent,
        "points_sum": points_sum,
        "points_max": max_points * students_count,
        "questions": items,
    }