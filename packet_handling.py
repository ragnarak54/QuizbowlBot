import PyPDF2
import re
import random
import question
from fuzzywuzzy import process
from fuzzywuzzy import fuzz


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

#questions = get_questions()
#question_arr = questions[2].question.split(" ")
#sent_question = " ".join(question_arr[:5])
#for i in range(1, question_arr.__len__() // 5):
    #print(sent_question + " ".join(question_arr[i*5:i*5+5]))
    #sent_question += " " + " ".join(question_arr[i*5:i*5+5])



