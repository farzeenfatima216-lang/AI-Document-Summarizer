import os

import streamlit as st
from langchain_core.prompts import PromptTemplate

try:
    from langchain_groq import ChatGroq
except Exception:  # pragma: no cover - optional dependency
    ChatGroq = None

from utils import prepare_document_payload

os.environ.setdefault(
    "GROQ_API_KEY",
    "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",
)

try:
    llm = ChatGroq(model="openai/gpt-oss-120b") if ChatGroq else None
except Exception:  # pragma: no cover - runtime safety
    llm = None

st.title("AI Document Summarizer and Q&A System")
st.write(
    "Upload a PDF, DOCX, or text file to generate a summary, extract key points, "
    "and ask questions based on the document."
)

uploaded_file = st.file_uploader(
    "Upload PDF, DOCX, or text file",
    type=["pdf", "docx", "txt", "md", "json"],
)

if uploaded_file is not None:
    payload = prepare_document_payload(uploaded_file.name, uploaded_file.getvalue())
    text = payload["text"]

    st.subheader("Document Text")
    st.write(text or "No readable text could be extracted from the uploaded file.")

    chunks = payload["chunks"]
    st.subheader("Document Chunks")
    for index, chunk in enumerate(chunks):
        st.write(f"Chunk {index + 1}")
        st.write(chunk)
        st.write("-------------------------")
    st.success(f"Total Chunks: {len(chunks)}")

    st.subheader("Document Summary")
    if llm:
        with st.spinner("Generating summary..."):
            summary = llm.invoke("Summarize this document in 5 lines:\n" + text)
        st.write(summary.content)
    else:
        st.write("Summary generation is unavailable because the LLM client could not be initialized.")

    st.subheader("Key Points")
    if llm:
        with st.spinner("Extracting key points..."):
            points = llm.invoke("Give 5 key points from this document:\n" + text)
        st.write(points.content)
    else:
        st.write("Key point extraction is unavailable because the LLM client could not be initialized.")

    st.subheader("Ask Question")
    query = st.text_input("Enter your question")
    if query:
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
        final_prompt = prompt.format(context="\n".join(chunks[:3]), question=query)
        if llm:
            with st.spinner("Finding the best answer..."):
                response = llm.invoke(final_prompt)
            st.subheader("Answer")
            st.write(response.content)
        else:
            st.subheader("Answer")
            st.write("Answer generation is unavailable because the LLM client could not be initialized.")
