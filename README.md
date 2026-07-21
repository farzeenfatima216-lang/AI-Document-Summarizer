# AI Document Summarizer & Q&A System

## Project Description
This project is an AI-powered web application that enables intelligent document analysis. Users can upload documents, generate polished summaries, extract key points, and ask questions about the content. The application uses a custom HTTP backend server with LangChain and Groq LLM for advanced natural language processing.

## Features
- 📄 **Multi-Format Support**: Upload PDF, DOCX, TXT, MD, and JSON files
- 📝 **Document Preview**: View extracted text from your uploaded document
- 🎯 **Smart Summaries**: AI-generated summaries using Groq LLM
- 💡 **Key Points Extraction**: Automatically extract 5 key points from documents
- 📊 **Smart Chunking**: Automatic document chunking with overlapping windows (1000 char chunks, 200 char overlap)
- 🤖 **Q&A System**: Ask questions and get answers directly from your document content
- ⚡ **Fallback Support**: Built-in fallback mechanisms when LLM is unavailable
- 🎨 **Modern UI**: Clean, responsive web interface with real-time processing

## Architecture
- **Backend**: Python HTTP server (`serve_frontend.py`) running on `http://127.0.0.1:8000`
- **Frontend**: HTML5, CSS3, and Vanilla JavaScript (no build tools required)
- **AI Engine**: LangChain + Groq LLM
- **Document Processing**: PyPDF (PDF), python-docx (DOCX), built-in parsers (TXT, MD, JSON)

## Technologies Used
- Python 3.13
- LangChain
- Groq API
- PyPDF
- python-docx
- HTML5 / CSS3 / JavaScript
- Custom HTTP Server (SimpleHTTPRequestHandler)

## Installation

1. **Clone or navigate to the project directory**
```bash
cd AI_Document_summarizer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up Groq API Key** (optional but recommended for better Q&A)
   - Get your API key from [Groq Console](https://console.groq.com)
   - The application will work with fallback methods if key is not available

## Run Project

**Start the backend server:**
```bash
python serve_frontend.py
```

The application will be available at: **http://127.0.0.1:8000**

**Using Streamlit alternative (optional):**
```bash
streamlit run app.py
```

## Usage

1. Open http://127.0.0.1:8000 in your web browser
2. Click "Choose a PDF, DOCX, or text file" to select a document
3. Click "Analyze document" to process
4. View the document preview, summary, and key points
5. Use the Q&A section to ask questions about your document

## Project Structure
```
AI_Document_summarizer/
├── serve_frontend.py      # Main HTTP backend server
├── script.js              # Frontend JavaScript logic
├── index.html             # Web interface
├── styles.css             # Styling
├── utils.py               # Document extraction utilities
├── app.py                 # Streamlit alternative
├── requirements.txt       # Python dependencies
└── tests/                 # Unit tests
```

## API Endpoints

- **POST `/api/analyze`**: Upload and analyze a document
  - Accepts multipart form data with file upload
  - Returns: status, file_name, preview, summary, key_points, chunks, text_length

- **POST `/api/ask`**: Ask a question about the document
  - Accepts JSON with question, context, and chunks
  - Returns: status, answer

## Author
Farzeen Fatima  
BS Artificial Intelligence