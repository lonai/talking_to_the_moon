import logging
import re
import paramiko
import os
import psycopg2

from psycopg2 import Error
from dotenv import load_dotenv
from pathlib import Path
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler


KEY = 1

dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)

token = os.getenv('TOKEN')

connection = None
#keys for bot
host = os.getenv('RM_HOST')
port = os.getenv('RM_PORT')
username = os.getenv('RM_USER')
password = os.getenv('RM_PASSWORD')

#keys for bot_db
host_db = os.getenv('DB_HOST')
port_db = os.getenv('DB_PORT')
username_db = os.getenv('DB_USER')
password_db = os.getenv('DB_PASSWORD')
database = os.getenv('DB_DATABASE')
#keys for repl
host_repl_db = os.getenv('DB_REPL_HOST')
port_repl_db = os.getenv('DB_REPL_PORT')
user_repl_db = os.getenv('DB_REPL_USER')
password_repl_db = os.getenv('DB_REPL_PASSWORD')

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)



#Start and help command
def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Hello bro, {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Сейчас конечно помогу тебе, бро! Смотри список команд, если не поймешь что они делают, просто тыкны и узнаешь.')

    # Список всех зарегистрированных команд бота
    command_list = [f"/{command}" for command in context.bot.commands]

    # Добавляем в список другие команды, которые не были зарегистрированы
    custom_commands = [
    "/find_phone_numbers",
    "/find_email",
    "/verify_password",
    "/get_release",
    "/get_uname",
    "/get_uptime",
    "/get_df",
    "/get_free",
    "/get_mpstat",
    "/get_getw",
    "/get_auths",
    "/get_critical",
    "/get_ps",
    "/get_ss",
    "/get_apt_list",
    "/get_services",
    "/get_repl_logs",
    "/get_emails",
    "/get_phone_numbers"
]

    command_list.extend(custom_commands)

    # Формируем сообщение с перечислением всех команд
    help_message = "Вот и они:\n" + "\n".join(command_list)

    # Отправляем сообщение с помощью
    update.message.reply_text(help_message)

#ssh session
def ssh_connect(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data


#PHONE
def find_phone_numbers_command(update: Update, context):
    update.message.reply_text('Ты вводишь текст, а мы ищем телефонные номера, все просто бро! ')

    return 'find_phone_numbers'

def find_phone_numbers (update: Update, context):
    user_input = update.message.text

    phoneNumRegex = re.compile(r'(?:\+7|8)(?:(?:\(|\ \(|)\d{3}(?:\)|\)\ |)|[- ]?\d{3}[- ]?)(?:\d{3}[- ]?)(?:\d{2}[- ]?)(?:\d{2})')
    phoneNumberList = phoneNumRegex.findall(user_input)

    if not phoneNumberList:
        update.message.reply_text('Упс, а ты точно ввел хоть один номер? Мы не видим.')
        return ConversationHandler.END
    else:
        phoneNumbers = ''
        for i in range(len(phoneNumberList)):
            phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'
        context.user_data[KEY] = phoneNumberList
        update.message.reply_text(phoneNumbers + '\n/yes, чтобы черкануть записи в тетрадь\n/no, для отказа, в этом нет ничего плохого, не дрейфь, бро')
        return 'write_confirm'
def get_phone_numbers(update: Update, context):
    try:
        connection = psycopg2.connect(user=username_db,
                                password=password_db,
                                host=host_db,
                                port=port_db,
                                database=database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phone;")
        data = cursor.fetchall()
        for row in data:
            update.message.reply_text(row)
            #print(row)
        logging.info("Получение phones - УСПЕХ")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END


def write_confirmed_phones(update: Update, context):
    plist = context.user_data.get(KEY, [])
    if len(plist) > 0:
        connection = psycopg2.connect(user=username_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database)

        try:
            cursor = connection.cursor()
            for phone_number in plist:
                cursor.execute("INSERT INTO phone (phone_number) VALUES " + "('" + phone_number + "')" + ";")
            connection.commit()
            logging.info("Команда успешно выполнена")
            update.message.reply_text('Вау! Карандаши былы хорошо заточены, только записи останутся у нас.')
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Что-то пошло не так, карандаши сломались. Записать не получилось. ')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
    else:
        return ConversationHandler.END
    context.user_data[KEY] = None
#PHONE

#MAIL
def find_emails(text):
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_regex, text)
    return emails


def find_email_command(update, context):
    update.message.reply_text('Ты вводишь текст, а мы ищем в нем email-адреса, все просто бро!')
    return 'find_email'

def find_email (update: Update, context):
    user_input = update.message.text

    emailRegex = re.compile(r'[a-zA-Z0-9._-]+@[a-zA-Z0-9-.]+\.[a-zA-Z]{2,}')
    emailList = emailRegex.findall(user_input)

    if not emailList:
        update.message.reply_text('Сорри, бро, email-адреса не найдены:')
        return ConversationHandler.END
    else:
        emails = ''
        for i in range(len(emailList)):
            emails += f'{i+1}. {emailList[i]}\n'
        context.user_data[KEY] = emailList
        update.message.reply_text(emails + '\n/yes, чтобы черкануть записи в тетрадь\n/no, для отказа, в этом нет ничего плохого, не дрейфь, бро')
        return 'write_confirm'


def get_emails (update: Update, context):
    try:
        connection = psycopg2.connect(user=username_db,
                                password=password_db,
                                host=host_db,
                                port=port_db,
                                database=database)

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM email;")
        data = cursor.fetchall()
        for row in data:
            update.message.reply_text(row)
            #print(row)
        logging.info("Выгрузка email из базы данных")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
    return ConversationHandler.END


def write_confirmed_emails(update: Update, context):
    elist = context.user_data.get(KEY, [])
    if len(elist) > 0:
        connection = psycopg2.connect(user=username_db,
                                      password=password_db,
                                      host=host_db,
                                      port=port_db,
                                      database=database)

        try:
            cursor = connection.cursor()
            for email_number in elist:
                cursor.execute("INSERT INTO email (email) VALUES " + "('" + email_number + "')" + ";")
            connection.commit()
            logging.info("Поздравляем! Команда выполнена!")
            update.message.reply_text('Записано, товарищ Адмирал!!Хаха, бро, ну ты чего, когда расход?')
        except (Exception, Error) as error:
            logging.error("Ошибка при работе с PostgreSQL: %s", error)
            update.message.reply_text('Ошибка, данные не были записаны, енот украл наши тетради.')
        finally:
            if connection is not None:
                cursor.close()
                connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
    else:
        return ConversationHandler.END
    context.user_data[KEY] = None

def write_cancelled(update: Update, context):
    context.user_data[KEY] = None
    update.message.reply_text('Отказ от записи, подпишите здесь и здесь.')
    return ConversationHandler.END
#MAIL

#PASS
# Обработчик команды /verify_password
def verify_password_command(update, context):
    update.message.reply_text('Введите пароль для проверки сложности:')
    return 'verify_password'


# Функция для проверки сложности пароля
def verify_password(update, context):
    password = update.message.text

    # Проверка сложности пароля с использованием регулярного выражения
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

    if re.match(password_regex, password):
        update.message.reply_text('Пароль сложный')
    else:
        update.message.reply_text('Пароль простой')

    return ConversationHandler.END
#PASS

#LINUX

#О релизе
def get_release(update: Update, context):
    update.message.reply_text(ssh_connect('lsb_release -a'))
    return ConversationHandler.END

#Об архитектуры процессора, имени хоста системы и версии ядра
def get_uname(update: Update, context):
    update.message.reply_text(ssh_connect('uname -a'))
    return ConversationHandler.END

#О времени работы
def get_uptime(update: Update, context):
    update.message.reply_text(ssh_connect('uptime -p'))
    return ConversationHandler.END

#Сбор информации о состоянии файловой системы
def get_df(update: Update, context):
    update.message.reply_text(ssh_connect('df -ah'))
    return ConversationHandler.END

#Сбор информации о состоянии оперативной памяти
def get_free(update: Update, context):
    update.message.reply_text(ssh_connect('free -wh'))
    return ConversationHandler.END

#Сбор информации о производительности системы
def get_mpstat(update: Update, context):
    update.message.reply_text(ssh_connect('mpstat -P ALL'))
    return ConversationHandler.END

#Сбор информации о работающих в данной системе пользователях
def get_w(update: Update, context):
    update.message.reply_text(ssh_connect('w'))
    return ConversationHandler.END
#Сбор логов
#Последние 10 входов в систему
def get_auths(update: Update, context):
    update.message.reply_text(ssh_connect('tail /var/log/auth.log'))
    return ConversationHandler.END

#Последние 5 критических события
def get_critical(update: Update, context):
    update.message.reply_text(ssh_connect('journalctl -p 2 | tail -n5'))
    return ConversationHandler.END

#Сбор информации о запущенных процессах
def get_ps(update: Update, context):
    update.message.reply_text(ssh_connect('ps -A u | head -n20'))
    return ConversationHandler.END

#Сбор информации об используемых портах
def get_ss(update: Update, context):
    update.message.reply_text(ssh_connect('ss -a | head -n20'))
    return ConversationHandler.END

#Сбор информации об установленных пакетах
def get_apt_list_command(update: Update, context):
    update.message.reply_text(
        'Введите "ALL", чтобы вывести всё \nили же введите имя конкретного пакета')
    return 'get_apt_list'

def get_apt_list(update: Update, context):
    user_input = update.message.text
    if (user_input == 'ALL'):
        update.message.reply_text(ssh_connect('apt list --installed | head -n20'))
    else:
        update.message.reply_text(ssh_connect('apt show ' + user_input))
    return ConversationHandler.END

#Сбор информации о запущенных сервисах
def get_services(update: Update, context):
    update.message.reply_text(ssh_connect('service --status-all'))
    return ConversationHandler.END

#Сбор информации о логах постргрес
def get_repl_logs (update: Update, context):
    connection = psycopg2.connect( host=host_db, port=port_db, database=database, user=username_db, password=password_db )
    cursor = connection.cursor()
    data = cursor.execute("SELECT pg_read_file(pg_current_logfile());")
    data = cursor.fetchall()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    answer = 'А вот и они, ты справился, мы в тебя верили.:\n'

    for str1 in data.split('\n'):
        if user_repl_db in str1:
            answer += str1 + '\n'
    if len(answer) == 17:
        answer = 'Бро, а какие данные то? Ничего не было, воспользуйся сначала командой поиска email, запиши его в бд и попробуй снова!!'
    for x in range(0, len(answer), 4096):
        update.message.reply_text(answer[x:x+4096])

    update.message.reply_text(sshConnectMaster('cat /var/log/postgresql/postgresql-15-main.log | grep repl_user | tail -n20'))
    return ConversationHandler.END
#lINUX

def main():
    updater = Updater(token, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога для поиска телефона
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_numbers', find_phone_numbers_command)],
        states={
            'find_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, find_phone_numbers)],
            'write_confirm': [CommandHandler('yes', write_confirmed_phones), CommandHandler('no', write_cancelled)]
        },
        fallbacks=[]
    )
    # Обработчик диалога для поиска email
    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_email_command)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, find_email)],
            'write_confirm': [CommandHandler('yes', write_confirmed_emails), CommandHandler('no', write_cancelled)]
        },
        fallbacks=[]
    )

    # Регистрируем состояние для проверки сложности пароля в обработчике диалога
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password_command)],
        states={'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)]},
        fallbacks=[]
    )


    convHandlerGetRelease = ConversationHandler(
        entry_points=[CommandHandler('get_release', get_release)],
        states={
            'get_release': [MessageHandler(Filters.text & ~Filters.command, get_release)],
        },
        fallbacks=[]
    )

    convHandlerGetUname = ConversationHandler(
        entry_points=[CommandHandler('get_uname', get_uname)],
        states={
            'get_uname': [MessageHandler(Filters.text & ~Filters.command, get_uname)],
        },
        fallbacks=[]
    )

    convHandlerGetUptime = ConversationHandler(
        entry_points=[CommandHandler('get_uptime', get_uptime)],
        states={
            'get_uptime': [MessageHandler(Filters.text & ~Filters.command, get_uptime)],
        },
        fallbacks=[]
    )

    convHandlerGetDf = ConversationHandler(
        entry_points=[CommandHandler('get_df', get_df)],
        states={
            'get_df': [MessageHandler(Filters.text & ~Filters.command, get_df)],
        },
        fallbacks=[]
    )

    convHandlerGetFree = ConversationHandler(
        entry_points=[CommandHandler('get_free', get_free)],
        states={
            'get_free': [MessageHandler(Filters.text & ~Filters.command, get_free)],
        },
        fallbacks=[]
    )

    convHandlerGetMpstat = ConversationHandler(
        entry_points=[CommandHandler('get_mpstat', get_mpstat)],
        states={
            'get_mpstat': [MessageHandler(Filters.text & ~Filters.command, get_mpstat)],
        },
        fallbacks=[]
    )

    convHandlerGetW = ConversationHandler(
        entry_points=[CommandHandler('get_w', get_w)],
        states={
            'get_w': [MessageHandler(Filters.text & ~Filters.command, get_w)],
        },
        fallbacks=[]
    )

    convHandlerGetAuths = ConversationHandler(
        entry_points=[CommandHandler('get_auths', get_auths)],
        states={
            'get_auths': [MessageHandler(Filters.text & ~Filters.command, get_auths)],
        },
        fallbacks=[]
    )

    convHandlerGetCritical = ConversationHandler(
        entry_points=[CommandHandler('get_critical', get_critical)],
        states={
            'get_critical': [MessageHandler(Filters.text & ~Filters.command, get_critical)],
        },
        fallbacks=[]
    )

    convHandlerGetPs = ConversationHandler(
        entry_points=[CommandHandler('get_ps', get_ps)],
        states={
            'get_ps': [MessageHandler(Filters.text & ~Filters.command, get_ps)],
        },
        fallbacks=[]
    )

    convHandlerGetSs = ConversationHandler(
        entry_points=[CommandHandler('get_ss', get_ss)],
        states={
            'get_ss': [MessageHandler(Filters.text & ~Filters.command, get_ss)],
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_list_command)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, get_apt_list)],
        },
        fallbacks=[]
    )

    convHandlerGetServices = ConversationHandler(
        entry_points=[CommandHandler('get_services', get_services)],
        states={
            'get_services': [MessageHandler(Filters.text & ~Filters.command, get_services)],
        },
        fallbacks=[]
    )

    convHandlerGetReplLogs = ConversationHandler(
        entry_points=[CommandHandler('get_repl_logs', get_repl_logs)],
        states={
            'get_repl_logs': [MessageHandler(Filters.text & ~Filters.command, get_repl_logs)],
        },
        fallbacks=[]
    )

    convHandlerGetEmails = ConversationHandler(
        entry_points=[CommandHandler('get_emails', get_emails)],
        states={
            'get_emails': [MessageHandler(Filters.text & ~Filters.command, get_emails)],
        },
        fallbacks=[]
    )

    convHandlerGetPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('get_phone_numbers', get_phone_numbers)],
        states={
            'get_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, get_phone_numbers)],
        },
        fallbacks=[]
    )


    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    # Обработчик команды /find_phone_numbers
    dp.add_handler(convHandlerFindPhoneNumbers)

    # Обработчик команды /find_email
    dp.add_handler(convHandlerFindEmail)

    # Обработчик команды /verify_password
    dp.add_handler(convHandlerVerifyPassword)

    # Обработчик команды /get_release
    dp.add_handler(convHandlerGetRelease)

    # Обработчик команды /get_uname
    dp.add_handler(convHandlerGetUname)

    # Обработчик команды /get_uptime
    dp.add_handler(convHandlerGetUptime)

    # Обработчик команды /get_df
    dp.add_handler(convHandlerGetDf)

    # Обработчик команды /get_free
    dp.add_handler(convHandlerGetFree)

    # Обработчик команды /get_mpstat
    dp.add_handler(convHandlerGetMpstat)

    # Обработчик команды /get_getw
    dp.add_handler(convHandlerGetW)

    # Обработчик команды /get_auths
    dp.add_handler(convHandlerGetAuths)

    # Обработчик команды /get_critical
    dp.add_handler(convHandlerGetCritical)

    # Обработчик команды /get_ps
    dp.add_handler(convHandlerGetPs)

    # Обработчик команды /get_ss
    dp.add_handler(convHandlerGetSs)

    # Обработчик команды /get_apt_list
    dp.add_handler(convHandlerGetAptList)

    # Обработчик команды /get_services
    dp.add_handler(convHandlerGetServices)

    # Обработчик команды /get_repl_logs
    dp.add_handler(convHandlerGetReplLogs)

    # Обработчик команды /get_emails
    dp.add_handler(convHandlerGetEmails)

    # Обработчик команды /get_phone_numbers
    dp.add_handler(convHandlerGetPhoneNumbers)



    # Запускаем бота
    updater.start_polling()

    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
