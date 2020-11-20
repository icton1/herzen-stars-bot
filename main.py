import pymongo
import telebot
import sys
import user_tags

# получить ключи доступа из окружения
if len(sys.argv) < 3:
    print("""Передайте ключи доступа в аргументы команды:
    python3 main.py пароль_от_mongodb токен_доступа_telegram_api\n""")
    sys.exit()
else:
    credentials = {
        "mongodb_password": sys.argv[1],
        "tg_token": sys.argv[2]
    }

# инициализировать бота
bot = telebot.TeleBot(credentials["tg_token"])

# подключить базу данных
cluster = pymongo.MongoClient(
    f"mongodb+srv://icton_bot:{credentials['mongodb_password']}@cluster0.yieez.mongodb.net/Icton?retryWrites=true&w=majority")
db = cluster['Icton']


# получить текст сообщения из БД по его ID
def msg(db_msg_id, mongo_db=db):
    messages = mongo_db['messages']
    return messages.find_one({'_id': db_msg_id})['msg']


@bot.message_handler(commands=['add_tag_to_user'])
def handle_tag_adding_start(tg_message):
    response_msg = send_message(tg_message, "Укажи студента и тэг")
    bot.register_next_step_handler(response_msg, handle_tag_adding_end)


def handle_tag_adding_end(tg_message):
    try:
        message = tg_message.text
        args = message.split(" ")

        if len(args) < 2:
            send_message(tg_message, "Упс, недостаточно аргументов")
            return

        user_tags.add_tag_to_user(args[0], args[1], db)
    except user_tags.UserTagsException as e:
        send_message(tg_message, e.msg)


@bot.message_handler(commands=['get_users_with_tag'])
def handle_users_with_tag_start(tg_message):
    response_msg = send_message(tg_message, "Укажи тэг")
    bot.register_next_step_handler(response_msg, handle_users_with_tag_end)


def handle_users_with_tag_end(tg_message):
    try:
        tag = tg_message.text

        users = user_tags.get_users_with_tag(tag, tg_message.chat, bot, db)

        users_msg = ""

        for user in users:
            user_msg = "@"
            user_msg += str(user.username) + " "
            users_msg += user_msg
        send_message(tg_message, users_msg)

    except user_tags.UserTagsException as e:
        send_message(tg_message, e.msg)


# test run
@bot.message_handler(content_types=['text'])
def send_message(message, text=msg('1')):
    return bot.send_message(message.chat.id, text)


# запустить работу бота в бесконечном цикле
if __name__ == '__main__':
    bot.infinity_polling()