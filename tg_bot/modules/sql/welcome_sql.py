import threading
from enum import Enum, unique

from sqlalchemy import Column, String, Boolean, UnicodeText, Integer

from tg_bot.modules.sql import SESSION, BASE

DEFAULT_WELCOME = "Hey {first}, how are you?"
DEFAULT_LEAVE = "Nice knowing ya!"


@unique
class Types(Enum):
    TEXT = 0
    BUTTON_TEXT = 1
    STICKER = 2
    DOCUMENT = 3
    PHOTO = 4
    AUDIO = 5
    VOICE = 6
    VIDEO = 7


class Welcome(BASE):
    __tablename__ = "welcome_pref"
    chat_id = Column(String(14), primary_key=True)
    should_welcome = Column(Boolean, default=True)
    custom_welcome = Column(UnicodeText, default=DEFAULT_WELCOME)
    welcome_type = Column(Integer, default=Types.TEXT)
    custom_leave = Column(UnicodeText, default=DEFAULT_LEAVE)
    leave_type = Column(Integer, default=Types.TEXT)

    def __init__(self, chat_id, should_welcome=True):
        self.chat_id = chat_id
        self.should_welcome = should_welcome

    def __repr__(self):
        return "<Chat {} should Welcome new users: {}>".format(self.chat_id, self.should_welcome)


Welcome.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def get_preference(chat_id):
    welc = SESSION.query(Welcome).get(str(chat_id))
    SESSION.close()
    if welc:
        return welc.should_welcome, welc.custom_welcome, welc.custom_leave, welc.welcome_type, welc.leave_type
    else:
        # Welcome by default.
        return True, DEFAULT_WELCOME, DEFAULT_LEAVE


def set_preference(chat_id, should_welcome):
    with INSERTION_LOCK:
        curr = SESSION.query(Welcome).get(str(chat_id))
        if not curr:
            curr = Welcome(str(chat_id), should_welcome)
        else:
            curr.should_welcome = should_welcome

        SESSION.add(curr)
        SESSION.commit()


def set_custom_welcome(chat_id, custom_welcome, welcome_type):
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id), True)

        if custom_welcome:
            welcome_settings.custom_welcome = custom_welcome
            welcome_settings.welcome_type = welcome_type.value

        else:
            welcome_settings.custom_welcome = DEFAULT_LEAVE
            welcome_settings.welcome_type = Types.TEXT

        SESSION.add(welcome_settings)
        SESSION.commit()


def get_custom_welcome(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = DEFAULT_WELCOME
    if welcome_settings and welcome_settings.custom_welcome:
        ret = welcome_settings.custom_welcome

    SESSION.close()
    return ret


def set_custom_leave(chat_id, custom_leave, leave_type):
    with INSERTION_LOCK:
        welcome_settings = SESSION.query(Welcome).get(str(chat_id))
        if not welcome_settings:
            welcome_settings = Welcome(str(chat_id), True)

        if custom_leave:
            welcome_settings.custom_leave = custom_leave
            welcome_settings.leave_type = leave_type.value

        else:
            welcome_settings.custom_leave = DEFAULT_LEAVE
            welcome_settings.leave_type = Types.TEXT

        SESSION.add(welcome_settings)
        SESSION.commit()


def get_custom_leave(chat_id):
    welcome_settings = SESSION.query(Welcome).get(str(chat_id))
    ret = DEFAULT_LEAVE
    if welcome_settings and welcome_settings.custom_leave:
        ret = welcome_settings.custom_leave

    SESSION.close()
    return ret


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Welcome).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
        SESSION.commit()
