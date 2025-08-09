import os
import streamlit as st
import chromadb
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.cerebras import Cerebras
from llama_index.llms.groq import Groq
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.cohere import CohereEmbedding

# Load environment variables
load_dotenv()

# Dummy user database
USERS_DB = {
    "Tony": {"password": "password123", "role": "engineering"},
    "Bruce": {"password": "securepass", "role": "marketing"},
    "Sam": {"password": "financepass", "role": "finance"},
    "Peter": {"password": "pete123", "role": "engineering"},
    "Sid": {"password": "sidpass123", "role": "marketing"},
    "Natasha": {"password": "hrpass123", "role": "hr"}
}

# Role-based access control for documents
ROLE_ACCESS = {
    "hr": ["hr", "general"],
    "engineering": ["engineering", "general"],
    "finance": ["finance", "general"],
    "marketing": ["marketing", "general"]
}

# Initialize session state
def initialize_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Set page config
st.set_page_config(
    page_title="Departmental RAG System",
    page_icon="🔒",
    layout="wide"
)

# Initialize session state
initialize_session_state()

def login(username: str, password: str) -> bool:
    """Authenticate user and set session state"""
    if username in USERS_DB and USERS_DB[username]["password"] == password:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = USERS_DB[username]["role"]
        st.session_state.messages = []
        return True
    return False

def logout():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.messages = []

@st.cache_resource
def load_vector_index(role: str):
    """Load the ChromaDB index for the user's role"""
    try:
        # Initialize Cohere embeddings
        cohere_api_key = os.getenv("COHERE_API_KEY")
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY not found in environment variables")
            
        embed_model = CohereEmbedding(
            cohere_api_key=cohere_api_key,
            model_name="embed-english-v3.0",
            input_type="search_document"
        )
        Settings.embed_model = embed_model
        
        # Initialize Chroma client
        persist_dir = f"./chroma_db/{role}"
        chroma_client = chromadb.PersistentClient(path=persist_dir)
        
        # Get the collection
        chroma_collection = chroma_client.get_collection("documents")
        
        # Create vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Load the index
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context,
            embed_model=embed_model
        )
        
        return index
    except Exception as e:
        st.error(f"Error loading vector index: {str(e)}")
        st.stop()

def chat_interface():
    """Main chat interface"""
    st.title(f"🔒 {st.session_state.role.capitalize()} Department Assistant")
    st.write(f"Welcome, {st.session_state.username}!")
    
    # Load the appropriate index for the user's role
    index = load_vector_index(st.session_state.role)
    
    # Initialize Cerebras LLM
    try:
        llm = Groq(
            model="openai/gpt-oss-120b",  # Using a smaller model for demo
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.5,
            system_prompt="You are a helpful assistant specialized in " + st.session_state.role + " department documents. Answer the user queries with the help of the provided context with high accuracy and precision."  # Optional if using local instance
        )
        
        # Create query engine with the LLM
        query_engine = index.as_query_engine(
            llm=llm,
            similarity_top_k=3,
            response_mode="compact"
        )
    except Exception as e:
        st.error(f"Error initializing LLM: {str(e)}")
        st.warning("Falling back to default LLM settings. Some features may be limited.")
        query_engine = index.as_query_engine(
            similarity_top_k=3,
            response_mode="compact"
        )
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input(f"Ask about {st.session_state.role} documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Get response from query engine
                response = query_engine.query(prompt)
                full_response = str(response)
                message_placeholder.markdown(full_response)
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                message_placeholder.error(error_msg)
                full_response = error_msg
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

def main():
    """Main application"""
    # Sidebar
    with st.sidebar:
        st.title("🔒 Department RAG System")
        
        if st.session_state.authenticated:
            st.write(f"Logged in as: **{st.session_state.username}**")
            st.write(f"Role: **{st.session_state.role.capitalize()}**")
            
            if st.button("Logout"):
                logout()
                st.rerun()
            
            st.markdown("---")
            st.write("### Available Documents")
            for doc_type in ROLE_ACCESS.get(st.session_state.role, []):
                st.write(f"- {doc_type.capitalize()} documents")
            
            st.markdown("---")
            st.write("### About")
            st.write("This is a secure RAG system with role-based access control.")
        else:
            st.write("### Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if login(username, password):
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    # Main content
    if st.session_state.authenticated:
        chat_interface()
    else:
        st.title("🔒 Department RAG System")
        st.write("Please log in to access the system.")

if __name__ == "__main__":
    main()
