from loguru import logger
import openai
#import tiktoken
from pydantic import BaseModel
from retry import retry

MODEL = "gpt-3.5-turbo"

logger.info(f"MODEL: {MODEL}")

#encoder = tiktoken.get_encoding('cl100k_base')

#def token_count(text):
#    return len(encoder.encode(text))

class ChatRoleMessage(BaseModel):
    role: str
    text: str

class SystemMessage(ChatRoleMessage):
    role = 'system'
    text: str

class ContextMessage(ChatRoleMessage):    
    role = 'system'    
    text: str
    
class AssistantMessage(ChatRoleMessage):
    role = 'assistant'    
    text: str

class UserMessage(ChatRoleMessage):
    role = 'user'
    text: str

@retry(tries=10, delay=.3)
def completion(msgs :ChatRoleMessage, temperature=1) -> str:
    for msg in msgs:
        logger.info(f"{msg.role}: {msg.text}")

    messages = [{"role": msg.role, "content": msg.text} for msg in msgs]
    
    try:
        response =  openai.ChatCompletion.create(model = MODEL,
                                                 messages = messages,
                                                 temperature = temperature)
    except Exception as e:
        logger.exception(e)
        raise
        
    logger.info(response)
    response_text = response['choices'][0]['message']['content']
    return response_text
