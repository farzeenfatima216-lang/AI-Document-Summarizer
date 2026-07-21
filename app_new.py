import os

import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from utils import prepare_document_payload

os.environ.setdefault("GROQ_API_KEY", "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")

st.set_page_config(page_title="AI Document Summarizer", page_icon="📄", layout="wide")

st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }
    .hero-card {
        background: linear-gradient(135deg, #111827, #1f2937);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    .hero-card h1 {
        font-size: 2rem;
        margin-bottom: 0.4rem;
    }
    .hero-card p {
        font-size: 1rem;
        color: #d1d5db;
        margin: 0;
    }
    .panel-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 8px 20px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    llm = ChatGroq(model="openai/gpt-oss-120b")
except Exception:  # pragma: no cover - runtime safety
    llm = None

st.markdown(
    """
    <div class="hero-card">
        <h1>AI Document Summarizer & Q&A</h1>
        <p>Upload a PDF, DOCX, or text file to generate a polished summary, extract key points, and ask questions from the document.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Upload your document</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose a PDF, DOCX, or text file",
        type=["pdf", "docx", "txt", "md", "json"],
    )
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    payload = prepare_document_payload(uploaded_file.name, uploaded_file.getvalue())
    text = payload["text"]

    if text.strip():
        col1, col2 = st.columns([1.2, 0.8])

        with col1:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Document preview</div>', unsafe_allow_html=True)
            with st.expander("Show extracted text", expanded=False):
                st.text_area("", text, height=220)
            st.markdown('</div>')

            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)
            if llm:
                with st.spinner("Generating summary..."):
                    summary = llm.invoke("Summarize this document in 5 lines:\n" + text)
                st.write(summary.content)
            else:
                st.write("Summary generation is unavailable because the LLM client could not be initialized.")
            st.markdown('</div>')

            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Key points</div>', unsafe_allow_html=True)
            if llm:
                with st.spinner("Extracting key points..."):
                    points = llm.invoke("Give 5 key points from this document:\n" + text)
                st.write(points.content)
            else:
                st.write("Key point extraction is unavailable because the LLM client could not be initialized.")
            st.markdown('</div>')

        with col2:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Document analysis</div>', unsafe_allow_html=True)
            chunks = payload["chunks"]
            st.write(f"Total chunks: **{len(chunks)}**")
            st.write("The document has been split into searchable sections for Q&A.")
            st.success("Document processing completed successfully")
            st.markdown('</div>')

            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Ask a question</div>', unsafe_allow_html=True)
            query = st.text_input("Enter your question", placeholder="e.g. What is the main idea?")
            if query:
                context = "\n".join(chunks[:3])
                prompt = PromptTemplate(
                    input_variables=["context", "question"],
                    template="""
Answer the question only from the given context.
Context:
{context}
Question:
{question}
Answer:
""",
                )
                final_prompt = prompt.format(context=context, question=query)
                if llm:
                    with st.spinner("Finding the best answer..."):
                        response = llm.invoke(final_prompt)
                    st.write(response.content)
                else:
                    st.write("Answer generation is unavailable because the LLM client could not be initialized.")
                st.markdown('</div>')
    else:
        st.warning("No readable text could be extracted from the uploaded file.")
else:
    st.info("Upload a file to begin.")
