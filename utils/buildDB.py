from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

loader = TextLoader("chunks.txt", encoding="utf-8")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=200
)

chunks = splitter.split_documents(docs)

embeddings = OllamaEmbeddings(model="nomic-embed-text")

db = Chroma.from_documents(
    chunks,
    embeddings,
    persist_directory="./hytale_db"
)

db.persist()
print("Vectorial DB created.")
