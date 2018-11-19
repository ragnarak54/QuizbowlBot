import PyPDF2
import re
import random
import question
import json
from html import unescape


def get_questions():
    questionlist = []
    pdf_names = []
    for i in range(1, 9):
        pdf_names.append("Round 0" + str(i) + ".pdf")
    for pdf_name in pdf_names:
        pdf_obj = open(pdf_name, "rb")
        pdf_reader = PyPDF2.PdfFileReader(pdf_obj)
        packet = ""
        for page in range(1, 7):
            page1 = pdf_reader.getPage(page)
            if page == 1:
                arr3 = re.split(r'(1\.\s)', page1.extractText())
                packet = arr3[0].split("-")[0]
                arr3[2] = arr3[1] + arr3[2]
                arr2 = re.split(r'<[A-Z][a-z]*>', arr3[2])

            else:
                arr2 = re.split(r'<[A-Z][a-z]*>', page1.extractText())
            arr2 = arr2[:arr2.__len__()-1]

            for string in arr2:
                split_arr = string.split("ANSWER: ")
                ques = re.split(r'[0-9]\.\s', split_arr[0].replace("\n", ""), maxsplit=1)[1]
                answer = split_arr[1].replace("\n", "")
                if "[" in answer:
                    answer = answer.split("[")[0]
                questionlist.append(question.Question(ques, answer, packet))
    return questionlist


def load_category(cat):
    """Given a category, opens the downloaded archive, serializes the relevant information about tossups, and
    then deserializes it into a new json to be loaded up by the main program"""

    questions = []
    bonuses = []
    with open(cat + 'dl.json', encoding='utf8') as fop:
        data = json.load(fop)
    for tossup in data["data"]["tossups"]:
        questions.append(question.Question(tossup["text"], unescape(tossup["answer"]), cat, tossup["tournament"]["name"],
                                           tossup["formatted_text"], unescape(tossup["formatted_answer"])))
    for bonus in data["data"]["bonuses"]:
        for i in range(0, 3):
            bonus["formatted_answers"][i] = unescape(bonus["formatted_answers"][i])
            bonus["answers"][i] = unescape(bonus["answers"][i])
        bonuses.append(question.Bonus(bonus["leadin"], bonus["texts"], bonus["answers"], cat, bonus["tournament"]["name"],
                                      bonus["formatted_texts"], bonus["formatted_answers"]))
    q_list = [obj.__dict__ for obj in questions]
    b_list = [obj.__dict__ for obj in bonuses]
    final = {"tossups": q_list,
             "bonuses": b_list}
    with open(cat + '.json', 'w', encoding='utf8') as fop:
        json.dump(final, fop)


def get_ms_qs():
    questionlist = []
    pdf_names = []
    for year in range(2010, 2013):
        for i in range(1, 11):
            # pdf_names.append("round" + str(i) + ".txt")
            filename = "/round" + str(i) + ".txt"
            with open("MS/" + str(year) + filename) as f:
                text = f.read()
            if year == 2010:
                packet = text.split("Round")[0].split("Tossups")[1]
            else:
                packet = text.split("Round")[0]
            text = '1. '.join(re.split(r'1\.\s', text)[1:])
            text = "1. " + text
            text = text.split("Bonuses")[0]
            questions = re.split(r'[0-9]+\.\s', text)[1:]
            m = re.search(r'[0-9]+\.\s.*', text)
            while m:
                print(m.group())
                q = re.split(r'[0-9]+\.\s', m.group().split("ANSWER: ")[0])[1]
                a = m.group().split("ANSWER:")[1].strip()
                if '[' in a:
                    a = a.split('[')[0].strip()
                questionlist.append(question.Question(q, a, None, packet))
                text = text.replace(m.group(), "")

                m = re.search(r'[0-9]+\.\s.*', text)
            print("Packet " + str(i) + " complete!")
        print("year " + str(year) + " complete!")

    dick_list = [obj.__dict__ for obj in questionlist]
    with open('test2.json', 'w') as f:
        json.dump(dick_list, f)
    return questionlist
load_category("geography")
# exit(0)
# with open('artdl.json', encoding='utf8') as f:
#     print(json.load(f)["data"]["tossups"][0]["formatted_text"][0])
# exit(0)
# dick_list = [obj.__dict__ for obj in get_geo_qs()]
# with open('test3.json', 'w', encoding='utf8') as file:
#     json.dump(dick_list, file)
#
# dick_list = [obj.__dict__ for obj in get_art_qs()]
# with open('art.json', 'w', encoding='utf8') as file:
#     json.dump(dick_list, file)
#
# with open('art.json', 'r', encoding='utf8') as f:
#     decoded = json.loads(f.read())
#
# print(decoded[0])
