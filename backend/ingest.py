import os
from dotenv import load_dotenv
from langchain_ollama import OllamaEmbeddings    
from langchain_pinecone import PineconeVectorStore

# Load the API key from .env
load_dotenv()

print("Initializing local embedding model...")
# Connect to the local Ollama embedding model using the updated class
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

print("Connecting to Pinecone...")
# The new Pinecone package automatically uses the PINECONE_API_KEY from your .env
index_name = "debate-knowledge"

# Sample "documentation" facts for the agents
sample_documents = [
    "Fact 1: Deploying autonomous AI without human oversight in financial systems led to a 15% increase in rapid micro-crashes in 2025 simulations.",
    "Fact 2: Tech startups utilizing fully autonomous CI/CD pipelines with AI agents reported a 40% reduction in server deployment costs.",
    "Fact 3: The 'Ghost-in-the-Loop' vulnerability allows bad actors to inject malicious prompts directly into production AI databases, bypassing standard firewalls."
]

print("Converting text to vectors and uploading to Pinecone... (This takes a moment)")
# Embed the text locally and send it straight to Pinecone
vectorstore = PineconeVectorStore.from_texts(
    texts=sample_documents, 
    embedding=embeddings, 
    index_name=index_name
)

print("✅ Success! Knowledge successfully ingested into Pinecone.")