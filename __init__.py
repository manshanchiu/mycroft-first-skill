from mycroft import MycroftSkill, intent_file_handler


class RoyFirstSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('skill.first.roy.intent')
    def handle_skill_first_roy(self, message):
        self.speak_dialog('skill.first.roy')


def create_skill():
    return RoyFirstSkill()

