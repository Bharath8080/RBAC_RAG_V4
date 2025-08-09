# Departmental RAG System with Role-Based Access Control

A production-ready Streamlit-based RAG (Retrieval-Augmented Generation) application with MongoDB authentication and role-based access control. This application allows users to securely access and query department-specific documents based on their assigned roles.

## ✨ Features

- **Secure Authentication**: MongoDB-based user authentication
- **Role-Based Access Control (RBAC)**: Granular access to department-specific documents
- **Efficient Document Retrieval**: ChromaDB vector store with Cohere embeddings
- **Natural Language Queries**: Powered by Groq's LLM with Cohere embeddings
- **Modern UI**: Clean, responsive interface with dark/light theme support
- **Department-Specific Knowledge Bases**: Isolated document repositories for each department

## 🛠️ Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB instance)
- Cohere API key (for text embeddings)
- Groq API key (for LLM, optional but recommended)

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Bharath8080/RBAC_RAG_V4.git
   cd RBAC_RAG_V4
   ```

2. **Set up the environment**
   ```bash
   # Install uv (if not already installed)
   pip install uv
   
   # Create and activate virtual environment
   uv venv
   .venv\Scripts\activate  # On Windows
   # OR
   source .venv/bin/activate  # On Unix/macOS
   
   # Install dependencies
   uv pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the project root with the following content:
   ```
   # MongoDB Configuration
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-address>/<database>?retryWrites=true&w=majority
   DB_NAME=rag_system

   # Cohere API Key (for embeddings)
   COHERE_API_KEY=your_cohere_api_key_here

   # Optional: Groq API Key (for LLM)
   GROQ_API_KEY=your_groq_api_key_here
   ```
   Replace the placeholder values with your actual credentials.

4. **Set up the vector store**
   ```bash
   python ingest.py
   ```
   This will process and index all documents in the `resources/data/` directory.

5. **Initialize the database with sample users**
   ```bash
   python ingest_db.py
   ```
   This will create sample user accounts in your MongoDB database.

6. **Run the application**
   ```bash
   streamlit run app.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## 👥 Default User Accounts

| Username | Password    | Department  |
|----------|-------------|-------------|
| tony     | password123 | engineering |
| bruce    | securepass  | marketing   |
| sam      | financepass | finance     |
| natasha  | hrpass123   | hr          |

## 📁 Project Structure

```
RBAC_RAG_V4/
├── .env.example           # Example environment variables
├── app.py                # Main Streamlit application
├── database.py           # Database connection and user management
├── ingest.py             # Document processing and vector store creation
├── ingest_db.py          # Initialize MongoDB with sample users
├── requirements.txt      # Python dependencies
├── resources/
│   └── data/             # Department-specific documents
│       ├── engineering/
│       ├── finance/
│       ├── hr/
│       └── marketing/
└── chroma_db/            # ChromaDB vector store (created after first run)
```

## 🔧 Configuration

### Environment Variables

- `MONGO_URI`: MongoDB connection string
- `DB_NAME`: Database name (default: `rag_system`)
- `COHERE_API_KEY`: Required for text embeddings
- `GROQ_API_KEY`: Required for LLM responses (falls back to local model if not provided)

### Adding New Users

1. Run the `ingest_db.py` script with new user data
2. Or add users directly to MongoDB in the `users` collection

### Adding New Documents

1. Place documents in the appropriate department folder under `resources/data/`
2. Run `python ingest.py` to update the vector store

## 🛡️ Security Notes

- Always store sensitive information in environment variables, never in code
- Use strong, unique passwords for MongoDB access
- Regularly update your dependencies for security patches
- Consider implementing rate limiting in production
- Enable MongoDB network access restrictions

## 📄 License

This project is part of the Codebasics Resume Project Challenge.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the web framework
- [ChromaDB](https://www.trychroma.com/) for vector storage
- [Cohere](https://cohere.com/) for embeddings
- [Groq](https://groq.com/) for LLM inference
- [MongoDB](https://www.mongodb.com/) for user management
