__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import streamlit as st
import chromadb
from typing import Dict, Optional, Any
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.groq import Groq
from llama_index.embeddings.cohere import CohereEmbedding

# Import database module
from database import db, initialize_users

# Load environment variables
load_dotenv()

# Initialize default users
initialize_users()

# Role-based access control for documents
ROLE_ACCESS = {
    "hr": ["hr", "general"],
    "engineering": ["engineering", "general"],
    "finance": ["finance", "general"],
    "marketing": ["marketing", "general"]
}

# Initialize session state
def initialize_session_state():
    """Initialize or reset the session state"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "role" not in st.session_state:
        st.session_state.role = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "vector_index" not in st.session_state:
        st.session_state.vector_index = None
    if "query_engine" not in st.session_state:
        st.session_state.query_engine = None

# Set page config
st.set_page_config(
    page_title="Departmental RAG System",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
initialize_session_state()

# Authentication functions
def login(username: str, password: str) -> bool:
    """
    Authenticate user and set session state
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        bool: True if authentication was successful, False otherwise
    """
    try:
        user = db.verify_user(username, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.username = user["username"]
            st.session_state.role = user["role"]
            st.session_state.messages = [
                {"role": "assistant", "content": f"Welcome, {user['username']}! How can I assist you today?"}
            ]
            st.rerun()  # Rerun to update the UI
            return True
        return False
    except Exception as e:
        st.error(f"An error occurred during login: {str(e)}")
        return False

def logout():
    """
    Log out the current user and clear session state
    """
    username = st.session_state.get('username', 'Unknown')
    st.session_state.clear()
    initialize_session_state()
    st.success(f"Successfully logged out {username}")
    st.rerun()  # Rerun to update the UI

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

def show_login_form():
    """Display the login form"""
    st.title("🔒 Departmental RAG System")
    st.markdown("### Please log in to access the system")
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                login_button = st.form_submit_button("Login")
                
                if login_button:
                    if not username or not password:
                        st.error("Please enter both username and password")
                    elif login(username, password):
                        st.success(f"Welcome, {username}! Redirecting...")
                    else:
                        st.error("Invalid username or password")

    # Add some helpful information
    st.markdown("---")
    st.markdown("""
    ### Demo Credentials
    - **Engineering:** Tony / password123
    - **Marketing:** Bruce / securepass
    - **Finance:** Sam / financepass
    - **HR:** Natasha / hrpass123
    """)

def main():
    """
    Main application entry point
    Handles routing between login and main application
    """
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
        }
        .stTextInput input, .stTextInput input:focus {
            border: 1px solid #4a90e2 !important;
            box-shadow: 0 0 0 1px #4a90e2 !important;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            background-color: #4a90e2;
            color: white;
        }
        .stButton>button:hover {
            background-color: #357abd;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar for logout and user info
    with st.sidebar:
        if st.session_state.authenticated:
            st.markdown(f"### Welcome, {st.session_state.username}")
            st.markdown(f"**Role:** {st.session_state.role.capitalize()}")
            
            if st.button("Logout", key="logout_btn"):
                logout()
                return
            
            st.markdown("---")
            st.markdown("### About")
            st.markdown("""
            This is a secure departmental RAG system that provides
            role-based access to information across different departments.
            """)
    
    # Main content area
    if not st.session_state.authenticated:
        show_login_form()
    else:
        # Display chat interface if authenticated
        st.title(f"💬 {st.session_state.role.capitalize()} Department Chat")
        chat_interface()

if __name__ == "__main__":
    main()
