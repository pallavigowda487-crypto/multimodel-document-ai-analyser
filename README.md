# Multimodal AI Analyzer

A production-ready AI-powered multimodal document intelligence web application using Python, Streamlit, MongoDB, and the Grok API.

## Features
- **Multimodal Support**: Upload PDFs, DOCX, TXT, Images, Audio, and Video files.
- **Conversational AI**: Ask questions about your uploaded content.
- **Insights & Summaries**: Extract key points, generate summaries, perform sentiment analysis, and more.
- **Persistent Storage**: Uploads and chat histories are stored in MongoDB Atlas.

## Local Setup

1. **Clone the repository** (if applicable) or navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Install System Dependencies** (if running locally):
   - **Tesseract OCR**: Required for image text extraction. (Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) for Windows or use `apt-get install tesseract-ocr` on Linux/Mac).
   - **FFmpeg**: Required for audio/video extraction. (Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH).
5. **Set Environment Variables**:
   Copy `.env.example` to `.env` and fill in your keys:
   ```env
   GROK_API_KEY=your_grok_api_key
   MONGODB_URI=your_mongodb_connection_string
   ```
6. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

## Deployment on Streamlit Cloud

1. Push your repository to GitHub.
2. Connect the repository to Streamlit Community Cloud.
3. In the Streamlit Cloud dashboard, go to **Advanced Settings** and add your Secrets:
   ```toml
   GROK_API_KEY = "your_grok_api_key"
   MONGODB_URI = "your_mongodb_connection_string"
   ```
4. Streamlit Cloud will automatically read `packages.txt` to install `tesseract-ocr` and `ffmpeg`, and `requirements.txt` to install Python dependencies.

## Architecture
- **Frontend**: Streamlit
- **Database**: MongoDB Atlas
- **LLM**: Grok API (via `openai` python package)
- **Modularity**: Code is split into specific processor modules (`utils/document_processor.py`, `utils/audio_processor.py`, etc.) for clean scaling.
