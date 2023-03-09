"""
Base class for an embedding model (e.g. ada002)
"""

from pydantic import BaseModel, Field
import enum


class EmbeddingModelName(str, enum.Enum):
    """
    List of supported embedding models
    """
    ada002 = 'text-embedding-ada-002'
    multi_qa_mpnet_base_cos_v1 = 'multi-qa-mpnet-base-cos-v1'


class ModelEmbedding(BaseModel):
    """
    Embedding of a text as returned by a BaseEmbeddingModel derived class
    """
    text:         str
    tokens:       int
    gpt2_tokens:  int
    vector:       list[float]
    model:        EmbeddingModelName


class MaxTokenExceededException(Exception):
    """
    exception to raise during embedding if the number of tokens exceeds the maximum
    """


class BaseEmbeddingModel:

    def embed(self, text: str) -> ModelEmbedding:
        """
        return the embedding for the text
        """
        raise NotImplementedError

    def num_tokens(self, text: str) -> int:
        """
        return the number of tokens in the text
        """
        raise NotImplementedError

    def max_tokens(self) -> int:
        """
        return the maximum number of tokens that can be embedded
        """
        raise NotImplementedError

    def dim(self) -> int:
        """
        return the dimension of the embedding
        """
        raise NotImplementedError

    def model(self) -> EmbeddingModelName:
        """
        return the model type
        """
        raise NotImplementedError
   
    
