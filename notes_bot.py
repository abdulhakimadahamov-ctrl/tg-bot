import telebot
import sqlite3
from dotenv import load_dotenv
import os   

load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))

conn = sqlite3.connect('notes.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT,
        text TEXT
    )
''')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📝 Добавить заметку', '📋 Мои заметки')
    bot.send_message(message.chat.id, 'Привет! Я бот для заметок.', reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle(message):
    chat_id = str(message.chat.id)

    if message.text == '📝 Добавить заметку':
        bot.send_message(message.chat.id, 'Напиши текст заметки:')
        bot.register_next_step_handler(message, save_note)

    elif message.text == '📋 Мои заметки':
        cursor.execute('SELECT id, text FROM notes WHERE chat_id = ?', (chat_id,))
        notes = cursor.fetchall()
        if not notes:
            bot.send_message(message.chat.id, 'У тебя пока нет заметок.')
        else:
            for note in notes:
                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton('Удалить', callback_data=f'delete_{note[0]}'))
                bot.send_message(message.chat.id, f'{note[1]}', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Неизвестная команда.')

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete(call):
    note_id = int(call.data.split('_')[1])
    chat_id = str(call.message.chat.id)
    cursor.execute('DELETE FROM notes WHERE id = ? AND chat_id = ?', (note_id, chat_id))
    conn.commit()
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, 'Заметка удалена.')

def save_note(message):
    chat_id = str(message.chat.id)
    cursor.execute('INSERT INTO notes (chat_id, text) VALUES (?, ?)', (chat_id, message.text))
    conn.commit()
    bot.send_message(message.chat.id, 'Заметка сохранена!')

bot.polling()