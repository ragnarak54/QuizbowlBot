class Question:
    def __init__(self, question, answer, category, packet, formatted_question=None, formatted_answer=None):
        self.question = question
        self.answer = answer
        self.category = category
        self.packet = packet
        self.formatted_question = formatted_question
        self.formatted_answer = formatted_answer


class Bonus:
    def __init__(self, leadin, texts, answers, category, packet, formatted_texts=None, formatted_answers=None):
        self.leadin = leadin
        self.texts = texts
        self.answers = answers
        self.category = category
        self.packet = packet
        self.formatted_texts = formatted_texts
        self.formatted_answers = formatted_answers

