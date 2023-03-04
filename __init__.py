from mycroft import MycroftSkill, intent_handler
from adapt.intent import IntentBuilder
from mycroft.util import LOG
# import removes_context
from mycroft.skills.context import removes_context
import time
import cv2
from cv2 import detail_ImageFeatures
import os
import sys
from multiprocessing import Process, Queue
import csv
import json
from .cvAPI import getDetail, getObjLabel


LOGSTR = '********************====================########## '

MODE = 'TEST'
# need to be changed
IMAGE_STORE_PATH = '/opt/mycroft/skills/roy-first-skill-skill/photo/'
# need to be changed
TEST_IMAGE_PATH_MULTI = '/opt/mycroft/skills/roy-first-skill-skill/testPhoto/multi.jpeg'
# need to be changed
TEST_IMAGE_PATH_HAND = '/opt/mycroft/skills/roy-first-skill-skill/testPhoto/2.jpeg'

#========================= new params and functions for case 3 ==============================

CSV_FIELD_NAME = ['objectLabel', 'objectLogo', 'objectText', 'objectColor']
# need to be changed
CSV_FILE_NAME = '/opt/mycroft/skills/roy-first-skill-skill/store/store.csv'

class RoyFirstSkill(MycroftSkill):


    def __init__(self):
        MycroftSkill.__init__(self)
        self.category_str = ''
        self.color_str = ''
        self.brand_str = ''
        self.kw_str = ''
        self.img_multi = ''
        self.img_hand = ''
        self.detail = ''
        self.first_api_call_return = ''
        self.log.info(LOGSTR + "_init_ EasyShoppingSkill")

    # @intent_handler('skill.first.roy.intent')
    # def handle_skill_first_roy(self, message):
    #     self.speak_dialog('skill.first.roy')

    def initialize(self):
        self.reload_skill = False

    def speak_categories(self, first_api_return):
        string = ''
        for obj in first_api_return['objectList']:
            string += obj['name'][0] +' in ' + obj['loc'] + ' '
        self.speak(string, expect_response=True)
    
    @intent_handler('is.there.any.goods.intent')
    def handle_is_there_any_goods(self,message):
        if self.img_multi == '':
            # if self.img_multi == '', 
            # then it means that user hasn't invoked intent(handle_view_goods)
            self.handle_no_context1(message)
        else:
            # use try-catch block here, since there maybe error return from the cv api
            try:        
                self.log.info(LOGSTR + 'actual img path')
                self.log.info(self.img_multi)
                if MODE == 'TEST':
                    self.log.info(LOGSTR + 'testing mode, use another image')
                    self.img_multi = TEST_IMAGE_PATH_MULTI
                category_label = message.data.get('category')
                objectlist = getObjLabel.getObjectsThenLabel(self.img_multi)
                # label_list = [['milk','drink','bottle'], ['milk','drink','bottle']]
                # loc_list = ['left top','right top']
                label_list = []
                loc_list = []
                detected = False

                # for obj in objectlist['objectList']:
                #     label_list.append(obj['name'])
                #     loc_list.append(obj['loc'])
                for obj in self.first_api_call_return['objectList']:
                    label_list.append(obj['name'])
                    loc_list.append(obj['loc'])

                for i  in range(len(label_list)):
                    label_str = (label_list[i])
                    # label_str = label_str.lower()
                    if category_label is not None:
                        if category_label in label_str:
                                self.speak_dialog('yes.goods',
                                            {'category': category_label,
                                            'location': loc_list[i]})
                                detected = True
                                break
                    else:
                        continue
                if detected == False:
                    self.speak_dialog('no.goods',
                    {'category': category_label})

            except Exception as e:
                self.log.error((LOGSTR + "Error: {0}").format(e))
                self.speak_dialog(
                "exception", {"action": "calling computer vision API"})

        # str = 'yes i find ' + category_label + ' in front of you'
        # self.speak(str)
        # self.speak_dialog('take.photo')
        # self.speak_dialog('yes.goods',{'category':category_label, 'location': 'top left'})

    @intent_handler(IntentBuilder('AskItemBrand').require('Brand').build())
    def handle_ask_item_brand(self,message):
        self.speak('I am talking about the brand of the item')

    @intent_handler('view.goods.intent')
    def handle_view_goods(self, message):
        self.speak_dialog('take.photo')
        self.img_multi = ''
        self.img_hand = ''
        # step 1.2: create another process to do the photo taking
        img_queue = Queue()
        take_photo_process = Process(target=take_photo, args=(img_queue,))
        take_photo_process.daemon = True
        take_photo_process.start()
        take_photo_process.join()
        self.img_multi = img_queue.get()

        self.first_api_call_return = getObjLabel.getObjectsThenLabel(self.img_multi)
        objectNum = self.first_api_call_return['objectNum']
        if objectNum >= 5:
            self.speak('I find some goods here, you can ask me whatever goods you want.', expect_response=True)
        else:
            self.speak('I find some goods here, they are')
            self.speak_categories(self.first_api_call_return)
            self.handle_is_there_any_goods(message)

    @intent_handler(IntentBuilder('AskItemBrand').require('Brand').require('getDetailContext').build())
    def handle_ask_item_brand(self, message):
        self.handle_ask_item_detail('brand', self.brand_str)

    @intent_handler(IntentBuilder('ViewItemInHand').require('ViewItemInHandKeyWord'))
    def handle_view_item_in_hand(self, message):
        self.speak_dialog('take.photo')
        self.img_multi = ''
        self.img_hand = ''

        # create another process to do the photo taking
        img_queue = Queue()
        take_photo_process = Process(target=take_photo, args=(img_queue,))
        take_photo_process.daemon = True
        take_photo_process.start()
        take_photo_process.join()
        self.img_hand = img_queue.get()

        # call cv api, and get result. 
        try:
            self.log.info(LOGSTR + 'actual img path')
            self.log.info(self.img_hand)
            if MODE == 'TEST':
                self.log.info(LOGSTR + 'testing mode, use another image')
                self.img_hand = TEST_IMAGE_PATH_HAND

            detail = getDetail(self.img_hand)
            self.detail = detail

            self.category_str = generate_str(detail['objectLabel'])

            if self.category_str != '':
                self.set_context('getDetailContext')
                self.speak_dialog(
                    'item.category', {'category': self.category_str}, expect_response=True)

                self.brand_str = generate_str(detail['objectLogo'])

                color_list = []
                for color in detail['objectColor']:
                    color_list.append(color['colorName'])
                self.color_str = generate_str(color_list)

                self.kw_str = ' '.join(detail['objectText'])

            else:
                self.clear_all()
                self.remove_context('getDetailContext')
                self.speak(
                    'I cannot understand what is in your hand. Maybe turn around it and let me see it again', expect_response=True)
                
        except Exception as e:
            self.log.error((LOGSTR + "Error: {0}").format(e))
            self.speak_dialog(
                "exception", {"action": "calling computer vision API"})


    @intent_handler(IntentBuilder('AskItemCategory').require('Category').require('getDetailContext').build())
    def handle_ask_item_category(self, message):
        self.handle_ask_item_detail('category', self.category_str)

    @intent_handler(IntentBuilder('AskItemColor').require('Color').require('getDetailContext').build())
    def handle_ask_item_color(self, message):
        self.handle_ask_item_detail('color', self.color_str)

    @intent_handler(IntentBuilder('AskItemBrand').require('Brand').require('getDetailContext').build())
    def handle_ask_item_brand(self, message):
        self.handle_ask_item_detail('brand', self.brand_str)

    @intent_handler(IntentBuilder('AskItemKw').require('Kw').require('getDetailContext').build())
    def handle_ask_item_keywords(self, message):
        self.handle_ask_item_detail('keyword', self.kw_str)

    @intent_handler(IntentBuilder('AskItemInfo').require('Info').require('getDetailContext').build())
    def handle_ask_item_complete_info(self, message):
        self.handle_ask_item_detail('info', self.category_str)

    @intent_handler(IntentBuilder('FinishOneItem').require('Finish').require('getDetailContext').build())
    @removes_context('getDetailContext')
    def handle_finish_current_item(self, message):
        if self.detail != '':
            write_to_csv(self.detail)
            self.speak('Got you request. Let\'s continue shopping!')
            self.clear_all()
        else:
            self.speak('Sorry, I don\'t understand')
    
    @intent_handler(IntentBuilder('NoContext').one_of('Category', 'Color', 'Brand', 'Kw', 'Info'))
    def handle_no_context2(self, message):
        self.speak('Please let me have a look at what\'s in your hand first.')

    @intent_handler('not.take.item.intent')
    @removes_context('getDetailContext')
    def handle_finish_current_item_not_take(self, message):
        if self.img_hand != '':
            self.speak('Don\'t put it into cart. Let\'s continue shopping!')
            self.clear_all()
        else:
            self.speak('Sorry, I don\'t understand')


    @intent_handler('have.bought.intent')
    def handle_have_bought(self, message):
        ask_category = message.data.get('category')
        category_detail = check_category_in_csv(ask_category)
        if category_detail: 
            # dic is not empty
            tell_detail = self.ask_yesno('do.you.want.to.know.detail.about.you.have.bought')

            if tell_detail == 'yes':
                this_category_str = generate_str(string_to_array(category_detail['objectLabel']))
                this_brand_str = generate_str(string_to_array(category_detail['objectLogo']))
                this_color_str = generate_str(get_color_array(category_detail['objectColor']))
                this_kw_str = ' '.join(string_to_array(category_detail['objectText']))

                self.speak_dialog('item.complete.info', {'category': this_category_str})
                self.handle_ask_item_detail('color', this_color_str)
                self.handle_ask_item_detail('brand', this_brand_str)
                self.handle_ask_item_detail('keyword', this_kw_str)
            else:
                self.speak('OK, I won\'t say details.')

        else:
            # dic is empty
            self.speak_dialog('do.not.bought.item', {'category': ask_category})

    def handle_no_context1(self, message):
        self.speak('Please let me have a look at what\'s in front of you first.')
        # add prompts
        take_photo = self.ask_yesno('do.you.want.to.take.a.photo') # This calls .dialog file.
        if take_photo == 'yes':
            self.handle_view_goods(message)
        elif take_photo == 'no':
            self.speak('OK. I won\'t take photo')
        else:
            self.speak('I cannot understand what you are saying')

    def handle_ask_item_detail(self, detail, detail_str):
        if detail_str == '':
            self.speak_dialog(
            'cannot.get', {'detail': detail}, expect_response=True)
        else:
            dialog_str = 'item.' + detail
            self.speak_dialog(dialog_str, {detail: detail_str}, expect_response=True)

    def clear_all(self):
        self.types_str = ''
        self.color_str = ''
        self.logo_str = ''
        self.kw_str = ''
        self.img_hand = ''
        self.img_multi = ''
        self.detail = ''
        self.first_api_call_return = ''



def create_skill():
    return RoyFirstSkill()


def generate_str(possible_list):
    '''
    Generate string for Mycroft to speak it
    Args: 
        possible_list: array list with len = 3, each element is a string
    Returns:
        a string, e.g. possible_list = ['a', 'b', 'c'], res = 'a, b, and c'
    '''
    res = ''
    if len(possible_list) == 3:
        res = possible_list[0] + ' ' + \
            possible_list[1] + ' and ' + possible_list[2]
    elif len(possible_list) == 2:
        res = possible_list[0] + ' and ' + possible_list[1]
    elif len(possible_list) == 1:
        res = possible_list[0]

    return res


def take_photo(img_queue):
    '''
    Do taking photo
    '''
    LOG.info(LOGSTR + 'take photo process start')
    cap = cv2.VideoCapture(0)
    img_name = 'cap_img_' + str(time.time()) + '.jpg'
    img_path = IMAGE_STORE_PATH + img_name

    #<-- Take photo in specific time duration -->
    cout = 0
    while True:
        ret, frame = cap.read()
        cv2.waitKey(1)
        cv2.imshow('capture', frame)
        cout += 1 
        if cout == 50:
            img_queue.put(img_path)
            cv2.imwrite(img_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()
    LOG.info(LOGSTR + 'take photo process end')
    os._exit(0)

def write_to_csv(row):
    with open(CSV_FILE_NAME, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELD_NAME)
        writer.writerow(row)
        f.close()

def check_category_in_csv(category):
    with open(CSV_FILE_NAME, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            categorys = string_to_array(row['objectLabel'])
            categorys = [ele.lower() for ele in categorys]
            if category in categorys:
                return row
        return {}

def string_to_array(s):
    s_ws_bracket = s[2:-2]
    s_w_comma = s_ws_bracket.replace('\', \'', ',')
    return s_w_comma.split(',')


def get_color_array(s):
    s_ws_bracket = s[1:-1]
    if not s_ws_bracket:
        return []
    s_array = s_ws_bracket.split('}, {')
    res = []
    for ele in s_array:
        if ele[0] != '{':
            ele = '{' + ele
        if ele[-1] != '}':
            ele = ele + '}'
        ele = ele.replace('\'', '"')
        ele_json = json.loads(ele)
        res.append(ele_json['colorName'])
    return res