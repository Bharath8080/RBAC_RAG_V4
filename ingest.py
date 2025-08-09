import os
import chromadb
from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.cohere import CohereEmbedding

# Load environment variables
load_dotenv()

# Configure the embedding model
cohere_api_key = os.getenv("COHERE_API_KEY")
if not cohere_api_key:
    raise ValueError("COHERE_API_KEY not found in environment variables")

# Initialize the embedding model
embed_model = CohereEmbedding(
    cohere_api_key=cohere_api_key,
    model_name="embed-english-v3.0",
    input_type="search_document"
)

# Set the global embedding model
Settings.embed_model = embed_model

def process_documents(department: str, base_dir: str = "./resources/data"):
    """
    Process and index documents for a specific department
    
    Args:
        department: The department name (e.g., 'hr', 'engineering')
        base_dir: Base directory containing department folders
    """
    print(f"Processing documents for {department} department...")
    
    # Define paths
    dept_path = Path(base_dir) / department
    general_path = Path(base_dir) / "general"
    persist_dir = f"./chroma_db/{department}"
    
    # Create directory if it doesn't exist
    os.makedirs(persist_dir, exist_ok=True)
    
    # Initialize Chroma client
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    
    # Clear existing collection if it exists
    try:
        chroma_client.delete_collection("documents")
    except:
        pass
    
    # Create a new collection
    chroma_collection = chroma_client.get_or_create_collection("documents")
    
    # Create vector store
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # Load department-specific documents
    documents = []
    
    # Add department-specific files
    if dept_path.exists() and dept_path.is_dir():
        for file_path in dept_path.glob("*"):
            if file_path.is_file() and file_path.suffix in ['.md', '.txt', '.csv']:
                print(f"Processing {file_path.name}...")
                try:
                    # Read the file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Create a document with metadata
                    from llama_index.core import Document
                    doc = Document(
                        text=content,
                        metadata={
                            "source": str(file_path.name),
                            "department": department,
                            "type": "department_specific"
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    # Add general documents
    if general_path.exists() and general_path.is_dir():
        for file_path in general_path.glob("*"):
            if file_path.is_file() and file_path.suffix in ['.md', '.txt', '.csv']:
                print(f"Processing general document: {file_path.name}...")
                try:
                    # Read the file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Create a document with metadata
                    from llama_index.core import Document
                    doc = Document(
                        text=content,
                        metadata={
                            "source": str(file_path.name),
                            "department": "general",
                            "type": "general"
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    print(f"Error processing general document {file_path}: {str(e)}")
    
    if not documents:
        print(f"No documents found for {department} department.")
        return
    
    print(f"Indexing {len(documents)} documents...")
    
    # Create index with the documents
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
        embed_model=embed_model
    )
    
    print(f"✅ Successfully indexed {len(documents)} documents for {department} department")
    print(f"Index stored in: {persist_dir}")

def main():
    """Main function to process documents for all departments"""
    departments = ["hr", "engineering", "finance", "marketing"]
    
    for dept in departments:
        print(f"\n{'='*50}")
        print(f"Processing {dept.upper()} department")
        print(f"{'='*50}")
        process_documents(dept)
    
    print("\n✅ Document processing completed for all departments!")

if __name__ == "__main__":
    main()
