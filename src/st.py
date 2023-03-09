# hugging face sentence transformer based embeddings

from loguru import logger
from sentence_transformers import SentenceTransformer
from embedding_model import BaseEmbeddingModel, ModelEmbedding, MaxTokenExceededException, EmbeddingModelName
import tiktoken
from retry import retry
from requests import Session
import os
from concurrent.futures import ThreadPoolExecutor

pool = ThreadPoolExecutor(max_workers=20)

HF_API_TOKEN=os.environ['HF_API_TOKEN']
HF_INFERENCE_ENDPOINT=os.environ['HF_INFERENCE_ENDPOINT']

session = Session()
session.headers.update({'Authorization': f'Bearer {HF_API_TOKEN}'})

@retry(delay=.1)
def hf_inference(text: str) -> list[float]:
        r = session.post(HF_INFERENCE_ENDPOINT, json={'inputs': text})
        return r.json()['embeddings']
        
class HFSentenceTransformer(BaseEmbeddingModel):

    def __init__(self, modelname : str) -> None:
        super().__init__()
        self.modelname = modelname
        self.st_model = SentenceTransformer(modelname)
        self._dim = len(self.st_model.encode('foo'))
        self.gpt2_tokenizer = tiktoken.get_encoding("gpt2")
        
    def embed(self, text: str) -> ModelEmbedding:
        """
        Embed a text string using the openai text-embedding-ada-002, returning a ModelEmbedding            
        """
        assert(not text.isspace())
        _text =  text.replace("\n", " ")  #  is this still needed?
        num_tokens = self.num_tokens(_text)
        if num_tokens > self.max_tokens():
            logger.warning(f"Max tokens exceeded: {num_tokens} > {self.max_tokens()}")
            #raise MaxTokenExceededException
        vector = self.st_model.encode(_text)
        return ModelEmbedding(text        = text,
                              tokens      = num_tokens,  
                              vector      = list(vector),
                              model       = self.modelname,
                              gpt2_tokens = self.num_gpt2_tokens(text))  # count tokens on original text with original newlines
    

    def embed_batch(self, texts: list[str]) -> list[ModelEmbedding]:
        """
        Embed a text string using the openai text-embedding-ada-002, returning a ModelEmbedding            
        """
        _texts = [text.replace("\n", " ") for text in texts]
        num_tokens = [self.num_tokens(t) for t in _texts]
        if max(num_tokens) > self.max_tokens():
            logger.warning(f"Max tokens exceeded: {max(num_tokens)} > {self.max_tokens()}")
            #raise MaxTokenExceededException
        if self.st_model.device.type == 'cpu':
            vectors = list(pool.map(hf_inference, _texts))
        else:
            vectors = self.st_model.encode(_texts)
            
        return [ModelEmbedding(text        = text,
                               tokens      = tkns,
                               vector      = list(v),
                               model       = self.modelname,
                               gpt2_tokens = self.num_gpt2_tokens(text)) for text, tkns, v in zip(texts, num_tokens, vectors)]
        
    def num_tokens(self, text: str) -> int:
        """
        return the number of tokens in the text when encoded by this embedding model.
        """
        return len(self.st_model.tokenizer.encode(text.replace('\n', " ")))

    def num_gpt2_tokens(self, text: str) -> int:
        """
        return the number of gpt2 tokens in the text without any transformations to the text
        """
        return len(self.gpt2_tokenizer.encode(text))
        
    def max_tokens(self) -> int:
        """
        return the maximum number of tokens that can be embedded
        """
        return self.st_model.max_seq_length
            
    def dim(self) -> int:
        """     
        return the dimension of the embedding
        """
        return self._dim

    def model(self) -> EmbeddingModelName:
        """
        return the model type
        """
        return self.modelname
