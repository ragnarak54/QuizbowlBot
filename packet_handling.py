import PyPDF2
import re
import random
import question
import json


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
                q = re.split(r'[0-9]+\.\s', m.group().split("ANSWER:")[0])[1]
                a = m.group().split("ANSWER:")[1]
                if '[' in a:
                    a = a.split('[')[0]
                questionlist.append(question.Question(q, a, packet))
                text = text.replace(m.group(), "")

                m = re.search(r'[0-9]+\.\s.*', text)
            print("Packet " + str(i) + " complete!")
        print("year " + str(year) + " complete!")
    return questionlist


# dick_list = [obj.__dict__ for obj in get_ms_qs()]
# with open('test2.json', 'w') as file:
#     json.dump(dick_list, file)
