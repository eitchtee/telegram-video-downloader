import logging
import os
from traceback import print_exc

import youtube_dl
from config import TELEGRAM_USER_ID, BOT_TOKEN, WETRANSFER_KEY
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from wetransfer import TransferApi

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


def download_video(link: str):
    work_dir = os.path.dirname(os.path.realpath(__file__))
    down_folder = os.path.normpath('{}/downloads/'.format(work_dir))
    down_folder_before_down = os.listdir(down_folder)
    try:
        ydl_opts = {'noplaylist': True,
                    'outtmpl': "{}/%(id)s.%(ext)s".format(down_folder),
                    'nocontinue': True,
                    'format': 'bestvideo+bestaudio/best',
                    'merge-output-format': 'mp4'
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
    msg = '*Download:*\n\n{}'. \
        format(upload_file(download_video(update.message.text),
                           update.message.text))
    update.message.reply_markdown(msg, quote=True)


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