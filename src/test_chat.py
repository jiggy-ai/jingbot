# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import openai
import tiktoken

encoders = {i:tiktoken.get_encoding(i) for i in tiktoken.list_encoding_names()}

messages = [{"role": "system",    "content": "You are a helpful assistant."},
            {"role": "user",      "content": "Who won the world series in 2020?"},
            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
            {"role": "user",      "content": "Where was it played?"}]


messages = [{"role": "system",    "content": "Who won the world series in 2000?"}]

messages = [{"role": "user",    "content": "What is the most useful info in sec filings?"}]

input_text = ""
for i in messages:
    input_text += f"{i['role']}\n{i['content']}\n"

print(input_text)

for ename, enc in encoders.items():
    print(f'{ename}: {2*len(messages)+len(enc.encode(input_text))}')


response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                        messages=messages,
                                        temperature=.125)

response_text = response['choices'][0]['message']['content']

print(response['usage'])
print(response_text)

prefix = "assistant\n"
for ename, enc in encoders.items():
    print(f'{ename}: {len(enc.encode(prefix+response_text))}')

