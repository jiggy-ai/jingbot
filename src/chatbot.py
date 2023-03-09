"""
Chatbot based on OpenAI GPT-3.5-turbo
Copyright (C) 2023 Jiggy AI LLC
"""
from loguru import logger
import os
from telegram import Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from bs4 import BeautifulSoup, NavigableString, Tag
import tiktoken
import openai
import re
from readability import Document
from random import choice

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

    text = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"receive message {chat_id}: {text}")

    if chat_id not in chat_id_to_context:
        await set_random_role(update)
        
    chat_context = chat_id_to_context[chat_id]

    response_text = chat_context.user_message(text)
    logger.info(f"send message {chat_id}: {response_text}")
    try:
        await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
    except:
        await update.message.reply_text(response_text)



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
