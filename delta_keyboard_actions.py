import json
import time
from delta_farsi_sentences import *
import telepot
from telepot.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ForceReply
from delta_bot_shared_values import *
from delta_flask import *




def categories_result(msg):
    pass


def price_oriented_result(msg):
    pass


def about_us_result(msg):
    pass
