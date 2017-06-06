import time
from delta_farsi_sentences import *
from delta_keyboard_actions import *
import telepot
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply

"""
$ python3.5 skeleton_route.py <token>
It demonstrates:
- passing a routing table to `MessageLoop` to filter flavors.
- the use of custom keyboard and inline keyboard, and their various buttons.
Remember to `/setinline` and `/setinlinefeedback` to enable inline mode for your bot.
It works like this:
- First, you send it one of these 4 characters - `c`, `i`, `h`, `f` - and it replies accordingly:
    - `c` - a custom keyboard with various buttons
    - `i` - an inline keyboard with various buttons
    - `h` - hide custom keyboard
    - `f` - force reply
- Press various buttons to see their effects
"""

message_with_inline_keyboard = None


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

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        print('Chat:', content_type, chat_type, chat_id)

        if content_type != 'text':
            return

        if msg['text'] in self.reply_keyboard_buttons_dict:
            print('here')
            action_method = self.reply_keyboard_buttons_dict[msg['text']]
            action_method(msg)
        else:
            markup = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text=new_gifts_fa)],
                [KeyboardButton(text=categories_fa)],
                [KeyboardButton(text=price_oriented_fa)],
                [KeyboardButton(text=about_us_fa)],
            ], resize_keyboard=True, one_time_keyboard=True)
            bot.sendMessage(chat_id, please_choose_fa, reply_markup=markup)

        command = msg['text'][-1:].lower()

        if command == 'c':
            markup = ReplyKeyboardMarkup(keyboard=[
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
                [KeyboardButton(text='sadfsadfdasfdsafdasfsdfdsasalam')],
            ], resize_keyboard=True, selective=True, one_time_keyboard=True)
            # markup = ReplyKeyboardMarkup(keyboard=[
            #     ['Plain text', KeyboardButton(text='Text only')],
            #     [dict(text='Phone', request_contact=True), KeyboardButton(text='Location', request_location=True)],
            # ])
            bot.sendMessage(chat_id, 'Custom keyboard with various buttons', reply_markup=markup)
        elif command == 'i':
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [dict(text='Telegram URL', url='https://core.telegram.org/')],
                [InlineKeyboardButton(text='Callback - show notification', callback_data='notification')],
                [dict(text='Callback - show alert', callback_data='alert')],
                [InlineKeyboardButton(text='Callback - edit message', callback_data='edit')],
                [dict(text='Switch to using bot inline', switch_inline_query='initial query')],
            ])

            global message_with_inline_keyboard
            message_with_inline_keyboard = bot.sendMessage(chat_id, 'Inline keyboard with various buttons',
                                                           reply_markup=markup)
        elif command == 'h':
            markup = ReplyKeyboardRemove()
            bot.sendMessage(chat_id, 'Hide custom keyboard', reply_markup=markup)
        elif command == 'f':
            markup = ForceReply()
            bot.sendMessage(chat_id, 'Force reply', reply_markup=markup)

    def on_callback_query(self, msg):
        query_id, from_id, data = telepot.glance(msg, flavor='callback_query')
        print('Callback query:', query_id, from_id, data)

        if data == 'notification':
            bot.answerCallbackQuery(query_id, text='Notification at top of screen')
        elif data == 'alert':
            bot.answerCallbackQuery(query_id, text='Alert!', show_alert=True)
        elif data == 'edit':
            global message_with_inline_keyboard

            if message_with_inline_keyboard:
                msg_idf = telepot.message_identifier(message_with_inline_keyboard)
                bot.editMessageText(msg_idf, 'NEW MESSAGE HERE!!!!!')
            else:
                bot.answerCallbackQuery(query_id, text='No previous message to edit')


TOKEN = '216938007:AAH8RyEjdyVzzS6O9i3ExXTaZqX6NCIRZKM'

bot = telepot.DelegatorBot(TOKEN, [
    include_callback_query_chat_id(
        pave_event_space())(
        per_chat_id(), create_open, VoteCounter, timeout=10),
])
MessageLoop(bot).run_as_thread()
print('Listening ...')

while 1:
    time.sleep(10)
