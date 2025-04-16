import streamlit as st
import os
import glob
from finalrag import (
    extract_text_from_pdf, 
    summarize_text, 
    generate_pdf_rag_response, 
    get_pdf_files
)
import openai
import tempfile

# Page configuration
st.set_page_config(
    page_title="Thesis Library Assistant",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if "pdf_corpus" not in st.session_state:
    st.session_state.pdf_corpus = []
    
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key="fAaHJwAYLY_D6HzVyTJ2Hr7Ve8KjKg1WT5sV5oFxGBA",
    base_url="https://api.brilliantai.co"
)

def create_corpus_from_uploaded_files(uploaded_files):
    """Create corpus from uploaded files"""
    corpus = []
    temp_dir = tempfile.mkdtemp()
    
    for uploaded_file in uploaded_files:
        # Save the uploaded file to temp directory
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Extract text from the PDF
        text = extract_text_from_pdf(file_path)
        
        # Create document entry with metadata
        document = {
            'title': uploaded_file.name,
            'path': file_path,
            'content': text,
            'summary': summarize_text(text[:5000]) if text else "[No content extracted]"
        }
        
        corpus.append(document)
    
    return corpus

# App header
st.title("📚 CSPC Thesis Library Assistant")
st.markdown("""
This assistant helps you find relevant information in thesis papers and research documents in CSPC library.
""")

# Sidebar for uploading files and selecting data source
with st.sidebar:
    st.header("Data Source")
    
    data_source = st.radio(
        "Choose your data source:",
        ["Upload Files", "Use Existing Files"]
    )
    
    if data_source == "Upload Files":
        uploaded_files = st.file_uploader(
            "Upload thesis papers or research PDFs",
            type="pdf",
            accept_multiple_files=True
        )
        
        if uploaded_files and st.button("Process Uploaded PDFs"):
            with st.spinner("Processing uploaded PDFs..."):
                st.session_state.pdf_corpus = create_corpus_from_uploaded_files(uploaded_files)
                st.success(f"Processed {len(st.session_state.pdf_corpus)} PDF documents!")
    
    else:  # Use Existing Files
        if st.button("Load PDFs from Directory"):
            with st.spinner("Scanning directory for PDFs..."):
                pdf_files = get_pdf_files()
                
                if not pdf_files:
                    st.error("No PDF files found in the current directory.")
                else:
                    st.info(f"Found {len(pdf_files)} PDF files in the directory.")
                    
                    # Create corpus from existing PDFs
                    corpus = []
                    for pdf_path in pdf_files:
                        pdf_name = os.path.basename(pdf_path)
                        
                        # Extract text
                        text = extract_text_from_pdf(pdf_path)
                        
                        # Create document entry
                        document = {
                            'title': pdf_name,
                            'path': pdf_path,
                            'content': text,
                            'summary': summarize_text(text[:5000]) if text else "[No content extracted]"
                        }
                        
                        corpus.append(document)
                    
                    st.session_state.pdf_corpus = corpus
                    st.success(f"Processed {len(corpus)} PDF documents!")

    # Display available documents
    if st.session_state.pdf_corpus:
        st.subheader("Available Documents")
        for i, doc in enumerate(st.session_state.pdf_corpus, 1):
            with st.expander(f"{i}. {doc['title']}"):
                st.write("**Summary:**")
                st.write(doc['summary'])

# Main chat interface
st.header("Ask about the Research Papers")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input for user question
user_query = st.chat_input("What would you like to know about the thesis papers?")

if user_query:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    # Display user message in chat
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Generate response if corpus is available
    if st.session_state.pdf_corpus:
        with st.chat_message("assistant"):
            with st.spinner("Searching through thesis papers..."):
                response = generate_pdf_rag_response(user_query, st.session_state.pdf_corpus)
            st.markdown(response)
        
        # Add response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
    else:
        with st.chat_message("assistant"):
            st.warning("Please upload or load PDF documents before asking questions.")
        
        # Add warning to chat history
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": "⚠️ Please upload or load PDF documents before asking questions."
        })

# Add footer
st.markdown("---")
st.caption(" CSPC Thesis Library Assistant - Helping you find the right research papers for your needs")
