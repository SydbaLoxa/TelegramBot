import os.path
import base64
from time import sleep
from datetime import datetime, time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import telebot
from telebot import types

# Настройки
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TELEGRAM_TOKEN = '8114870676:AAG3HXU-iQDEfgDLyzXSetuQbzvYc696PIM'
CHAT_ID = '1083393440' # ID чата или пользователя для уведомлений
AUTHORIZED_SENDER = "robot@keenetic.cloud" # Авторизованный отправитель
room_status = "Активская закрыта >:("
start_time = time(7, 0)  # 7:00 утра
end_time = time(22, 0)   # 10:00 вечера

# Инициализация бота
# Необходимо создать токен при помощи OAuth2.0, который будет использоваться для GmailAPI
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def check_email():
    global room_status
    creds = authenticate_gmail()
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
        messages = results.get('messages', [])
        
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            
            headers = msg_data['payload']['headers']
            subject = None
            sender = None
            
            for header in headers:
                if header['name'] == 'Subject':
                    subject = header['value']
                elif header['name'] == 'From':
                    sender = header['value']
            
            # Проверяем, что sender и subject не None перед использованием
            if sender and AUTHORIZED_SENDER in sender:
                if subject and "«Keenetic Giga (KN-1010)» > «Keenetic Giga (KN-1010)» запущен" in subject:
                    room_status = "Активская открыта :)"
                    bot.send_message(CHAT_ID, "Активская открыта :)")
                elif subject and "«Keenetic Giga (KN-1010)» > «Keenetic Giga (KN-1010)» офлайн" in subject:
                    room_status = "Активская закрыта >:("
                    bot.send_message(CHAT_ID, "Активская закрыта >:(")

                # Отмечаем письмо как прочитанное
                service.users().messages().modify(
                    userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}
                ).execute()
                
    except HttpError as error:
        print(f'An error occurred: {error}')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Создаем объект клавиатуры
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    check_button = types.KeyboardButton("Открыта?")
    markup.add(check_button)

    # Отправляем приветственное сообщение с клавиатурой
    bot.send_message(
        message.chat.id,
        "Привет! Нажмите кнопку ниже, чтобы проверить статус комнаты.",
        reply_markup=markup
    )

# Обработчик для кнопки "Проверить"
@bot.message_handler(func=lambda message: message.text == "Открыта?")
def check_status(message):
    global room_status
    bot.send_message(message.chat.id, f"{room_status}")
    
# Обработчик команды /check
@bot.message_handler(commands=['check'])
def check_status(message):
    bot.send_message(message.chat.id, f"{room_status}")

# Функция для постоянной проверки почты
def main():
    while True:

        check_email()
        sleep(30)

# Запуск
if __name__ == "__main__":
    bot.send_message(CHAT_ID, "Бот запущен и отслеживает состояние комнаты.")
    import threading
    threading.Thread(target=main).start()
    bot.polling(timeout=30, long_polling_timeout=86400)
