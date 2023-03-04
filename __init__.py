from mycroft import MycroftSkill, intent_file_handler, intent_handler, IntentBuilder


class RoyFirstSkill(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('skill.first.roy.intent')
    def handle_skill_first_roy(self, message):
        self.speak_dialog('skill.first.roy')
    
    # @intent_handler('is.there.any.good.intent')
    # def handle_is_there_any_goods(self,message):
    #     category_label = message.data.get('category')
    #     str = 'yes i find ' + category_label + ' in front of you'
    #     # self.speak(str)
    #     self.speak_dialog('take.photo')

    # @intent_handler(IntentBuilder('AskItemBrand').require('brand').build())
    # def handle_ask_item_brand(self,message):
    #     self.speak('I am talking about the brand of the item')


def create_skill():
    return RoyFirstSkill()

