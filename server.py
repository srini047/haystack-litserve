from constants import SERVER_PORT, CO_API_KEY
import litserve as ls
import os

from haystack.utils import Secret
from haystack import Document, Pipeline
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.writers import DocumentWriter
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever

from haystack_integrations.components.embedders.cohere.document_embedder import (
    CohereDocumentEmbedder,
)
from haystack_integrations.components.embedders.cohere.text_embedder import (
    CohereTextEmbedder,
)


os.environ["CO_API_KEY"] = CO_API_KEY
document_store = InMemoryDocumentStore(embedding_similarity_function="cosine")


class DocumentChatAPI(ls.LitAPI):
    def setup(self, device):
        documents = [
            Document(
                content="This repo has an example of Haystack <> Litserve"
            ),
            Document(
                content="Haystack is AI framework for building LLM applications"
            ),
            Document(content="Litserve is a serving engine for LLMs"),
            Document(
                content="Making a RAG pipeline with Haystack and Litserve"
            ),
            Document(content="Cohere for embedding and LLM inference"),
        ]

        indexing_pipeline = Pipeline()
        indexing_pipeline.add_component(
            "embedder",
            CohereDocumentEmbedder(),
        )
        indexing_pipeline.add_component(
            "writer", DocumentWriter(document_store=document_store)
        )
        indexing_pipeline.connect("embedder", "writer")

        indexing_pipeline.run({"embedder": {"documents": documents}})

    def decode_request(self, request):
        return request["query"]

    def predict(self, query):
        query_pipeline = Pipeline()
        query_pipeline.add_component("text_embedder", CohereTextEmbedder())
        query_pipeline.add_component(
            "retriever",
            InMemoryEmbeddingRetriever(document_store=document_store),
        )
        query_pipeline.connect(
            "text_embedder.embedding", "retriever.query_embedding"
        )

        result = query_pipeline.run({"text_embedder": {"text": query}})

        query_pipeline = Pipeline()
        query_pipeline.add_component("text_embedder", CohereTextEmbedder())
        query_pipeline.add_component(
            "retriever",
            InMemoryEmbeddingRetriever(document_store=document_store),
        )
        query_pipeline.connect(
            "text_embedder.embedding", "retriever.query_embedding"
        )

        result = query_pipeline.run({"text_embedder": {"text": query}})

        return result["retriever"]["documents"][0]

    def encode_response(self, output):
        return {"output": output}


if __name__ == "__main__":
    api = DocumentChatAPI()
    server = ls.LitServer(api)
    server.run(port=SERVER_PORT)
