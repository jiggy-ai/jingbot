
# memobot sqlmodel models
# Copyright (C) 2022 William S. Kish


from typing import Optional, List
from sqlmodel import Field, SQLModel, Column, ARRAY, Float, Enum
from pydantic import EmailStr, BaseModel, ValidationError, validator
from pydantic import condecimal
from time import time
import enum


timestamp = condecimal(max_digits=14, decimal_places=3)  # unix epoch timestamp decimal to millisecond precision




class TelegramUser(SQLmodel, table=True):
    id:             int       = Field(primary_key=True, description='Telegram User ID')
    username:       str       = Field(index=True, description="Telegram username")    
    first_name:     str       = Field(description="User's first name")
    last_name:      str       = Field(description="User's last name")
    is_bot:         bool      = Field(description="is_bot from telegram")
    is_premium:     bool      = Field(description="is_premium from telegram")
    language_code:  str       = Field(description="language_code from telegram")
    created_at:     timestamp = Field(default_factory=time, description='The epoch timestamp when the Evaluation was created.')

class TelegramChat(SQLmodel, table=True):
    id:             int       = Field(primary_key=True, description='Telegram Chat ID')
    title:          str       = Field(description="Chat title from telegram")
    type:           str       = Field(description="Chat type from telegram")
    created_at:     timestamp = Field(default_factory=time, description='The epoch timestamp when the Evaluation was created.')    
        
class URL(SQLmodel, table=True):
    id:             int       = Field(primary_key=True, description='Unique ID')
    url:            str       = Field((max_length=2048, description='The actual supplied URL')
    user_id         int       = Field(index=True, foreign_key='telegramuser.id', description='The user who sent the URL')
    created_at:     timestamp = Field(default_factory=time, description='The epoch timestamp when this was created.')


class UrlText(SQLModel, table=True):
    id:          int           = Field(primary_key=True, description="The text unique id.")
    url_id:      int           = Field(index=True, foreign_key="url.id", description="The usr this text was extracted from.")
    mechanism:   str           = Field(description="identifies which software mechanism exracted the text from the url")
    created_at:  timestamp     = Field(default_factory=time, description='The epoch timestamp when the url was crawled.')
    text:        str           = Field(max_length=65535, description="The readable text we managed to extract from the Url.")
    content      Optional[str] = Field(max_length=65535, description="original html content")
    content_type Optional[str] = Field(description="content type from http")

            
