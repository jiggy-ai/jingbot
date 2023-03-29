"""
Chatbot based on OpenAI GPT-3.5-turbo
Copyright (C) 2023 Jiggy AI LLC
"""
from loguru import logger
import os
import telegram
from telegram import Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from bs4 import BeautifulSoup, NavigableString, Tag
import tiktoken
import openai
import re
from readability import Document
from random import choice
import asyncio
from time import time
import re

bot = ApplicationBuilder().token(os.environ['JINGBOT_TELEGRAM_API_TOKEN']).build()

from chatstack import ChatContext

chat_id_to_context = {}

async def set_random_role(update):
    await update.message.reply_text("Use /act to select a specific role for the chatbot or /random to select another random role.", parse_mode=ParseMode.MARKDOWN)
    role = choice(list(prompts.prompts.keys()))
    await update.message.reply_text(f"Selected role: '{role}'")
    prompt = prompts.prompts[role]
    chat_id_to_context[update.message.chat_id] = ChatContext(base_system_msg_text=prompts.prompts[role],
                                                             min_response_tokens=400,           # minimum number of tokens to reserve for model completion response;  max input context will be (4096 - min_response_tokens)
                                                             max_response_tokens=800,
                                                             temperature=0.7)
from retry import retry

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    handle message from user
    """
    logger.info(update)
    if update.message is None:
        logger.info('update.message is None (e.g. edited message)')
        return
    #with Session(engine) as session:
    #    user = User.from_telegram_user(session, update.message.from_user)

    text = update.message.text            
    if update.message.chat.type != ChatType.PRIVATE:
        return # ignore messages in groups
        #text = gpt_prefix(text)
        #if not text:
        #    return    
    #logger.info(f'{user.id} {user.first_name} {user.last_name} {user.username} {user.telegram_id}: "{text}"')
    if not text or text.isspace():
        return    

    # send placeholder message to user
    placeholder_message = await update.message.reply_text("...")

    # send typing action
    await update.message.chat.send_action(action="typing")
     
    text = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"receive message {chat_id}: {text}")

    if chat_id not in chat_id_to_context:
         chat_id_to_context[update.message.chat_id] = ChatContext(base_system_msg_text=prompts.prompts['Assistant'],
                                                                  min_response_tokens=400,           # minimum number of tokens to reserve for model completion response;  max input context will be (4096 - min_response_tokens)
                                                                  max_response_tokens=800,
                                                                  temperature=0.5)        
    chat_context = chat_id_to_context[chat_id]
    gen = chat_context.user_message_stream(text)
    last_time = time()
    prev_reply_text = ""
    target_dt = .1
    async for status, reply_text in gen:

        if len(reply_text) > 4096:
            await update.message.reply_text("response length exceeded")
            # consider starting a new placeholder message
            return
                
        target_dt = min(1, target_dt*1.05)
        if time() - last_time < target_dt and status != "finished":
            continue
        last_time = time()

        async def send_response():
            try:
                await context.bot.edit_message_text(reply_text, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id, parse_mode=ParseMode.MARKDOWN)
            except telegram.error.RetryAfter as e:
                # 'telegram.error.RetryAfter: Flood control exceeded. Retry in 267 seconds'
                logger.error(e)
                pattern = r'\d+'
                number = int(re.search(pattern, text).group())
                logger.info(f'sleep {number}')
                sleep(number)
                await update.message.reply_text("<telegram rate limit exceeded>")
            except telegram.error.BadRequest as e:
                logger.error(e)
                if str(e).startswith("Message is not modified"):
                    return
                else:
                    await context.bot.edit_message_text(reply_text, chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id)
        await send_response()
                
    logger.info(f"send message {chat_id}: {reply_text}")




bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

import prompts

async def command(update: Update, tgram_context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle command from user
    role - Set the role by name or semantic search
    random - select a random role
    prompt - output the base system prompt for the current role
    """
    text = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"receive command {chat_id}: {text}")    
    if text.startswith('/role' ):
        role = text[5:].strip()
        if not role:
             await update.message.reply_text(f"I know how to act as the following:\n{', '.join(prompts.prompts.keys())}")
             return                               
        role = prompts.search_role(role)
        await update.message.reply_text(f"Using role '{role}'")
        prompt = prompts.prompts[role]

        chat_id_to_context[chat_id] = ChatContext(base_system_msg_text=prompts.prompts[role],
                                                  min_response_tokens=400,           # minimum number of tokens to reserve for model completion response;  max input context will be (4096 - min_response_tokens)
                                                  max_response_tokens=800,
                                                  temperature=0.7)
    elif text.startswith('/random'):
        await set_random_role(update)
    elif text.startswith('/prompt'):
        await update.message.reply_text(chat_id_to_context[chat_id].base_system_msg.text)
    
bot.add_handler(MessageHandler(filters.COMMAND, command))

logger.info("run_polling")
bot.run_polling()
