"""
GPT URL summarizer & search Telegram Bot

This is an older version of the  bot based on text-davinci-003

"""
from loguru import logger
import os
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from bs4 import BeautifulSoup, NavigableString, Tag
import tiktoken
import openai
import re
from readability import Document
import whisper
import rtr

openai.api_key = os.environ["OPENAI_API_KEY"]

OPENAI_ENGINE = "text-davinci-003"

tokenizer = tiktoken.get_encoding("gpt2")

whisper_model = whisper.load_model("large")

session = requests.session()
session.mount('https://', HTTPAdapter(max_retries=Retry(connect=5,
                                                        read=5,
                                                        status=5,
                                                        redirect=2,
                                                        backoff_factor=.001,
                                                        status_forcelist=(500, 502, 503, 504))))


bot = ApplicationBuilder().token(os.environ['JINGBOT_TELEGRAM_API_TOKEN']).build()


def extract_text_from_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.find_all(text=True)

    output = ''
    blacklist = ['[document]','noscript','header','html','meta','head','input','script', "style"]
    # there may be more elements you don't want

    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)
    return output


MAX_INPUT_TOKENS=3200


def url_to_response(url):
    """
    query the url and return the text content
    raises exception if unable to adequately parse content
    """
    resp = session.get(url)

    if resp.status_code != 200:
        return f"Unable to GET contents of {url}"

    PREPROMPT = "Provide a detailed summary of the following web page. If there is anything controversial please highlight the controversy. If there is something surprising, unique or clever, please highlight that as well:\n"
    
    doc = Document(resp.text)
    text = extract_text_from_html(doc.summary())
    
    if not len(text) or text.isspace():
        return "Unable to extract text data from url"
    
    token_count = len(tokenizer.encode(text)['input_ids'])

    if token_count > MAX_INPUT_TOKENS:
        # crudely truncate longer texts to get it back down to approximately the target MAX_INPUT_TOKENS
        split_point = int((MAX_INPUT_TOKENS/token_count)*len(text))
        percent = int(100*split_point/len(text))
        text = text[:split_point]  + "<TRUNCATED>\n\n"
        response = f"Only first {percent}% of url content processed due to length."
    else:
        response = ""
    prompt = PREPROMPT + text
    completion = openai.Completion.create(engine=OPENAI_ENGINE,
                                          prompt=prompt,
                                          temperature=.2,
                                          max_tokens=880)
    response += completion.choices[0].text
    logger.info(response)
    return response

def is_url(msg : str) -> bool:
    try:
        re.search("(?P<url>https?://[^\s]+)", msg).group("url")
        logger.info(f'url: {url}')
        return True
    except AttributeError:        
        return False
    
    
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    handle message from user
    """
    logger.info(update)
    text = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"receive message {chat_id}: {text}")

    def process():
        if is_url(text):
            return url_to_response(text)
        else:
            return rtr.askchat(text)

    try:
        response = process()
    except Exception as e:
        logger.exception(f"error handling message {text}")
        response = f'Unable to parse the url due to exception: {e}'
    await update.message.reply_text(response)


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    handle message from user

    example voice message:
        voice=Voice(duration=2,
                    file_id='AwACAgEAAx0Kb7SkOAADWmOfXswwgYvfboWWQKtJZAzWK7WhAAJ2AwxH4RJGJgNeIseL_LAQ',
                    file_size=11721,
                    file_unique_id='AgADdgMAAsMR-EQ',
                    mime_type='audio/ogg')

    """
    logger.info(update)
    voice = update.message.voice
    f = await voice.get_file()    
    try:
        os.unlink("voice.ogg")
    except:
        pass
    await f.download_to_drive('voice.ogg')
    import hashlib
    logger.info(hashlib.md5(open('voice.ogg', 'rb').read()).hexdigest())
    logger.info(whisper_model.device)
    result = whisper_model.transcribe("voice.ogg", verbose=True, task='transcribe')
    logger.info(result)
    response = result['text']
    logger.info(response)
    #await update.message.reply_text(response)

    if result['language'] == 'en':
        # lanugage was english, simply return now
        response = rtr.askchat(result['text'])
        await update.message.reply_text(response)
        return

    # now translate the result as well
    result = whisper_model.transcribe("voice.ogg", verbose=True, task='translate')
    logger.info(result)
    response = result['text']
    logger.info(response)
    #await update.message.reply_text(response)
    await update.message.reply_text(rtr.askchat(response))

    
bot.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, voice_handler))
bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

logger.info("run_polling")
bot.run_polling()
