import os
import openai
import PyPDF2
import glob
from pathlib import Path
import numpy as np
import re

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
                
                # Limit extraction to first 10 pages to avoid processing huge PDFs
                if page_num >= 9:  # Already processed first 10 pages (0-9)
                    text += "\n[Note: Only the first 10 pages were processed for brevity]"
                    break
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return f"[Error processing {os.path.basename(pdf_path)}]"

def get_pdf_files(directory='.'):
    """Get a list of PDF files in the current directory"""
    pdf_files = []
    for pdf_file in glob.glob(os.path.join(directory, '*.pdf')):
        pdf_files.append(pdf_file)
    return pdf_files

def create_pdf_corpus():
    """Create a corpus by extracting text from available PDF files"""
    pdf_files = get_pdf_files()
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return []
    
    print(f"Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        print(f"- {os.path.basename(pdf)}")
    
    corpus = []
    for pdf_path in pdf_files:
        pdf_name = os.path.basename(pdf_path)
        print(f"Processing {pdf_name}...")
        
        # Extract text from the PDF
        text = extract_text_from_pdf(pdf_path)
        
        # Create document entry with metadata
        document = {
            'title': pdf_name,
            'path': pdf_path,
            'content': text,
            'summary': summarize_text(text[:5000]) if text else "[No content extracted]"
        }
        
        corpus.append(document)
    
    return corpus

def summarize_text(text, max_length=200):
    """Create a brief summary of the text using the first part"""
    if not text:
        return "[No content available]"
        
    # Get the first few sentences or paragraph
    text = text.strip()
    summary = text[:max_length]
    
    # Make sure we don't cut words
    if len(text) > max_length:
        summary = summary[:summary.rfind(' ')] + '...'
        
    return summary

# Initialize the OpenAI client
client = openai.OpenAI(
    api_key="fAaHJwAYLY_D6HzVyTJ2Hr7Ve8KjKg1WT5sV5oFxGBA",
    base_url="https://api.brilliantai.co"
)

def generate_pdf_rag_response(user_query, pdf_corpus):
    """Generate response from LLM with access to PDF corpus"""
    
    if not pdf_corpus:
        return "No PDF documents were processed. Please add PDF files to the directory and run the notebook again."

    # Format the corpus information as context
    corpus_formatted = ""
    for i, doc in enumerate(pdf_corpus, start=1):
        corpus_formatted += f"Document {i}: {doc['title']}\n"
        corpus_formatted += f"Summary: {doc['summary']}\n\n"
        
        # Add a sample of the content (first 1000 chars)
        if len(doc['content']) > 0:
            content_sample = doc['content'][:1000].replace('\n', ' ').strip()
            corpus_formatted += f"Content sample: {content_sample}...\n\n"
            
    # Create a system message that includes the PDF corpus information
    #system_message = f"""You are a knowledgeable academic research assistant. You have access to the following PDF documents:\n{corpus_formatted}\n\nHelp users find relevant information based on their interests. When responding, first analyze the user's query, then identify the most relevant documents from the corpus, and explain why they are relevant. Refer to specific content from the documents when possible."""
    system_message = f"""You are a knowledgeable academic research assistant. You have access to the following PDF documents:\n{corpus_formatted}\n\n
                        Help users find relevant information based on their interests. Identify the most relevant documents from the corpus, and explain
                        why they are relevant. Refer to specific content from the documents when possible."""

    # Create a prompt for the user query
    # prompt = f"""I'm interested in information related to: \"{user_query}\".
    #             Please help me find the most relevant information from the PDF documents, and explain:
    #             1. Which documents are most relevant to my interest and why
    #             2. How the content of these documents relates to my query
    #             3. Specific insights or findings from these documents that address my query
    #             4. Any connections between different documents that might be valuable
    #             5. Finally, add one simple sentence that tells user the most relevant document title you found"""

    prompt = f"""I'm interested in information related to: \"{user_query}\".
            Please help me find the most relevant information from the PDF documents, and explain:
            1. Which documents are most relevant to my interest and why (2 sentences in new line)
            2. How the content of these documents relates to my query
            3. Specific insights or findings from these documents that address my query (one sentence in new line)
            4. Any connections between different documents that might be valuable (one sentence in new line)
            5. Finally, add one simple sentence that tells user the most relevant document title you found (one sentence in new line)
            """

    # Generate the response
    response = client.chat.completions.create(
        model="DeepSeek-R1",
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=800,  # Increased for more comprehensive responses
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    
    return response.choices[0].message.content

# This code only runs when the script is executed directly, not when imported
if __name__ == "__main__":
    # Create the corpus from PDF files
    pdf_corpus = create_pdf_corpus()

    # Display summary information about the processed PDFs
    print(f"\nProcessed {len(pdf_corpus)} PDF documents:")
    for i, doc in enumerate(pdf_corpus, start=1):
        print(f"{i}. {doc['title']}")
        print(f"   Summary: {doc['summary']}")
        print()

    user_input = input("Please enter your research topic or question: ")

    # Get response from the PDF RAG system
    pdf_response = generate_pdf_rag_response(user_input, pdf_corpus)

    # Display the LLM's response
    print("\nGenerated response based on PDF documents:")
    print(pdf_response)