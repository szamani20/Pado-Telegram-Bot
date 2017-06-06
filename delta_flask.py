import json
import os

import redis
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from werkzeug.utils import secure_filename

from delta_bot_shared_values import *
from delta_farsi_sentences import *
from delta_settings import UPLOAD_FOLDER
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply

import threading
from delta_keyboard_actions import *
import telepot
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://szamani:katykaty@localhost:5432/deltabot'
app.config['SECRET_KEY'] = "random string"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
redis_db = redis.StrictRedis(host="localhost", port=6379, db=0)


class Category(db.Model):
    id = db.Column('category_id', db.Integer, primary_key=True)
    category_title = db.Column(db.String(100))
    category_specification = db.Column(db.String(250))
    gifts = db.relationship('Gift', backref='category', lazy='dynamic')


class Gift(db.Model):
    id = db.Column('gift_id', db.Integer, primary_key=True)
    gift_title = db.Column(db.String(100))
    gift_specification = db.Column(db.String(250))
    gift_price = db.Column(db.String(100))
    gift_image = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'))


class Sell(db.Model):
    sell_id = db.Column('sell_id', db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer)
    gift_id = db.Column(db.Integer)
    sell_price = db.Column(db.String(100))
    sell_description = db.Column(db.String(250), default='')
    sell_image = db.Column(db.String(100), default='')
    sell_address = db.Column(db.String(250), default='')
    # more to go


class Customer(db.Model):
    id = db.Column('customer_id', db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_family = db.Column(db.String(100), default='')
    customer_phone = db.Column(db.String(20), default='')
    tg_id = db.Column(db.String(20))
    tg_name = db.Column(db.String(50))
    tg_family = db.Column(db.String(50), default='')
    tg_username = db.Column(db.String(50), default='')


class UserRedisInfo:
    def __init__(self, categories_slide_number, price_oriented_slide_number, new_gifts_slide_number=0):
        self.categories_slide_number = categories_slide_number
        self.price_oriented_slide_number = price_oriented_slide_number
        self.new_gifts_slide_number = new_gifts_slide_number


class DatabaseRedisInfo:
    def __init__(self, gifts, categories):  # key ==> 'DatabaseRedisInfo'
        self.gifts = gifts
        self.categories = categories
        self.gifts_sorted = sorted(gifts, key=lambda x: int(x.gift_price[:-1]))


def create_initial_redis_info(dri):
    csn_dict = dict()
    for c in dri.categories:
        csn_dict[str(c.id)] = 0
    posn_list = [0] * price_oriented_constant
    r = UserRedisInfo(csn_dict, posn_list)
    return json.dumps(r.__dict__)
    # return json.JSONEncoder().encode(r.__dict__)


def new_gifts_result(msg, dri, next_gifts=False, category_id=None, price_oriented=False, price_index=None):
    chat_id = str(msg['from']['id'])

    if category_id:
        callback_data = 'next_' + str(category_id)
    elif price_oriented:
        callback_data = 'nextoriented_' + str(price_index)
    else:
        callback_data = 'next'

    redis_info = redis_db.get(chat_id)
    if redis_info is None:
        redis_info = create_initial_redis_info(dri)
        redis_db.set(chat_id, redis_info)
    if type(redis_info) != str:
        redis_info = redis_info.decode('utf-8')
    print(str(redis_info))
    r = UserRedisInfo(**json.loads(str(redis_info)))

    if not next_gifts and not price_oriented and category_id is None:
        r.new_gifts_slide_number = 0
    if not next_gifts and not price_oriented and category_id is not None:
        r.categories_slide_number[category_id] = 0
    if not next_gifts and price_oriented:
        r.price_oriented_slide_number[price_index] = 0

    if category_id:
        c_gifts = [g for g in dri.gifts if str(g.category_id) == str(category_id)]
        gifts = c_gifts[-(new_gifts_count_constant + r.categories_slide_number[category_id]):
        len(c_gifts) - r.categories_slide_number[category_id]]
    elif price_oriented:
        gifts = dri.gifts[-(new_gifts_count_constant + r.price_oriented_slide_number[price_index]):
        len(dri.gifts) - r.price_oriented_slide_number[price_index]]
    else:
        gifts = dri.gifts[-(new_gifts_count_constant + r.new_gifts_slide_number):
        len(dri.gifts) - r.new_gifts_slide_number]
    images = [i.gift_image for i in gifts]

    if len(gifts) == 0:
        bot.sendMessage(chat_id, finished_fa)

    for i in range(len(gifts)):
        if i == len(gifts) - 1:
            keyboard = [[InlineKeyboardButton(text=gift_fa,
                                              callback_data=str(gifts[i].id)),
                         InlineKeyboardButton(text=next_fa,
                                              callback_data=callback_data)]]
        else:
            keyboard = [[InlineKeyboardButton(text=gift_fa,
                                              callback_data=str(gifts[i].id))]]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        bot.sendPhoto(chat_id, open(app.config['UPLOAD_FOLDER'] + str(gifts[i].category_id) + '/' + images[i], 'rb'),
                      caption=str(gifts[i].gift_specification) + '\n' + str(gifts[i].gift_price), reply_markup=markup)

    if category_id:
        if len(gifts) == 0:
            r.categories_slide_number[category_id] = 0
        r.categories_slide_number[category_id] += len(gifts)
    elif price_oriented:
        if len(gifts) == 0:
            r.price_oriented_slide_number[price_index] = 0
        r.price_oriented_slide_number[price_index] += len(gifts)
    else:
        if len(gifts) == 0:
            r.new_gifts_slide_number = 0
        r.new_gifts_slide_number += len(gifts)

    redis_db.set(chat_id, json.JSONEncoder().encode(r.__dict__))


def categories_result(msg, dri):
    chat_id = str(msg['from']['id'])
    categories = dri.categories
    keyboard = []
    twos = False
    for i in range(len(categories)):
        if twos:
            twos = not twos
            continue
        if i < len(categories) - 1:
            keyboard.append([
                KeyboardButton(text=categories[i].category_title),
                KeyboardButton(text=categories[i + 1].category_title)])
            twos = True
        else:
            keyboard.append([KeyboardButton(text=categories[i].category_title)])
    keyboard.append([KeyboardButton(text=to_main_menu_fa)])

    markup = ReplyKeyboardMarkup(keyboard=keyboard,
                                 resize_keyboard=True,
                                 one_time_keyboard=True)
    bot.sendMessage(chat_id, please_choose_fa, reply_markup=markup)


def price_oriented_result(msg, dri):
    chat_id = str(msg['from']['id'])
    gifts = dri.gifts_sorted
    keyboard = []
    min_price, price_domain = price_domain_helper(gifts)
    for i in range(price_oriented_constant):
        keyboard.append([
            KeyboardButton(text=price_range_fa.format(str(int(i * price_domain) + min_price),
                                                      str(int((i + 1) * price_domain) + min_price)))
        ])
    keyboard.append([KeyboardButton(text=to_main_menu_fa)])

    markup = ReplyKeyboardMarkup(keyboard=keyboard,
                                 resize_keyboard=True,
                                 one_time_keyboard=True)
    bot.sendMessage(chat_id, please_choose_fa, reply_markup=markup)


def price_domain_helper(gifts):
    min_price = int(gifts[0].gift_price[:-1])
    max_price = int(gifts[len(gifts) - 1].gift_price[:-1])
    price_domain = int((max_price - min_price) / price_oriented_constant)

    return min_price, price_domain


def about_us_result(msg, dri=None):
    chat_id = msg['from']['id']
    bot.sendMessage(chat_id, about_us_text_fa)


def check_customer_database(msg):
    chat_id = msg['from']['id']
    customer_name = msg['from']['first_name']
    customer_family = msg['from']['last_name']
    customer_phone = ''
    tg_name = customer_name
    tg_family = customer_family
    tg_username = msg['from']['username']
    if Customer.query.filter_by(tg_id=chat_id).scalar() is not None:
        return
    else:
        c = Customer(customer_name=customer_name,
                     customer_family=customer_family if customer_family is not None else '',
                     customer_phone=customer_phone,
                     tg_id=chat_id,
                     tg_name=tg_name,
                     tg_family=tg_family if tg_family is not None else '',
                     tg_username=tg_username if tg_username is not None else '')

        db.session.add(c)
        db.session.commit()


class VoteCounter(telepot.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(VoteCounter, self).__init__(*args, **kwargs)
        self.reply_keyboard_buttons = [
            {'text': new_gifts_fa, 'action': new_gifts_result},
            {'text': categories_fa, 'action': categories_result},
            {'text': price_oriented_fa, 'action': price_oriented_result},
            {'text': about_us_fa, 'action': about_us_result},
        ]
        self.reply_keyboard_buttons_dict = dict()
        for item in self.reply_keyboard_buttons:
            self.reply_keyboard_buttons_dict[item['text']] = item['action']

        self.list_of_categories = list(Category.query.all())
        self.list_of_gifts = list(Gift.query.all())

        self.dri = DatabaseRedisInfo(self.list_of_gifts, self.list_of_categories)

        self.category_title_id_dict = dict()
        for c in self.list_of_categories:
            self.category_title_id_dict[c.category_title] = c.id
            if not os.path.exists('./static/' + str(c.id)):
                os.makedirs('./static/' + str(c.id))

        self.price_domain_dict = dict()
        min_price, price_domain = price_domain_helper(self.dri.gifts_sorted)
        for i in range(price_oriented_constant):
            self.price_domain_dict[price_range_fa.format(str(int(i * price_domain) + min_price),
                                                         str(int((i + 1) * price_domain) + min_price))] = (
                str(int(i * price_domain) + min_price), str(int((i + 1) * price_domain) + min_price), i)

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(msg)
        print('Chat:', content_type, chat_type, chat_id)

        threading.Thread(target=check_customer_database, args=msg)

        if content_type != 'text':
            return

        if msg['text'] in self.reply_keyboard_buttons_dict:
            print('here')
            action_method = self.reply_keyboard_buttons_dict[msg['text']]
            action_method(msg, self.dri)
        elif msg['text'] in self.category_title_id_dict:
            print('here 2')
            new_gifts_result(msg, self.dri, category_id=self.category_title_id_dict.get(msg['text']))
        elif msg['text'] in self.price_domain_dict:
            print('here 3')
            gifts_ranged = [g for g in self.dri.gifts_sorted if
                            int(self.price_domain_dict[msg['text']][0]) <= int(g.gift_price[:-1]) <=
                            int(self.price_domain_dict[msg['text']][1])]
            gifts_ranged.reverse()
            r2 = DatabaseRedisInfo(gifts_ranged, self.dri.categories.copy())
            price_index = self.price_domain_dict[msg['text']][2]
            for c in r2.gifts:
                print(c.gift_price, end=' ')
            print('\n', price_index)
            new_gifts_result(msg, r2, price_oriented=True, price_index=price_index)
        else:
            markup = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text=new_gifts_fa)],
                [KeyboardButton(text=categories_fa)],
                [KeyboardButton(text=price_oriented_fa)],
                [KeyboardButton(text=about_us_fa)],
            ], resize_keyboard=True, one_time_keyboard=True)
            bot.sendMessage(chat_id, please_choose_fa, reply_markup=markup)

    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)

        if data == 'next':
            new_gifts_result(msg, self.dri, next_gifts=True)
            print('Next')
        elif data.startswith('next_'):
            new_gifts_result(msg, self.dri, next_gifts=True, category_id=data[5:])
        elif data.startswith('nextoriented_'):
            min_price, max_price = 0, 0
            for min_p, max_p, p_index in self.price_domain_dict.values():
                if p_index == int(data[13:]):
                    min_price, max_price = int(min_p), int(max_p)
                    break
            gifts_ranged = [g for g in self.dri.gifts_sorted if
                            min_price <= int(g.gift_price[:-1]) <= max_price]
            gifts_ranged.reverse()
            r2 = DatabaseRedisInfo(gifts_ranged, self.dri.categories.copy())
            for c in r2.gifts:
                print(c.gift_price, end=' ')
            print()
            new_gifts_result(msg, r2, next_gifts=True, price_oriented=True,
                             price_index=int(data[13:]))
        elif data == 'previous':
            print('Previous')


# TOKEN = '216938007:AAH8RyEjdyVzzS6O9i3ExXTaZqX6NCIRZKM'
#
# bot = telepot.DelegatorBot(TOKEN, [
#     include_callback_query_chat_id(
#         pave_event_space())(
#         per_chat_id(), create_open, VoteCounter, timeout=10),
# ])
# MessageLoop(bot).run_as_thread()
# # db.create_all()
# print('Listening ...')
#
# while 1:
#     time.sleep(10)


@app.route('/add_d', methods=['GET'])
def addd():
    db.create_all()
    return 'hellllo'


@app.route('/add_5', methods=['GET'])
def addc():
    c = Category()
    g = Gift()
    c.category_title = category5_fa
    c.category_specification = 'Category Specification 5'
    g.gift_title = 'Gift 11'
    g.gift_specification = 'Gift Specification 11'
    g.gift_price = '260$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 56'
    g2.gift_specification = 'Gift Specification 56'
    g2.gift_price = '420$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 31'
    g3.gift_specification = 'Gift Specification 31'
    g3.gift_price = '310$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 48'
    g4.gift_specification = 'Gift Specification 48'
    g4.gift_price = '100$'
    g4.gift_image = 'img4.jpg'
    g5 = Gift()
    g5.gift_title = 'Gift 48'
    g5.gift_specification = 'Gift Specification 48'
    g5.gift_price = '200$'
    g5.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(g5)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_4', methods=['GET'])
def hello_world():
    c = Category()
    g = Gift()
    c.category_title = category4_fa
    c.category_specification = 'Category Specification 4'
    g.gift_title = 'Gift 1'
    g.gift_specification = 'Gift Specification 1'
    g.gift_price = '20$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 2'
    g2.gift_specification = 'Gift Specification 2'
    g2.gift_price = '230$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 3'
    g3.gift_specification = 'Gift Specification 3'
    g3.gift_price = '110$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 4'
    g4.gift_specification = 'Gift Specification 4'
    g4.gift_price = '56$'
    g4.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_3', methods=['GET'])
def hello_world():
    c = Category()
    g = Gift()
    c.category_title = category3_fa
    c.category_specification = 'Category Specification 3'
    g.gift_title = 'Gift 1'
    g.gift_specification = 'Gift Specification 1'
    g.gift_price = '760$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 2'
    g2.gift_specification = 'Gift Specification 2'
    g2.gift_price = '290$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 3'
    g3.gift_specification = 'Gift Specification 3'
    g3.gift_price = '120$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 4'
    g4.gift_specification = 'Gift Specification 4'
    g4.gift_price = '26$'
    g4.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_2', methods=['GET'])
def addc():
    c = Category()
    g = Gift()
    c.category_title = category2_fa
    c.category_specification = 'Category Specification 2'
    g.gift_title = 'Gift 11'
    g.gift_specification = 'Gift Specification 11'
    g.gift_price = '260$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 56'
    g2.gift_specification = 'Gift Specification 56'
    g2.gift_price = '420$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 31'
    g3.gift_specification = 'Gift Specification 31'
    g3.gift_price = '310$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 48'
    g4.gift_specification = 'Gift Specification 48'
    g4.gift_price = '120$'
    g4.gift_image = 'img4.jpg'
    g5 = Gift()
    g5.gift_title = 'Gift 48'
    g5.gift_specification = 'Gift Specification 48'
    g5.gift_price = '210$'
    g5.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(g5)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/add_1', methods=['GET'])
def hello_world():
    c = Category()
    g = Gift()
    c.category_title = category1_fa
    c.category_specification = 'Category Specification 1'
    g.gift_title = 'Gift 1'
    g.gift_specification = 'Gift Specification 1'
    g.gift_price = '210$'
    g.gift_image = 'img.jpg'
    g2 = Gift()
    g2.gift_title = 'Gift 2'
    g2.gift_specification = 'Gift Specification 2'
    g2.gift_price = '236$'
    g2.gift_image = 'img2.jpg'
    g3 = Gift()
    g3.gift_title = 'Gift 3'
    g3.gift_specification = 'Gift Specification 3'
    g3.gift_price = '10$'
    g3.gift_image = 'img3.jpg'
    g4 = Gift()
    g4.gift_title = 'Gift 4'
    g4.gift_specification = 'Gift Specification 4'
    g4.gift_price = '526$'
    g4.gift_image = 'img4.jpg'
    c.gifts.append(g)
    c.gifts.append(g2)
    c.gifts.append(g3)
    c.gifts.append(g4)
    db.session.add(g)
    db.session.add(g2)
    db.session.add(g3)
    db.session.add(g4)
    db.session.add(c)
    db.session.commit()
    return 'Hello World!'


@app.route('/send_file', methods=['POST'])
def hello_file():
    if 'file' not in request.files:
        print('no file!')
        return 'no file!'
    file = request.files['file']
    if file.filename == '':
        print('no selected file')
        return 'no selected file'
    if file:
        file_name = secure_filename(file.filename)
        print(file_name)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
        print('Nice')
        return 'Nice!'
    return 'dafuq?'


if __name__ == '__main__':
    app.run()
