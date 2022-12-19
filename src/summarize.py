#!/usr/bin/env python3.9

import os
import sys
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3 import Retry
from retrying import retry
from bs4 import BeautifulSoup, NavigableString, Tag
from transformers import GPT2Tokenizer
import openai
import re
from readability import Document
import string

openai.api_key = os.environ["OPENAI_API_KEY"]
OPENAI_ENGINE="text-davinci-002"

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")


session = requests.session()
session.mount('https://', HTTPAdapter(max_retries=Retry(connect=5,
                                                        read=5,
                                                        status=5,
                                                        redirect=2,
                                                        backoff_factor=.001,
                                                        status_forcelist=(500, 502, 503, 504))))





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


MAX_INPUT_TOKENS=2800


resp = requests.get(sys.argv[-1])

if resp.status_code != 200:
    print(f"Unable to GET contents of {url}")
    os.exit(1)

PREPROMPT = "Provide a one paragraph summary of the following web page:\n"
doc = Document(resp.text)

text = extract_text_from_html(doc.summary())
print()
print(text)
print()
token_count = len(tokenizer(text)['input_ids'])
print("TOKEN COUNT:", token_count)
print("=============================================")    
if token_count > MAX_INPUT_TOKENS:
    # crudely truncate longer texts to get it back down to approximately the target MAX_INPUT_TOKENS
    split_point = int((MAX_INPUT_TOKENS/token_count)*len(text))
    text = text[:split_point]  + "<TRUNCATED>\n\n"
    print(f"truncated text to first {split_point} characters")
    print(text)
    print("=============================================")
print("=============================================")        

msg = text

completion = openai.Completion.create(engine=OPENAI_ENGINE,
                                      prompt=PREPROMPT + text,
                                      temperature=.2,
                                      max_tokens=1000)
msg = completion.choices[0].text
print(msg)


