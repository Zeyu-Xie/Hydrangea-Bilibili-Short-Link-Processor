import logging
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

# Functions
def get_server_info():
    hn = socket.gethostname()
    ip = requests.get('https://api.ipify.org').text
    return (hn, ip)
def legal_bilibili_short_url(url):
    url_parsed = None
    try:
        url_parsed = urlparse(url)
    except Exception as e:
        return (False, "URL parsing error.")
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
    return (True, "URL is legal.")
def short_link_redirected_url(short_link):
    # Send a HEAD request to get the redirection URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
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
    url = update.message.text
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
