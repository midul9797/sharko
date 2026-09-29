import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

def build_rag_chain():
    # Load text files (robust to CWD and encoding)
    all_docs = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_files = [
        os.path.join(base_dir, "data", "frontend.txt"),
        os.path.join(base_dir, "data", "backend.txt"),
        os.path.join(base_dir, "data", "dataset.txt"),
        os.path.join(base_dir, "data", "model_traning.txt"),
    ]
    for file_path in data_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found: {file_path}")
        # Prefer UTF-8; fall back to Latin-1 to avoid chardet dependency
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            all_docs.extend(loader.load())
        except UnicodeDecodeError:
            loader = TextLoader(file_path, encoding="latin-1")
            all_docs.extend(loader.load())

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=50)
    docs = splitter.split_documents(all_docs)

    # Use local HuggingFace embeddings (no API calls needed)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    # Vector DB
    vectorstore = Chroma.from_documents(docs, embedding=embeddings)

    # Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        # other params...
    )
    # Retrieval + LLM chain
    retriever = vectorstore.as_retriever()
    prompt_template = """You are an AI assistant for project Sharko, a shark habitat prediction system currently focused on Australian coastal waters. Your job is to answer questions about how the project was built, how the models were trained, how the dataset was created, how the frontend was built, and how the backend was built, based strictly on the Context below (which reflects the current, Australia-focused version of the project, not any earlier global version). Answer the question with a relevant tone. Don't answer questions that are not related to the project. Question and Context are given below. Don't tell the user you are telling the answer based on the context. Answer the question briefly.
    Context:
    {context}
    Question:
    {question}
    Answer:
"""

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=prompt_template,
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        combine_docs_chain_kwargs={"prompt": prompt}
    )

    return chain
