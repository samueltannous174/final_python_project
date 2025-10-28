from pathlib import Path
from typing import List, Sequence, Optional

from haystack import Pipeline
from haystack.components.converters import MultiFileConverter
from haystack.components.preprocessors import DocumentCleaner, RecursiveDocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.builders import ChatPromptBuilder
from haystack.dataclasses import ChatMessage

from haystack_integrations.document_stores.chroma import ChromaDocumentStore
from haystack_integrations.components.retrievers.chroma import ChromaEmbeddingRetriever
from haystack_integrations.components.generators.openrouter import OpenRouterChatGenerator

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5
OPENROUTER_MODEL = "openai/gpt-4o-mini"
from pathlib import Path
try:
    from django.conf import settings
    BASE_DIR = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parents[1]))
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[1]

CHROMA_PATH = str(BASE_DIR / "chroma_db")
COLLECTION = "books"

def _get_store() -> ChromaDocumentStore:
    return ChromaDocumentStore(
        persist_path=CHROMA_PATH,
        collection_name=COLLECTION,
    )

_STORE = _get_store()
_TEXT_EMBEDDER = SentenceTransformersTextEmbedder(model=EMBED_MODEL)
_RETRIEVER = ChromaEmbeddingRetriever(document_store=_STORE, top_k=TOP_K)

_SEARCH_PIPE = Pipeline()
_SEARCH_PIPE.add_component("text_embedder", _TEXT_EMBEDDER)
_SEARCH_PIPE.add_component("retriever", _RETRIEVER)
_SEARCH_PIPE.connect("text_embedder.embedding", "retriever.query_embedding")
# 

def _build_index_pipeline(store: ChromaDocumentStore) -> Pipeline:
    pipe = Pipeline()
    converter = MultiFileConverter()
    cleaner = DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True,
        remove_repeated_substrings=True,
    )
    splitter = RecursiveDocumentSplitter(split_length=CHUNK_SIZE, split_overlap=CHUNK_OVERLAP)
    doc_embedder = SentenceTransformersDocumentEmbedder(model=EMBED_MODEL)
    writer = DocumentWriter(document_store=store)

    pipe.add_component("convert", converter)
    pipe.add_component("clean", cleaner)
    pipe.add_component("split", splitter)
    pipe.add_component("doc_embedder", doc_embedder)
    pipe.add_component("write", writer)

    pipe.connect("convert.documents", "clean.documents")
    pipe.connect("clean.documents", "split.documents")
    pipe.connect("split.documents", "doc_embedder.documents")
    pipe.connect("doc_embedder.documents", "write.documents")
    return pipe
from chromadb import PersistentClient

def _build_query_pipeline(store: ChromaDocumentStore) -> Pipeline:
  
  
    pipe = Pipeline()
    text_embedder = SentenceTransformersTextEmbedder(model=EMBED_MODEL)
    
    retriever = ChromaEmbeddingRetriever(document_store=store, top_k=TOP_K)


    prompt = ChatPromptBuilder(
        template=[
            ChatMessage.from_system(
            "Use ONLY this context to answer.\n\n"
            "{% for d in documents %}"
            "Source {{ loop.index }}:\n{{ d.content }}\n---\n"
            "{% endfor %}"
            "Question: {{query}}\n\n"
            "Answer concisely. if not conext answer what you know"
            ),
            ChatMessage.from_user("Question: {{ query }}")
        ],
        required_variables=["documents", "query"]
    )

    generator = OpenRouterChatGenerator(model=OPENROUTER_MODEL)

    pipe.add_component("text_embedder", text_embedder)
    pipe.add_component("retriever", retriever)
    pipe.add_component("prompt", prompt)
    pipe.add_component("llm", generator)

    pipe.connect("text_embedder.embedding", "retriever.query_embedding")
    pipe.connect("retriever.documents", "prompt.documents")
    pipe.connect("prompt.prompt", "llm.messages")
 

    return pipe

def index_files(file_paths: Sequence[str]) -> None:
    if not file_paths:
        return
    sources = [str(Path(p).resolve()) for p in file_paths if Path(p).is_file()]
    if not sources:
        return
    pipe = _build_index_pipeline(_STORE)
    pipe.run({"convert": {"sources": sources}})

def run_rag(query: str) -> str:
    print("query:", query)
    qa = _build_query_pipeline(_STORE)
    result = qa.run({
        "text_embedder": {"text": query},
        "prompt": {"query": query},
    },         include_outputs_from={"text_embedder", "retriever", "prompt", "llm"}
)
    embedding = result.get("text_embedder", {}).get("embedding", None)
 

    docs = result.get("retriever", {}).get("documents", [])
    print(f"\nRetrieved {len(docs)} document(s):\n")
    for i, d in enumerate(docs, 1):
        score = getattr(d, "score", "N/A")
        preview = (d.content or "").replace("\n", " ")[:220]
        print(f"{i}. score={score}  id={getattr(d, 'id', 'N/A')}")
        print(f"   {preview}\n")

    
    replies = result["llm"]["replies"]
    if not replies:
        return ""
    if hasattr(replies[0], "text") and replies[0].text:
        return replies[0].text
    if hasattr(replies[0], "content") and replies[0].content:
        parts = [getattr(p, "text", "") for p in replies[0].content if getattr(p, "text", "")]
        return "\n".join(p for p in parts if p).strip()
    return ""
