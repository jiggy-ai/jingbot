
from transformers import GPT2Tokenizer
import whisper

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

whisper_model = whisper.load_model("large")

