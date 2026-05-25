import streamlit as st
import os
import hashlib
import time
from uuid import uuid4

# Import utilities
from utils.helpers import setup_directories, cleanup_temp_files, validate_file_size, chunk_text
from utils.database import save_upload_metadata, get_upload_by_hash, save_chat_message, get_chat_history, save_summary
from utils.document_processor import process_document
from utils.image_processor import process_image
from utils.audio_processor import process_audio
from utils.video_processor import process_video
from utils.ai_engine import (
    generate_summary,
    extract_key_points,
    explain_content,
    sentiment_analysis,
    ask_question
)

# Configuration
st.set_page_config(
    page_title="Multimodal AI Analyzer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Custom CSS for Premium Aesthetics (Glassmorphism, Gradients)
st.markdown("""
<style>
    /* Global styles and typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: #f8fafc;
    }

    /* Sidebar glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Upload Box */
    [data-testid="stFileUploadDropzone"] {
        background: rgba(255, 255, 255, 0.03);
        border: 2px dashed rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploadDropzone"]:hover {
        border-color: #8b5cf6;
        background: rgba(139, 92, 246, 0.05);
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
        border: none;
        color: white;
    }

    /* Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.05);
        margin-bottom: 10px;
    }

    /* Input Fields */
    .stTextInput>div>div>input, .stTextArea>div>textarea {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 8px;
    }
    .stTextInput>div>div>input:focus, .stTextArea>div>textarea:focus {
        border-color: #8b5cf6;
        box-shadow: 0 0 0 1px #8b5cf6;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px 8px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.05);
        border-bottom: 2px solid #8b5cf6;
    }
    
    /* Headers */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #a78bfa, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid4())
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""
if 'file_metadata' not in st.session_state:
    st.session_state.file_metadata = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = ""

# Ensure directories exist
setup_directories()

def process_uploaded_file(uploaded_file):
    """Handles saving and processing of the uploaded file."""
    # Check size
    file_bytes = uploaded_file.read()
    if not validate_file_size(len(file_bytes)):
        st.error(f"File {uploaded_file.name} exceeds the 200MB limit.")
        return False
        
    # Generate hash for duplication check
    file_hash = hashlib.md5(file_bytes).hexdigest()
    
    existing_record = get_upload_by_hash(file_hash)
    if existing_record:
        st.info("File previously processed. Loading from database...")
        st.session_state.extracted_text = existing_record.get("extracted_text", "")
        st.session_state.file_metadata = existing_record
        return True

    # Save to temp
    temp_path = os.path.join("temp", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
        
    file_type = uploaded_file.type
    st.session_state.file_metadata = {
        "filename": uploaded_file.name,
        "type": file_type,
        "size": len(file_bytes),
        "file_hash": file_hash,
        "timestamp": time.time()
    }
    
    # Process based on type
    extracted_text = ""
    try:
        with st.spinner(f"Extracting intelligence from {uploaded_file.name}..."):
            if "pdf" in file_type or "word" in file_type or "text" in file_type or file_type == "text/plain":
                extracted_text = process_document(temp_path, file_type.split("/")[-1] if "/" in file_type else file_type)
            elif "image" in file_type:
                extracted_text = process_image(temp_path, file_type)
            elif "audio" in file_type:
                extracted_text = process_audio(temp_path, file_type)
            elif "video" in file_type:
                extracted_text = process_video(temp_path, file_type)
            else:
                st.warning(f"Unsupported file type: {file_type}")
                return False
                
            if not extracted_text:
                st.warning("No text could be extracted from the file.")
            else:
                st.session_state.extracted_text = extracted_text
                st.session_state.file_metadata["extracted_text"] = extracted_text
                # Save to DB
                save_upload_metadata(st.session_state.file_metadata)
                st.success("Extraction complete!")
                
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return False
    finally:
        cleanup_temp_files()
        
    return True

# UI Layout
st.title("🧠 Multimodal AI Analyzer")
st.markdown("Unlock intelligent insights from **Documents, Images, Audio, and Video**.")

# Sidebar
with st.sidebar:
    st.header("📤 Upload Content")
    uploaded_files = st.file_uploader("Drop your files here", 
                                     type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg', 'mp3', 'wav', 'mp4', 'mov'],
                                     accept_multiple_files=False)
    
    st.divider()
    
    st.header("✍️ Direct Text Input")
    manual_text = st.text_area("Paste raw text here")
    if st.button("Process Text"):
        if manual_text:
            st.session_state.extracted_text = manual_text
            st.session_state.file_metadata = {
                "filename": "Manual Input",
                "type": "text/plain",
                "timestamp": time.time()
            }
            st.success("Text processed!")
            
    st.divider()
    if st.button("Reset Session", type="secondary"):
        st.session_state.clear()
        st.rerun()

# Process Uploads
if uploaded_files is not None and (not st.session_state.file_metadata or st.session_state.file_metadata.get("filename") != uploaded_files.name):
    process_uploaded_file(uploaded_files)

# Main Application Area
if st.session_state.extracted_text:
    
    st.markdown(f"**Current Context:** `{st.session_state.file_metadata.get('filename', 'Unknown')}`")
    
    tab1, tab2, tab3 = st.tabs(["📊 Intelligent Analysis", "💬 AI Chat", "📄 Raw Context"])
    
    with tab1:
        st.subheader("Generate Insights")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            analysis_mode = st.selectbox("Select Analysis Mode", 
                                         ["Summarize", "Extract Key Points", "Explain Concept", "Sentiment Analysis", "Custom AI Prompt"])
            
            detail_level = "Medium"
            if analysis_mode == "Summarize":
                detail_level = st.selectbox("Detail Level", ["Short", "Medium", "Detailed"])
                
            custom_prompt = ""
            if analysis_mode == "Custom AI Prompt":
                custom_prompt = st.text_input("Enter your instruction")
                
            if st.button("Generate ✨"):
                with st.spinner("Analyzing context..."):
                    context = st.session_state.extracted_text
                    # Limit context for huge files (very basic chunking for API limits)
                    if len(context) > 20000:
                        context = context[:20000] + "... [Truncated]"
                        st.info("Context truncated for API limits.")
                        
                    result = ""
                    if analysis_mode == "Summarize":
                        result = generate_summary(context, detail_level)
                    elif analysis_mode == "Extract Key Points":
                        result = extract_key_points(context)
                    elif analysis_mode == "Explain Concept":
                        result = explain_content(context)
                    elif analysis_mode == "Sentiment Analysis":
                        result = sentiment_analysis(context)
                    elif analysis_mode == "Custom AI Prompt" and custom_prompt:
                        result = ask_question(context, custom_prompt, [])
                        
                    st.session_state.analysis_results = result
                    save_summary({
                        "session_id": st.session_state.session_id,
                        "mode": analysis_mode,
                        "filename": st.session_state.file_metadata.get("filename"),
                        "result": result
                    })
                    
        with col2:
            st.markdown("### Results")
            if st.session_state.analysis_results:
                st.info(st.session_state.analysis_results)
                
                # Download Button
                st.download_button(
                    label="Download Analysis",
                    data=st.session_state.analysis_results,
                    file_name="analysis.txt",
                    mime="text/plain"
                )
            else:
                st.write("Results will appear here.")
                
    with tab2:
        st.subheader("Chat with your Data")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        # Chat Input
        if prompt := st.chat_input("Ask anything about the uploaded content..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            # Add to DB
            save_chat_message(st.session_state.session_id, "user", prompt)
                
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    context = st.session_state.extracted_text
                    if len(context) > 20000:
                        context = context[:20000]
                        
                    # Format history for Grok
                    api_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history[:-1]]
                    
                    response = ask_question(context, prompt, api_history)
                    st.markdown(response)
                    
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            save_chat_message(st.session_state.session_id, "assistant", response)
            
    with tab3:
        st.subheader("Extracted Content")
        with st.expander("View Raw Extracted Text", expanded=True):
            st.text_area("", st.session_state.extracted_text, height=400, disabled=True)
            
else:
    # Landing View
    st.markdown("""
    <div style="text-align: center; padding: 50px 20px;">
        <h2>Welcome to the Next Generation of Document Intelligence</h2>
        <p style="color: #94a3b8; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
            Upload your files via the sidebar or paste text to get started. Our AI can seamlessly read PDFs, 
            understand Word documents, transcribe Audio, extract text from Images, and parse Videos.
        </p>
    </div>
    """, unsafe_allow_html=True)
