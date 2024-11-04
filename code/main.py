import logging
from telegram import Update, MessageEntity
from telegram.ext import *
import os
import sys
import requests
from urllib.parse import urlparse, urlunparse, parse_qs
import yaml
import socket

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s\n', level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)
headers = config['headers']

# Functions
def get_server_info():
    hn = socket.gethostname()
    ip = requests.get('https://api.ipify.org').text
    return (hn, ip)
def legal_bilibili_short_url(url):
    global headers
    # Test if the URL can be parsed
    url_parsed = None
    try:
        url_parsed = urlparse(url)
    except Exception as e:
        return (False, "URL parsing error.")
    # Test if the URL is in the right format
    if url_parsed.scheme != "https":
        return (False, "URL scheme is not https.")
    if url_parsed.netloc != "b23.tv":
        return (False, "URL netloc is not b23.tv.")
    if url_parsed.params != "":
        return (False, "URL params is not empty.")
    if url_parsed.query != "":
        return (False, "URL query is not empty.")
    if url_parsed.fragment != "":
        return (False, "URL fragment is not empty.")
    # Test if the URL is valid
    res_headers = requests.get(url, headers=headers).headers
    if 'Bili-Status-Code' in res_headers.keys():
        if res_headers['Bili-Status-Code'] == '-404':
            return (False, "URL is in the right format but not valid.")
        else:
            return (True, "URL is legal.")
    else:
        return (True, "URL is legal.")
def short_link_redirected_url(short_link):
    global headers
    # Send a HEAD request to get the redirection URL
    response = requests.head(short_link, headers=headers)
    # Parse the query string from the redirection URL and reconstruct the URL
    location = urlparse(response.headers['Location'])
    query = parse_qs(location.query)
    for key, value in query.items():
        query[key] = value[0]
    location_dict = {
        'scheme': location.scheme,
        'netloc': location.netloc,
        'path': location.path,
        'params': location.params,
        'query': query,
        'fragment': location.fragment
    }
    redirected_url = urlunparse(
        (location_dict['scheme'], location_dict['netloc'], location_dict['path'], '', '', ''))
    # Return the URL
    return redirected_url

# Command Functions
async def server(update, context):
    hn, ip = get_server_info()
    await update.message.reply_text(f"Hostname: {hn}\nIP Address: {ip}")
    logger.info(f"Hostname: {hn}\nIP Address: {ip}")

# Message Functions
async def message(update, context):
    message = update.message
    url_list = []
    for entity in message.entities:
        if entity.type == MessageEntity.URL:
            url = message.text[entity.offset: entity.offset + entity.length]
            url_list.append(url)
    for url in url_list:
        legality, message = legal_bilibili_short_url(url)
        if not legality:
            await update.message.reply_text(message)
            logger.info(message)
        else:
            redirected_url = short_link_redirected_url(url)
            await update.message.reply_text(redirected_url)
            logger.info(redirected_url)

if __name__ == '__main__':

    try:
        # Create bot
        bot_token = sys.argv[1]
        application = Application.builder().token(bot_token).build()
        logger.info("Bot Started.")

        # Commands
        application.add_handler(CommandHandler("server", server))

        # Messages
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, message))

        # Run bot
        application.run_polling(1.0)

    except Exception as e:
        logger.error(f"ERROR: {type(e)} - {e}")
