#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Standard modules """
import logging
import signal
import sys
import json
import re
from io import BytesIO

""" Local modules """
import config

""" 3th party modules """
from telegram import *
from telegram.ext import * 
import youtube_dl

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=config.LOG_LEVEL)
log = logging.getLogger(__name__)


def handle_cancel(update, context):
    return ConversationHandler.END

def handle_start(bot, update):
    """ Handle /start command """
    update.message.reply_text(
        text='<strong>How to start?</strong>\nshare a link !', 
        parse_mode=ParseMode.HTML)

def handle_incoming_url(bot, update, chat_data):
    """ Handle incoming url """
    url = update.message.text
    log.info('Incoming url "%s"' % url)

    # load audio information
    ydl = youtube_dl.YoutubeDL()
    with ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError as e:
            update.message.reply_text( 
                '<strong>Error:</strong> <i>Given url is invalid or from an unsupported source.</i>', parse_mode=ParseMode.HTML)
            return ConversationHandler.END

    # TODO: create format keyboard

    update.message.reply_text('<strong>%s</strong>\n<i>uploader: %s\nduration: %s\n---------------------\nChoose format:</i>' % \
        (info['title'], info['uploader'], info['duration']), parse_mode=ParseMode.HTML)

    chat_data['url'] = url
    return CHOOSE_FORMAT

def handle_format(bot, update, chat_data):
    """ Handle format """
    _format = update.message.text

    update.message.reply_text('Choose quick or advanced')

    chat_data['format'] = _format
    return QUICK_OR_ADVANCED

def handle_invalid_format(bot, update, chat_data):
    """ Handle invalid format """
    _format = update.message.text

    update.message.reply_text('<strong>Error:</strong> <i>%s is not a valid format.</i>' % _format, parse_mode=ParseMode.HTML)
    return CHOOSE_FORMAT

def handle_quick_download(bot, update, chat_data):
    update.message.reply_text('quick')
    return ConversationHandler.END

def handle_advanced_download(bot, update, chat_data):
    update.message.reply_text('Advanced download not implemented yet.')
    return ConversationHandler.END

def handle_error(bot, update, error):
    log.warning('Update "%s" caused error "%s"', update, error)


QUICK_OR_ADVANCED, CHOOSE_FORMAT = range(2)

def initialize():
    log.info('Initialize Telegram Bot...')

    updater = Updater(config.BOT_TOKEN)
    updater.dispatcher.add_error_handler(handle_error)

    updater.dispatcher.add_handler(CommandHandler('start', handle_start))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.all, handle_incoming_url, pass_chat_data=True)],

        states={
            CHOOSE_FORMAT: [RegexHandler('(bestaudio|best)', handle_format, pass_chat_data=True), 
                            MessageHandler(Filters.all, handle_invalid_format, pass_chat_data=True)],

            QUICK_OR_ADVANCED: [RegexHandler('quick', handle_quick_download, pass_chat_data=True),
                                RegexHandler('advanced', handle_advanced_download, pass_chat_data=True)]
        },

        fallbacks=[CommandHandler('cancel', handle_cancel)],
        run_async_timeout=999
    )

    updater.dispatcher.add_handler(conv_handler)


    # Start the Bot
    log.info('Start polling...')
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    log.info('Initialize Telegram Bot...DONE. switching to idle mode.')
    updater.idle()

def on_exit(sig, func=None):
    print("exit handler triggered")
    sys.exit(1)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, on_exit)
    initialize()
