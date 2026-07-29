import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Load Hugging Face token safely from environment variables
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

def load_llm_model(model_name="deepseek-ai/deepseek-llm-7b-base"):
    """
    Loads the Hugging Face Causal LM model and tokenizer using environment credentials.
    """
    print(f"Loading model: {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        token=HF_TOKEN,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        token=HF_TOKEN,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True
    )
    return tokenizer, model

def process_document(file_path):
    """
    Processes uploaded PDF or DOCX documents and builds a Chroma vector store.
    """
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.docx'):
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")

    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Chroma.from_documents(docs, embeddings)
    return vector_store

def chat_with_documents(query, vector_store, tokenizer, model):
    """
    Retrieves context from uploaded document vectors and generates an answer using the LLM.
    """
    if vector_store is None:
        return "Please upload a document first to query its contents."

    # Retrieve relevant document snippets
    docs = vector_store.similarity_search(query, k=3)
    context = "\n".join([doc.page_content for doc in docs])

    prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return response.split("Answer:")[-1].strip()
