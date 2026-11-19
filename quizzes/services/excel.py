from io import BytesIO

from openpyxl import Workbook
from openpyxl.chart import BarChart, DoughnutChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from .stats import get_finish_stats, get_questions_list


TEXT_COLOR = "0D133F"
MUTED_COLOR = "83859F"
HEAD_FILL = "F5F5F8"
BORDER_COLOR = "E2E1EC"

GREEN = "00865F"
RED = "DC3545"
GRAY = "D1D1DB"

GROUP_COLORS = ["00BC7D", "00865F", "767B9C", "FF9B54", "DC3545"]

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

TEXT_ANSWER_SKIPPED = "Пропустив"

TITLE_FONT = Font(size = 16, bold = True, color = TEXT_COLOR)
SUBTITLE_FONT = Font(size = 11, color = MUTED_COLOR)
HEAD_FONT = Font(bold = True, color = TEXT_COLOR)
TEXT_FONT = Font(color = TEXT_COLOR)
QUESTION_FONT = Font(size = 13, bold = True, color = TEXT_COLOR)
CORRECT_FONT = Font(bold = True, color = GREEN)

HEAD_FILL_STYLE = PatternFill("solid", start_color = HEAD_FILL)
THIN = Side(style = "thin", color = BORDER_COLOR)
CELL_BORDER = Border(left = THIN, right = THIN, top = THIN, bottom = THIN)

CENTER = Alignment(horizontal = "center", vertical = "center")


def write_head(sheet, row, column, titles):
    for index, title in enumerate(titles):
        cell = sheet.cell(row = row, column = column + index, value = title)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL_STYLE
        cell.border = CELL_BORDER
        cell.alignment = CENTER


def write_row(sheet, row, column, values):
    for index, value in enumerate(values):
        cell = sheet.cell(row = row, column = column + index, value = value)
        cell.font = TEXT_FONT
        cell.border = CELL_BORDER

    return row


def color_points(series, colors):
    for index, color in enumerate(colors):
        point = DataPoint(idx = index)
        point.graphicalProperties.solidFill = color
        point.graphicalProperties.line.solidFill = "FFFFFF"
        series.dPt.append(point)


def make_doughnut(sheet, labels_column, values_column, first_row, last_row, colors, title):
    chart = DoughnutChart()
    chart.title = title
    chart.holeSize = 65
    chart.width = 9
    chart.height = 7.5

    values = Reference(sheet, min_col = values_column, min_row = first_row, max_row = last_row)
    labels = Reference(sheet, min_col = labels_column, min_row = first_row, max_row = last_row)

    chart.add_data(values, titles_from_data = False)
    chart.set_categories(labels)
    color_points(chart.series[0], colors)

    chart.title.overlay = False
    chart.legend.position = "b"
    chart.legend.overlay = False

    return chart


def count_results(results):
    correct = 0
    wrong = 0
    none = 0

    for result in results:
        if result == "correct":
            correct += 1
        elif result == "wrong":
            wrong += 1
        else:
            none += 1

    return correct, wrong, none


def build_students_sheet(sheet, room, stats):
    sheet.title = "Учні"

    sheet["A1"] = room.quiz.title
    sheet["A1"].font = TITLE_FONT

    subtitle = f"{stats['questions_count']} запитань · {stats['students_count']} учнів"
    if stats["course_name"]:
        subtitle = f"{stats['course_name']} · {subtitle}"

    sheet["A2"] = subtitle
    sheet["A2"].font = SUBTITLE_FONT

    write_head(sheet, 4, 1, ["Ім'я та прізвище", "Бали", "Точність", "Правильні", "Неправильні", "Пропущені"])

    row = 5
    for student in stats["students"]:
        correct, wrong, none = count_results(student["results"])

        write_row(sheet, row, 1, [
            student["name"],
            student["points"],
            student["accuracy"] / 100,
            correct,
            wrong,
            none,
        ])
        sheet.cell(row = row, column = 2).number_format = "#,##0"
        sheet.cell(row = row, column = 3).number_format = "0%"
        row += 1

    sheet["H4"] = "Загальна успішність"
    sheet["H4"].font = HEAD_FONT

    sheet["H5"] = "Середня точність групи"
    sheet["H5"].font = SUBTITLE_FONT
    sheet["I5"] = stats["total_percent"] / 100
    sheet["I5"].number_format = "0%"
    sheet["I5"].font = HEAD_FONT

    sheet["H6"] = f"{stats['total_correct']} із {stats['total_answers']} відповідей — правильні"
    sheet["H6"].font = SUBTITLE_FONT

    write_head(sheet, 8, 8, ["Точність", "Студентів"])

    group_row = 9
    for group in stats["groups"]:
        write_row(sheet, group_row, 8, [group["label"], group["count"]])
        group_row += 1

    chart = make_doughnut(sheet, 8, 9, 9, group_row - 1, GROUP_COLORS, "Розподіл студентів за точністю")
    chart.width = 12
    chart.height = 9
    sheet.add_chart(chart, "K4")

    widths = {"A": 30, "B": 12, "C": 12, "D": 13, "E": 15, "F": 13, "G": 3, "H": 26, "I": 12}
    for letter, width in widths.items():
        sheet.column_dimensions[letter].width = width


def build_question_block(sheet, item, students_count, start_row):
    title_cell = sheet.cell(row = start_row, column = 1, value = f"{item['number']:02d}. {item['text']}")
    title_cell.font = QUESTION_FONT
    title_cell.alignment = Alignment(wrap_text = True, vertical = "center")
    sheet.merge_cells(start_row = start_row, start_column = 1, end_row = start_row, end_column = 18)
    sheet.row_dimensions[start_row].height = 34

    sub_cell = sheet.cell(row = start_row + 1, column = 1, value = f"Середня точність групи: {item['percent']}% вірно")
    sub_cell.font = SUBTITLE_FONT

    table_row = start_row + 3
    write_head(sheet, table_row, 1, ["Результат", "Кількість"])
    write_row(sheet, table_row + 1, 1, ["Не правильно", item["wrong"]])
    write_row(sheet, table_row + 2, 1, ["Без відповіді", item["no_answer"]])
    write_row(sheet, table_row + 3, 1, ["Правильно", item["correct"]])

    donut = make_doughnut(sheet, 1, 2, table_row + 1, table_row + 3, [RED, GRAY, GREEN], f"{item['percent']}% вірно")
    sheet.add_chart(donut, f"D{start_row + 2}")

    list_rows = 0

    if item["is_text"]:
        write_head(sheet, table_row, 10, ["Відповіді учнів"])
        sheet.merge_cells(start_row = table_row, start_column = 10, end_row = table_row, end_column = 13)

        answer_row = table_row + 1

        if not item["text_answers"]:
            sheet.cell(row = answer_row, column = 10, value = "Ще немає відповідей").font = SUBTITLE_FONT
            answer_row += 1

        for answer in item["text_answers"]:
            answer_text = answer["text"]
            if answer["status"] == "none":
                answer_text = TEXT_ANSWER_SKIPPED

            text = answer_text
            if answer["name"]:
                text = f"{answer['name']}: {answer_text}"

            cell = sheet.cell(row = answer_row, column = 10, value = text)
            if answer["status"] == "correct":
                cell.font = Font(color = GREEN)
            elif answer["status"] == "wrong":
                cell.font = Font(color = RED)
            else:
                cell.font = Font(color = MUTED_COLOR)

            sheet.merge_cells(start_row = answer_row, start_column = 10, end_row = answer_row, end_column = 13)
            answer_row += 1

        list_rows = answer_row - table_row
    else:
        write_head(sheet, table_row, 10, ["", "Варіант відповіді", "Голосів", "Правильний"])

        option_row = table_row + 1
        for index, option in enumerate(item["options"]):
            if option["is_correct"]:
                mark = "Так"
            else:
                mark = "Ні"

            write_row(sheet, option_row, 10, [LETTERS[index], option["text"], option["count"], mark])
            option_row += 1

        list_rows = option_row - table_row

        if item["options"]:
            bars = BarChart()
            bars.type = "col"
            bars.title = "Вибір учасників"
            bars.width = 10
            bars.height = 7
            bars.legend = None
            bars.gapWidth = 60
            bars.x_axis.delete = False
            bars.y_axis.delete = False
            bars.y_axis.scaling.min = 0
            bars.y_axis.majorUnit = 1
            bars.title.overlay = False

            if students_count > 0:
                bars.y_axis.scaling.max = students_count

            values = Reference(sheet, min_col = 12, min_row = table_row + 1, max_row = option_row - 1)
            labels = Reference(sheet, min_col = 10, min_row = table_row + 1, max_row = option_row - 1)
            bars.add_data(values, titles_from_data = False)
            bars.set_categories(labels)

            colors = []
            for option in item["options"]:
                if option["is_correct"]:
                    colors.append(GREEN)
                else:
                    colors.append(RED)

            color_points(bars.series[0], colors)

            bars.dataLabels = DataLabelList()
            bars.dataLabels.showVal = True
            bars.dataLabels.showCatName = False
            bars.dataLabels.showSerName = False
            bars.dataLabels.showLegendKey = False

            sheet.add_chart(bars, f"O{start_row + 2}")

    chart_rows = 17
    block_rows = max(chart_rows, 3 + list_rows + 1)

    correct_row = start_row + block_rows
    label = sheet.cell(row = correct_row, column = 1, value = "ПРАВИЛЬНА ВІДПОВІДЬ")
    label.font = CORRECT_FONT

    answer = sheet.cell(row = correct_row + 1, column = 1, value = item["correct_text"])
    answer.font = TEXT_FONT
    sheet.merge_cells(start_row = correct_row + 1, start_column = 1, end_row = correct_row + 1, end_column = 18)

    return correct_row + 4


def build_questions_sheet(sheet, room, data):
    sheet.title = "Запитання"

    sheet["A1"] = room.quiz.title
    sheet["A1"].font = TITLE_FONT

    write_head(sheet, 3, 1, ["Учасники", "Запитань", "Точність групи", "Загальна кількість балів"])
    write_row(sheet, 4, 1, [
        data["students_count"],
        data["questions_count"],
        data["total_percent"] / 100,
        f"{data['points_sum']:,} / {data['points_max']:,}".replace(",", " "),
    ])
    sheet["C4"].number_format = "0%"

    row = 7
    for item in data["questions"]:
        row = build_question_block(sheet, item, data["students_count"], row)

    widths = {"A": 18, "B": 14, "C": 18, "D": 26, "J": 5, "K": 60, "L": 10, "M": 12}
    for letter, width in widths.items():
        sheet.column_dimensions[letter].width = width


def fit_to_page(sheet):
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True


def build_finish_excel(room):
    stats = get_finish_stats(room)
    questions = get_questions_list(room)

    workbook = Workbook()

    build_students_sheet(workbook.active, room, stats)
    build_questions_sheet(workbook.create_sheet(), room, questions)

    for sheet in workbook.worksheets:
        fit_to_page(sheet)

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    return buffer