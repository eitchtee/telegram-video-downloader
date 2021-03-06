import json
import logging
import os
import random
import string
from traceback import print_exc

import youtube_dl
from config import TELEGRAM_USER_ID, BOT_TOKEN, WETRANSFER_KEY
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackQueryHandler
from wetransfer import TransferApi

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


def queue_dir(request_id):
    work_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.normpath('{}/queue/{}.json'.format(work_dir, request_id))


def check_valid_urls(link):
    try:
        ydl_opts = {'noplaylist': True,
                    # 'dump_single_json': True,
                    'skip_download': True,
                    'quiet': True,
                    'simulate': True
                    }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except:
        return False
    else:
        return True


def download_video(link: str):
    work_dir = os.path.dirname(os.path.realpath(__file__))
    down_folder = os.path.normpath('{}/downloads/'.format(work_dir))
    down_folder_before_down = os.listdir(down_folder)
    try:
        ydl_opts = {'noplaylist': True,
                    'outtmpl': "{}/%(id)s.%(ext)s".format(down_folder),
                    'format': 'bestvideo[ext=mp4]+bestaudio['
                              'ext=m4a]/bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                    }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except:
        print_exc()
        return None

    down_folder_after_down = os.listdir(down_folder)
    video = None
    for file in down_folder_after_down:
        if file in down_folder_before_down:
            file_path = os.path.normpath('{}/{}'.format(down_folder, file))
            os.remove(file_path)
        else:
            video = os.path.normpath('{}/{}'.format(down_folder, file))

    return video


def download_audio(link: str):
    work_dir = os.path.dirname(os.path.realpath(__file__))
    down_folder = os.path.normpath('{}/downloads/'.format(work_dir))
    down_folder_before_down = os.listdir(down_folder)
    try:
        ydl_opts = {
            'noplaylist': True,
            'outtmpl': "{}/%(id)s.%(ext)s".format(down_folder),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])
    except:
        print_exc()
        return None

    down_folder_after_down = os.listdir(down_folder)
    video = None
    for file in down_folder_after_down:
        if file in down_folder_before_down:
            file_path = os.path.normpath('{}/{}'.format(down_folder, file))
            os.remove(file_path)
        else:
            video = os.path.normpath('{}/{}'.format(down_folder, file))

    return video


def upload_file(file, link):
    if file:
        try:
            api = TransferApi(WETRANSFER_KEY)
            download_link = api.upload_file(link, file)
            os.remove(file)
            return download_link
        except:
            print_exc()
            os.remove(file)
            return 'Não foi possível fazer o envio do arquivo.'
    else:
        return 'Não foi possível fazer o download.'


def start(update, context):
    update.message.reply_text('Oi! Me envia um vídeo ai...')


def down(update, context):
    links = update.message.text.split('\n')
    valid_links = []

    for link in links:
        is_url_valid = check_valid_urls(link)
        print(link, is_url_valid)
        if is_url_valid:
            chars = string.ascii_uppercase + string.digits
            file_id = ''.join(random.choice(chars) for x in range(20))
            valid_links.append([link, file_id])
        else:
            msg = f'*{link}*\n' \
                f'_URL Inválida ou não suportada!\n' \
                f'Tente de novo com outra._'
            update.message.reply_markdown(msg, quote=True)
    print(valid_links)

    for link in valid_links:
        with open(queue_dir(link[1]), 'w') as file:
            json.dump({'link': link[0]}, file)

        keyboard = [
            [InlineKeyboardButton('Vídeo',
                                  callback_data=f'v|{link[1]}'),
             InlineKeyboardButton('Áudio',
                                  callback_data=f'a|{link[1]}')],
            [InlineKeyboardButton('❌',
                                  callback_data=f'n|{link[1]}')]
        ]

        reply_markup_kb = InlineKeyboardMarkup(keyboard)

        msg = f'_O que você deseja baixar?_'
        update.message.reply_markdown(msg,
                                      disable_web_page_preview=True,
                                      quote=True,
                                      reply_markup=reply_markup_kb)


def button_handler(update, context):
    query = update.callback_query
    option, video_id = query.data.split('|')

    file_path = queue_dir(video_id)
    with open(file_path, 'r') as f:
        video_link = json.load(f).get('link', None)

    if option == 'v' and video_link:
        query.edit_message_text(text='_Fazendo o download..._',
                                quote=True,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)

        msg = '_Download do vídeo que você pediu:_\n\n{}'. \
            format(upload_file(download_video(video_link), video_link))
        query.edit_message_text(text=msg,
                                quote=True,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)

        if os.path.isfile(file_path):
            os.remove(file_path)

    elif option == 'a' and video_link:
        query.edit_message_text(text='_Fazendo o download..._',
                                quote=True,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)

        msg = '_Download do áudio que você pediu:_\n\n{}'. \
            format(upload_file(download_audio(video_link), video_link))
        # update.message.reply_markdown(msg, quote=True)
        query.edit_message_text(text=msg,
                                quote=True,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)

        if os.path.isfile(file_path):
            os.remove(file_path)

    elif option == 'n' and video_link:
        msg = '_Download cancelado._'
        query.edit_message_text(text=msg,
                                quote=True,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)

        if os.path.isfile(file_path):
            os.remove(file_path)

    else:
        msg = '_Não foi possível fazer o download do vídeo._'
        query.edit_message_text(text=msg,
                                quote=True,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True)
        if os.path.isfile(file_path):
            os.remove(file_path)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(BOT_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(
        CommandHandler("start", start, Filters.user(TELEGRAM_USER_ID)))

    updater.dispatcher.add_handler(CallbackQueryHandler(button_handler))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text & Filters.user(TELEGRAM_USER_ID),
                                  down))

    # log all errors
    # dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
