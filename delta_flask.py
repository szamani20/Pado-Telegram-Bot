import json
import os

import re
import redis
import time
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from werkzeug.utils import secure_filename

from delta_bot_shared_values import *
from delta_farsi_sentences import *
from delta_settings import UPLOAD_FOLDER, TOKEN
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply

import threading
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
    customer_phone = db.Column(db.String(20))
    gift_id = db.Column(db.Integer)
    gift_amount = db.Column(db.String(10))
    sell_price = db.Column(db.String(100))
    sell_description = db.Column(db.String(250), default='')
    sell_image = db.Column(db.String(100), default='')
    sell_address = db.Column(db.String(250), default='')
    is_final = db.Column(db.Boolean, default=False)
    has_received = db.Column(db.Boolean, default=False)
    # more to go


class Customer(db.Model):
    id = db.Column('customer_id', db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_family = db.Column(db.String(100), default='')
    customer_phone = db.Column(db.String(20), default='')
    destination_address = db.Column(db.String(250), default='')
    pending_order_gift_id = db.Column(db.Integer, nullable=True)
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
                                              callback_data='order_' + str(gifts[i].id)),
                         InlineKeyboardButton(text=next_fa,
                                              callback_data=callback_data)]]
        else:
            keyboard = [[InlineKeyboardButton(text=gift_fa,
                                              callback_data='order_' + str(gifts[i].id))]]
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
            KeyboardButton(text=price_range_fa.format(str(int(i * price_domain) + min_price + i),
                                                      str(int((i + 1) * price_domain) + min_price + i)))
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
    customer_family = msg['from']['last_name'] if 'last_name' in msg['from'] else ''
    customer_phone = ''
    tg_name = customer_name
    tg_family = customer_family
    tg_username = msg['from']['username'] if 'username' in msg['from'] else ''
    if Customer.query.filter_by(tg_id=str(chat_id)).scalar() is not None:
        print('Customer already created :|')
        return
    else:
        c = Customer(customer_name=customer_name,
                     customer_family=customer_family if customer_family is not None else '',
                     customer_phone=customer_phone,
                     tg_id=str(chat_id),
                     tg_name=tg_name,
                     tg_family=tg_family if tg_family is not None else '',
                     tg_username=tg_username if tg_username is not None else '')

        print('Customer created :|')

        db.session.add(c)
        db.session.commit()


def set_customer_phone_number(chat_id, msg):
    c = Customer.query.filter_by(tg_id=str(chat_id)).first()
    if c:
        c.customer_phone = msg['contact']['phone_number']
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
            self.price_domain_dict[price_range_fa.format(str(int(i * price_domain) + min_price + i),
                                                         str(int((i + 1) * price_domain) + min_price + i))] = (
                str(int(i * price_domain) + min_price + i), str(int((i + 1) * price_domain) + min_price + i), i)

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print(msg)
        print('Chat:', content_type, chat_type, chat_id)

        check_customer_database(msg)
        # threading.Thread(target=check_customer_database, args=msg)

        if content_type == 'contact':
            set_customer_phone_number(chat_id, msg)
            c = Customer.query.filter_by(tg_id=str(chat_id)).first()
            if c and c.customer_phone and c.customer_phone != '':
                self.phone_number_confirmed(chat_id, c)
            return
        elif content_type != 'text':
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
        elif msg['text'] == confirm_pending_order_fa:
            print('here 4')
            c = Customer.query.filter_by(tg_id=str(chat_id)).first()
            if c and c.pending_order_gift_id in [g.id for g in self.dri.gifts]:
                self.phone_number_confirmation(chat_id, c.pending_order_gift_id, c)
        elif msg['text'] == cancel_order_fa:
            print('here 5')
            c = Customer.query.filter_by(tg_id=str(chat_id)).first()
            if c and c.pending_order_gift_id is not None:
                c.pending_order_gift_id = None
                db.session.commit()

                markup = ReplyKeyboardMarkup(keyboard=[
                    [KeyboardButton(text=new_gifts_fa)],
                    [KeyboardButton(text=categories_fa)],
                    [KeyboardButton(text=price_oriented_fa)],
                    [KeyboardButton(text=about_us_fa)],
                ], resize_keyboard=True, one_time_keyboard=True)
                bot.sendMessage(chat_id, order_canceled_fa, reply_markup=markup)
        elif msg['text'] == confirm_phone_number_fa:
            c = Customer.query.filter_by(tg_id=str(chat_id)).first()
            if c and c.customer_phone and c.customer_phone != '':
                self.phone_number_confirmed(chat_id, c)
        elif re.match(r'\d{1-4}', msg['text']) is not None:
            c = Customer.query.filter_by(tg_id=str(chat_id)).first()
            self.gift_amount(chat_id, msg['text'], c)
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
        elif data.startswith('order_'):
            self.checkout_order(from_id, int(data[6:]))

    def checkout_order(self, chat_id, gift_id, phone_confirmed=False):
        c = Customer.query.filter_by(tg_id=str(chat_id)).first()
        print(c)

        if not c:
            print('customer is none :|')
            return

        if c.pending_order_gift_id \
                and c.pending_order_gift_id != '':

            gift = None

            for g in self.dri.gifts:
                if c.pending_order_gift_id == g.id:
                    gift = g
                    break

            if gift is None:
                print('no gift matched in dri')
                return

            markup = ReplyKeyboardMarkup(keyboard=
            [
                [KeyboardButton(text=confirm_pending_order_fa)],
                [KeyboardButton(text=cancel_order_fa)],
            ], resize_keyboard=True,
                one_time_keyboard=True)
            bot.sendMessage(chat_id, pending_order_fa.format(c.pending_order_gift_id))
            bot.sendPhoto(chat_id,
                          open(app.config['UPLOAD_FOLDER'] + str(gift.category_id) + '/' + gift.gift_image, 'rb'),
                          caption=str(gift.gift_specification) + '\n' + str(gift.gift_price),
                          reply_markup=markup)
            return
        else:
            c.pending_order_gift_id = gift_id
            db.session.commit()

        if not phone_confirmed:
            self.phone_number_confirmation(chat_id, gift_id, c)

    def phone_number_confirmed(self, chat_id, c):
        if c.pending_order_gift_id \
                and c.pending_order_gift_id != '':

            gift = None

            for g in self.dri.gifts:
                if c.pending_order_gift_id == g.id:
                    gift = g
                    break

            if gift is None:
                return

            bot.sendMessage(chat_id, 'لطفا تناژ مورد نظر را به صورت یک عدد وارد نمایید.',
                            reply_markup=ForceReply())

        else:
            markup = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text=new_gifts_fa)],
                [KeyboardButton(text=categories_fa)],
                [KeyboardButton(text=price_oriented_fa)],
                [KeyboardButton(text=about_us_fa)],
            ], resize_keyboard=True, one_time_keyboard=True)
            bot.sendMessage(chat_id, please_choose_fa, reply_markup=markup)

    def gift_amount(self, chat_id, amount, c):
        if c.pending_order_gift_id \
                and c.pending_order_gift_id != '':

            gift = None

            for g in self.dri.gifts:
                if c.pending_order_gift_id == g.id:
                    gift = g
                    break

            if gift is None:
                return

            markup = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text=new_gifts_fa)],
                [KeyboardButton(text=categories_fa)],
                [KeyboardButton(text=price_oriented_fa)],
                [KeyboardButton(text=about_us_fa)],
            ], resize_keyboard=True, one_time_keyboard=True)

            bot.sendMessage(chat_id, order_done_fa, reply_markup=markup)

            s = Sell()
            s.gift_amount = amount
            s.customer_id = c.id
            s.customer_phone = c.customer_phone
            s.gift_id = gift.id
            s.sell_price = gift.gift_price

            c.pending_order_gift_id = None

            db.session.add(s)
            db.session.commit()

    def phone_number_confirmation(self, chat_id, gift_id, c):
        if c.customer_phone != '':
            markup = ReplyKeyboardMarkup(keyboard=
            [
                [KeyboardButton(text=confirm_phone_number_fa)],
                [KeyboardButton(text=send_phone_fa, request_contact=True)],
                [KeyboardButton(text=cancel_order_fa)],
            ])
            bot.sendMessage(chat_id, phone_number_saved_fa.format(c.customer_phone), reply_markup=markup)
        else:
            keyboard = [
                [KeyboardButton(text=send_phone_fa, request_contact=True)],
                [KeyboardButton(text=cancel_order_fa)],
            ]
            markup = ReplyKeyboardMarkup(keyboard=keyboard,
                                         resize_keyboard=True,
                                         one_time_keyboard=True)
            bot.sendMessage(chat_id, order_text_send_phone_fa.format(str(gift_id)), reply_markup=markup)


bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
        per_chat_id(), create_open, VoteCounter, timeout=10),
])
MessageLoop(bot).run_as_thread()
# db.create_all()
print('Listening ...')

while 1:
    time.sleep(10)
