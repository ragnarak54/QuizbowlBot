class Tossup:
    def __init__(self, text, formatted_answer, category, packet, formatted_question=None):
        self.text = text
        self.formatted_answer = formatted_answer
        self.category = category
        self.packet = packet
        self.formatted_question = formatted_question


class Bonus:
    def __init__(self, leadin, texts, formatted_answers, category, packet, formatted_texts=None):
        self.leadin = leadin
        self.texts = texts
        self.formatted_answers = formatted_answers
        self.category = category
        self.packet = packet
        self.formatted_texts = formatted_texts

