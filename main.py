
import json

import os.path

import asyncio
import threading

from time import sleep

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1wj3WwtE86xgfeJSAIOVXx-cFHX6TAveR4nUsE1Zw170'

creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, User, __version__

from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters,\
    CallbackQueryHandler, ConversationHandler, Updater


TOKEN=None
with open('telegram_token.txt', 'r') as f:
    TOKEN=f.read()

DEMO_TOKEN='5629385379:AAFOTrjhLdi_YjyphxKX871SRT-O4qrvUwk'

UNAUTHORIZED, MENU, PASSPORT, TEAM, TASKS, CONTACTS, PROJECT, CHATS, RESET, CAMERAS, PHOTO_REPORT, SKETCHES, CHART = range(13)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
#keyboards
MENU_KEYBOARD=[
        [InlineKeyboardButton("Паспорт объекта", callback_data=PASSPORT)],
        [InlineKeyboardButton("Проект", callback_data=PROJECT)],
        [InlineKeyboardButton("Мои задачи", callback_data=TASKS)],
        [InlineKeyboardButton("Команда", callback_data=TEAM)],
        [InlineKeyboardButton("Чаты", callback_data=CHATS)],
        [InlineKeyboardButton("Сбросить бота", callback_data=RESET)]
]

MENU_BUTTON=[
        [InlineKeyboardButton("Главное меню", callback_data=MENU)],
]



def get_team():
    team_json={}
    with open('team.json', 'r') as f:
        team_json = json.load(f)
    return team_json

def get_column_by_name(head_row, column_name):
    search_row=[i.replace(' ','') for i in head_row]
    search_query=column_name.replace(' ','')
    return search_row.index(search_query)

def parse_columns(sheet_name,column_name):
    columns_raw = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                  range=sheet_name).execute()
    columns_raw = columns_raw.get('values', [])
    column_id = get_column_by_name(columns_raw[0],column_name)
    baked_columns = [columns_raw[i][column_id] for i in range(len(columns_raw)) if column_id<len(columns_raw[i])]
    return baked_columns[1:]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    team = get_team()

    if not (update.effective_chat.id in team.values()):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите своё имя и фамилию")
        return UNAUTHORIZED

    reply_markup = InlineKeyboardMarkup(MENU_KEYBOARD)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!",reply_markup=reply_markup)
    return MENU

async def authorization(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_creds=update.message.text
    team=parse_columns('Команда','ФИО')
    if user_creds in team[1:]:
        team_json=get_team()
        team_json[user_creds] = update.effective_chat.id
        with open('team.json', 'w') as f:
            f.write(json.dumps(team_json))

        reply_markup = InlineKeyboardMarkup(MENU_KEYBOARD)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="OK",
                                       reply_markup=reply_markup)
        return MENU
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="NO SUCH USER")
        return UNAUTHORIZED


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = InlineKeyboardMarkup(MENU_KEYBOARD)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выбери из списка",reply_markup=reply_markup)
    return MENU

async def passport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = InlineKeyboardMarkup(MENU_BUTTON)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="passport",
                                   reply_markup=reply_markup)
    return PASSPORT


async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    COLUMNS=['Статус','Описание','Дата начала','Дедлайн','Дата окончания','Ответственный']


    query_role=update.callback_query.data
    tasks_raw = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                   range='Задачи').execute()
    tasks_raw = tasks_raw.get('values', [])
    tasks = [tasks_raw[i] for i in range(1, len(tasks_raw))]
    # for i in tasks:

    team_json = get_team()

    receiver_name=''
    for i in team_json:
        if team_json[i]==update.effective_chat.id:
            receiver_name=i


    reply_markup = InlineKeyboardMarkup(MENU_BUTTON)

    user_tasks=[]
    for i in tasks:
        if receiver_name in i:
            user_tasks.append(i)
    for i in range(len(user_tasks)):
        message=''
        for j in range(len(COLUMNS)):
            column_id=get_column_by_name(tasks_raw[0],COLUMNS[j])
            message += '<b>' + COLUMNS[j] + '</b>' + ': '
            if column_id<len(user_tasks[i]):
                message+=user_tasks[i][column_id]
            message += '\n'
        if i==len(user_tasks)-1:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message, reply_markup=reply_markup,parse_mode='HTML')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='HTML')

    if len(user_tasks)==0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Нет задач',
                                       reply_markup=reply_markup, parse_mode='HTML')

    return MENU

async def team(update: Update, context: ContextTypes.DEFAULT_TYPE):
    roles_raw=parse_columns('Команда','Роль')
    roles = [*set([i for i in roles_raw])]

    keyboard = []
    for i in roles:
        keyboard.append([InlineKeyboardButton(i,callback_data=i)])
    keyboard.append([InlineKeyboardButton("Главное меню", callback_data=MENU)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Выбери из списка:', reply_markup=reply_markup)
    return TEAM

async def role_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    COLUMNS=['ID','ФИО','Роль','Телефон']
    query_role=update.callback_query.data
    roles_raw = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                   range='Команда').execute()
    roles_raw = roles_raw.get('values', [])
    roles = [roles_raw[i] for i in range(1, len(roles_raw))]

    employees=[]
    for i in roles:
        if query_role in i:
            employees.append(i)
    for i in range(len(employees)):
        message=''
        for j in range(len(COLUMNS)):
            column_id = get_column_by_name(roles_raw[0], COLUMNS[j])
            message+='<b>'+COLUMNS[j]+'</b>'+': '
            if column_id<len(employees[i]):
                message += employees[i][column_id]
            message+='\n'
        if i==len(employees)-1:
            reply_markup = InlineKeyboardMarkup(MENU_BUTTON)
            await context.bot.send_message(chat_id=update.effective_chat.id,reply_markup=reply_markup,text=message,parse_mode='HTML')
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,text=message,parse_mode='HTML')

    return MENU

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('team.json', 'w') as f:
        f.write('{}')
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Введите своё имя и фамилию')
    return UNAUTHORIZED

# "\u041f\u0443\u0448\u043e\u0432\u0438\u0447"
async def job_monitor(context: ContextTypes.DEFAULT_TYPE):
    COLUMNS = ['Статус', 'Описание', 'Дата начала', 'Дедлайн', 'Дата окончания', 'Ответственный']
    team = get_team()
    tasks_raw = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range='Задачи').execute()
    tasks_raw = tasks_raw.get('values', [])
    tasks = [tasks_raw[i] for i in range(1, len(tasks_raw))]
    for i in tasks:
        members=[]

        notification_column=get_column_by_name(tasks_raw[0],'Пора отправить напоминание')
        if (len(i)>notification_column)and(i[notification_column]=='Отправить напоминание'):
            members_column=get_column_by_name(tasks_raw[0],'Ответственный')
            members=i[members_column].split('\n')
        for j in members:
            if j in team.keys():
                message = '<b>ВНИМАНИЕ! Истекает дедлайн задачи!</b>\n'
                for k in range(len(COLUMNS)):
                    column_id=get_column_by_name(tasks_raw[0],COLUMNS[k])
                    message += '<b>' + COLUMNS[k] + '</b>' + ': '
                    if column_id < len(i):
                        message +=i[column_id]
                    message += '\n'
                await context.bot.send_message(chat_id=team[j], text=message,parse_mode='HTML')

if __name__ == '__main__':
    if not os.path.exists('team.json'):
        with open('team.json', 'w') as f:
            f.write('{}')
    application = ApplicationBuilder().token(TOKEN).build()
    updater = application.updater
    queue=application.job_queue
    job_minute = queue.run_repeating(job_monitor, interval=5)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start),MessageHandler(filters.TEXT,start),CallbackQueryHandler(start)],
        states={
            UNAUTHORIZED:[MessageHandler(filters.TEXT,authorization)],
            MENU:[CallbackQueryHandler(menu, pattern="^" + str(MENU) + "$"),
            CallbackQueryHandler(passport, pattern="^" + str(PASSPORT) + "$"),
            CallbackQueryHandler(tasks, pattern="^" + str(TASKS) + "$"),
            CallbackQueryHandler(team, pattern="^" + str(TEAM) + "$"),
            CallbackQueryHandler(reset, pattern="^" + str(RESET) + "$")],
            PASSPORT:[CallbackQueryHandler(menu, pattern="^" + str(MENU) + "$")],
            TEAM:[CallbackQueryHandler(role_info, pattern="^((?!" + str(MENU) + ").)*$"),
                  CallbackQueryHandler(menu, pattern="^" + str(MENU) + "$"),],
            TASKS:[CallbackQueryHandler(menu, pattern="^" + str(MENU) + "$")],
            CONTACTS:[],

        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)

    application.run_polling()
