import datetime as dt
import os

import paho.mqtt.client as mqtt
import telebot
from telebot import types
from dotenv import load_dotenv


load_dotenv()


HOST = os.getenv('HOST')
PORT = int(os.getenv('PORT'))
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
TOPIC = os.getenv('TOPIC')
TOKEN = os.getenv('TOKEN')


tb = telebot.TeleBot(TOKEN)


def parse_message(message):
    message = message.split()
    if not message:
        pass
    chat_id = message[-1]
    if message[0] == 'INFO':
        remain = message[1]
        total = message[2]
        send_info_message(remain, total, chat_id)
        pass
    elif message[0] == 'UPDATED':
        send_success_message(chat_id)
    elif message[0] == 'TAKED':
        remain = message[1]
        send_pill_taked_message(remain, chat_id)



def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(topic=TOPIC)


def on_message(client, userdata, msg):
    message = msg.payload.decode('utf-8')
    print(msg.topic + ' ' + message)
    parse_message(message)


client = mqtt.Client()
client.on_message = on_message
client.on_connect = on_connect


client.connect(host=HOST, port=PORT)
client.username_pw_set(username=USER, password=PASSWORD)
client.subscribe(topic=TOPIC)


@tb.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Информация')
    item2 = types.KeyboardButton('Замена картриджа')
    markup.add(item1, item2)
    tb.send_message(message.chat.id, 'Выберите действие', reply_markup=markup)


@tb.message_handler(content_types=['text'])
def info_message(message):
    if message.text == 'Информация':
        client.publish(TOPIC, f'GET {message.chat.id}', True)
    elif message.text == 'Замена картриджа':
        tb.send_message(message.chat.id,
                        'Сколько таблеток было загружено в картридж?')
        tb.register_next_step_handler(message, reload)
    else:
        tb.send_message(message.chat.id, 'Неизвестная команда')


def send_info_message(remain, total, chat_id):
    tb.send_message(chat_id, f'Осталось {remain} из {total}')


def send_success_message(chat_id):
    tb.send_message(chat_id, 'Информация обновлена успешно')


def send_pill_taked_message(remain, chat_id):
    taked_message = f"""Таблетка принята
Время: {dt.datetime.now().time().isoformat(timespec='minutes')}
Осталось таблеток: {remain}
    """
    tb.send_message(chat_id, taked_message)


def reload(message):
    if reload_is_valid(message):
        client.publish(TOPIC, f'RELOAD {message.text} {message.chat.id}', True)


def reload_is_valid(message):
    not_valid_message = ('Попробуйте вызвать команду снова, введя ' 
                        'число от 1 до 50')
    if not message.text.isdigit():
        tb.send_message(message.chat.id, not_valid_message)
        return False
    elif int(message.text) > 50:
        tb.send_message(message.chat.id, not_valid_message)
        return False
    else:
        return True


client.loop_start()
tb.infinity_polling()
