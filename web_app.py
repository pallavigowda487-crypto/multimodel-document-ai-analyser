import os
import hashlib
import time
from uuid import uuid4

from flask import Flask, redirect, render_template_string, request, session, url_for

from utils.ai_engine import ask_question, explain_content, extract_key_points, generate_summary, sentiment_analysis
from utils.audio_processor import process_audio
from utils.database import get_chat_history, get_upload_by_hash, save_chat_message, save_summary, save_upload_metadata
from utils.document_processor import process_document
from utils.helpers import cleanup_temp_files, setup_directories, validate_file_size
from utils.image_processor import process_image
from utils.video_processor import process_video

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-secret")

setup_directories()

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Multimodal AI Analyzer</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Arial, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
    }
    body { margin: 0; background: linear-gradient(135deg, #0f172a, #1e1b4b); min-height: 100vh; }
    .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
    .hero { padding: 20px 0 28px; }
    .hero h1 { margin: 0 0 8px; font-size: 2rem; }
    .hero p { margin: 0; color: #cbd5e1; line-height: 1.6; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .panel { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 20px; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.25); }
    .panel h2 { margin-top: 0; font-size: 1.1rem; }
    form { display: flex; flex-direction: column; gap: 12px; }
    input, textarea, select, button { font: inherit; border-radius: 10px; border: 1px solid rgba(148, 163, 184, 0.25); padding: 12px; background: rgba(15, 23, 42, 0.75); color: #f8fafc; }
    textarea { min-height: 150px; resize: vertical; }
    button { background: linear-gradient(90deg, #8b5cf6, #3b82f6); color: white; border: 0; cursor: pointer; font-weight: 700; }
    button.secondary { background: linear-gradient(90deg, #334155, #475569); }
    .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .status { padding: 12px 14px; border-radius: 12px; margin-bottom: 16px; }
    .status.success { background: rgba(16, 185, 129, 0.12); color: #86efac; border: 1px solid rgba(16, 185, 129, 0.3); }
    .status.error { background: rgba(248, 113, 113, 0.12); color: #fecaca; border: 1px solid rgba(248, 113, 113, 0.25); }
    .muted { color: #94a3b8; font-size: 0.95rem; }
    .chat { display: flex; flex-direction: column; gap: 12px; margin-top: 12px; }
    .message { border-radius: 12px; padding: 12px 14px; background: rgba(30, 41, 59, 0.9); border: 1px solid rgba(148, 163, 184, 0.18); }
    .message.user { border-color: rgba(99, 102, 241, 0.45); }
    .message.assistant { border-color: rgba(59, 130, 246, 0.45); }
    .meta { color: #94a3b8; font-size: 0.9rem; margin-bottom: 6px; }
    .analysis { white-space: pre-wrap; line-height: 1.6; }
    .context-box { margin-top: 12px; }
    .file-meta { color: #cbd5e1; margin-top: 8px; }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <h1>🧠 Multimodal AI Analyzer</h1>
      <p>Upload documents, images, audio, or video and ask questions through a regular web interface. This version runs without Streamlit.</p>
    </div>

    {% if message %}
      <div class="status success">{{ message }}</div>
    {% endif %}
    {% if error %}
      <div class="status error">{{ error }}</div>
    {% endif %}

    <div class="grid">
      <div class="panel">
        <h2>📤 Upload or paste content</h2>
        <form method="post" action="{{ url_for('upload_file') }}" enctype="multipart/form-data">
          <label>Upload file
            <input type="file" name="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.mp3,.wav,.mp4,.mov">
          </label>
          <button type="submit">Process upload</button>
        </form>

        <form method="post" action="{{ url_for('process_text') }}" style="margin-top: 16px;">
          <label for="manual_text">Direct text input</label>
          <textarea id="manual_text" name="manual_text" placeholder="Paste raw text here">{{ manual_text or '' }}</textarea>
          <button type="submit">Process text</button>
        </form>

        <div class="row" style="margin-top: 16px;">
          <form method="post" action="{{ url_for('reset_session') }}">
            <button type="submit" class="secondary">Reset session</button>
          </form>
        </div>

        {% if file_metadata %}
          <div class="file-meta">
            <strong>Current file:</strong> {{ file_metadata.filename }}<br>
            <strong>Type:</strong> {{ file_metadata.type }}
          </div>
        {% endif %}
      </div>

      <div class="panel">
        <h2>📊 Analysis</h2>
        <form method="post" action="{{ url_for('analyze') }}">
          <label>Analysis mode
            <select name="analysis_mode">
              <option value="Summarize" {% if analysis_mode == 'Summarize' %}selected{% endif %}>Summarize</option>
              <option value="Extract Key Points" {% if analysis_mode == 'Extract Key Points' %}selected{% endif %}>Extract key points</option>
              <option value="Explain Concept" {% if analysis_mode == 'Explain Concept' %}selected{% endif %}>Explain concept</option>
              <option value="Sentiment Analysis" {% if analysis_mode == 'Sentiment Analysis' %}selected{% endif %}>Sentiment analysis</option>
              <option value="Custom AI Prompt" {% if analysis_mode == 'Custom AI Prompt' %}selected{% endif %}>Custom AI prompt</option>
            </select>
          </label>
          <label>Detail level
            <select name="detail_level">
              <option value="Short" {% if detail_level == 'Short' %}selected{% endif %}>Short</option>
              <option value="Medium" {% if detail_level == 'Medium' %}selected{% endif %}>Medium</option>
              <option value="Detailed" {% if detail_level == 'Detailed' %}selected{% endif %}>Detailed</option>
            </select>
          </label>
          <label>Custom prompt
            <input type="text" name="custom_prompt" value="{{ custom_prompt or '' }}" placeholder="Optional instructions for a custom prompt">
          </label>
          <button type="submit">Generate insights</button>
        </form>

        {% if analysis_results %}
          <div class="analysis" style="margin-top: 16px;">
            <div class="meta">Analysis result</div>
            <div>{{ analysis_results }}</div>
          </div>
        {% else %}
          <p class="muted" style="margin-top: 16px;">Results will appear here after analysis.</p>
        {% endif %}
      </div>
    </div>

    <div class="panel context-box">
      <h2>📄 Extracted context</h2>
      {% if extracted_text %}
        <textarea readonly>{{ extracted_text }}</textarea>
      {% else %}
        <p class="muted">Upload a file or paste text to populate the context.</p>
      {% endif %}
    </div>

    <div class="panel" style="margin-top: 20px;">
      <h2>💬 Chat with your data</h2>
      <form method="post" action="{{ url_for('chat') }}">
        <label>Ask a question
          <input type="text" name="prompt" placeholder="Ask about the uploaded content" value="{{ prompt or '' }}">
        </label>
        <button type="submit">Send message</button>
      </form>
      <div class="chat">
        {% for msg in chat_history %}
          <div class="message {{ msg.role }}">
            <div class="meta">{{ msg.role }}</div>
            <div>{{ msg.content }}</div>
          </div>
        {% else %}
          <p class="muted">Chat history will appear here once you ask a question.</p>
        {% endfor %}
      </div>
    </div>
  </div>
</body>
</html>
"""


def ensure_session():
    if "session_id" not in session:
        session["session_id"] = str(uuid4())
    if "chat_history" not in session:
        session["chat_history"] = []
    if "analysis_results" not in session:
        session["analysis_results"] = ""
    if "extracted_text" not in session:
        session["extracted_text"] = ""


def get_file_type(file_storage):
    mimetype = (file_storage.mimetype or "").lower()
    filename = (file_storage.filename or "").lower()

    if "pdf" in mimetype or filename.endswith(".pdf"):
        return "pdf"
    if "docx" in mimetype or filename.endswith(".docx"):
        return "docx"
    if "text/plain" in mimetype or filename.endswith(".txt"):
        return "text/plain"
    if mimetype.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg")):
        return mimetype or "image"
    if mimetype.startswith("audio/") or filename.endswith((".mp3", ".wav")):
        return mimetype or "audio"
    if mimetype.startswith("video/") or filename.endswith((".mp4", ".mov")):
        return mimetype or "video"
    return mimetype or "unknown"


def sanitize_file_metadata(metadata):
    if not isinstance(metadata, dict):
        return {}

    sanitized = {}
    for key in ("filename", "type", "size", "file_hash", "timestamp", "extracted_text"):
        if key in metadata:
            sanitized[key] = metadata[key]
    return sanitized


def process_uploaded_file_storage(file_storage):
    file_bytes = file_storage.read()
    if not validate_file_size(len(file_bytes)):
        return False, f"File {file_storage.filename} exceeds the 200MB limit."

    file_hash = hashlib.md5(file_bytes).hexdigest()
    existing_record = get_upload_by_hash(file_hash)
    if existing_record:
        sanitized_metadata = sanitize_file_metadata(existing_record)
        session["extracted_text"] = sanitized_metadata.get("extracted_text", "")
        session["file_metadata"] = sanitized_metadata
        return True, "File previously processed. Loading from database..."

    temp_name = f"{uuid4().hex}_{file_storage.filename}"
    temp_path = os.path.join("temp", temp_name)

    with open(temp_path, "wb") as handle:
        handle.write(file_bytes)

    file_type = get_file_type(file_storage)
    metadata = {
        "filename": file_storage.filename,
        "type": file_storage.mimetype or file_type,
        "size": len(file_bytes),
        "file_hash": file_hash,
        "timestamp": time.time(),
    }

    try:
        if file_type in {"pdf", "docx", "text/plain"}:
            extracted_text = process_document(temp_path, file_type)
        elif file_type.startswith("image/") or file_type in {"image", "png", "jpg", "jpeg"}:
            extracted_text = process_image(temp_path, file_type)
        elif file_type.startswith("audio/") or file_type in {"audio", "mp3", "wav"}:
            extracted_text = process_audio(temp_path, file_type)
        elif file_type.startswith("video/") or file_type in {"video", "mp4", "mov"}:
            extracted_text = process_video(temp_path, file_type)
        else:
            return False, f"Unsupported file type: {file_storage.mimetype or file_type}"

        if not extracted_text:
            return False, "No text could be extracted from the file."

        session["extracted_text"] = extracted_text
        metadata["extracted_text"] = extracted_text
        session["file_metadata"] = sanitize_file_metadata(metadata)
        save_upload_metadata(metadata)
        return True, "Extraction complete!"
    except Exception as exc:
        return False, f"Error processing file: {exc}"
    finally:
        cleanup_temp_files()


@app.route("/")
def index():
    ensure_session()
    return render_template_string(
        HTML,
        message=session.pop("message", None),
        error=session.pop("error", None),
        extracted_text=session.get("extracted_text", ""),
        file_metadata=session.get("file_metadata"),
        chat_history=session.get("chat_history", []),
        analysis_results=session.get("analysis_results", ""),
        analysis_mode=session.get("analysis_mode", "Summarize"),
        detail_level=session.get("detail_level", "Medium"),
        custom_prompt=session.get("custom_prompt", ""),
        manual_text=session.get("manual_text", ""),
        prompt=session.get("prompt", ""),
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    ensure_session()
    file_storage = request.files.get("file")
    if not file_storage or file_storage.filename == "":
        session["error"] = "Please select a file to upload."
        return redirect(url_for("index"))

    success, message = process_uploaded_file_storage(file_storage)
    if success:
        session["message"] = message
    else:
        session["error"] = message
    return redirect(url_for("index"))


@app.route("/process_text", methods=["POST"])
def process_text():
    ensure_session()
    text = request.form.get("manual_text", "").strip()
    if not text:
        session["error"] = "Please enter some text to process."
        return redirect(url_for("index"))

    session["extracted_text"] = text
    session["file_metadata"] = {
        "filename": "Manual Input",
        "type": "text/plain",
        "timestamp": time.time(),
    }
    session["message"] = "Text processed!"
    return redirect(url_for("index"))


@app.route("/analyze", methods=["POST"])
def analyze():
    ensure_session()
    context = session.get("extracted_text", "")
    if not context:
        session["error"] = "Upload or paste content before analyzing."
        return redirect(url_for("index"))

    analysis_mode = request.form.get("analysis_mode", "Summarize")
    detail_level = request.form.get("detail_level", "Medium")
    custom_prompt = request.form.get("custom_prompt", "").strip()

    session["analysis_mode"] = analysis_mode
    session["detail_level"] = detail_level
    session["custom_prompt"] = custom_prompt

    if len(context) > 20000:
        context = context[:20000] + "... [Truncated]"

    result = ""
    try:
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
        elif analysis_mode == "Custom AI Prompt":
            result = "Please enter a custom prompt to continue."
        else:
            result = "Unsupported analysis mode."
    except Exception as exc:
        session["error"] = f"Error generating analysis: {exc}"
        return redirect(url_for("index"))

    session["analysis_results"] = result
    save_summary({
        "session_id": session["session_id"],
        "mode": analysis_mode,
        "filename": session.get("file_metadata", {}).get("filename") if session.get("file_metadata") else None,
        "result": result,
    })
    session["message"] = "Analysis complete!"
    return redirect(url_for("index"))


@app.route("/chat", methods=["POST"])
def chat():
    ensure_session()
    prompt = request.form.get("prompt", "").strip()
    if not prompt:
        session["error"] = "Please enter a question."
        return redirect(url_for("index"))

    context = session.get("extracted_text", "")
    if not context:
        session["error"] = "Upload or paste content before chatting."
        return redirect(url_for("index"))

    session["prompt"] = prompt
    session["chat_history"].append({"role": "user", "content": prompt})
    save_chat_message(session["session_id"], "user", prompt)

    history = [{"role": msg["role"], "content": msg["content"]} for msg in session["chat_history"][:-1]]
    if len(context) > 20000:
        context = context[:20000]

    try:
        response = ask_question(context, prompt, history)
    except Exception as exc:
        session["error"] = f"Error generating response: {exc}"
        return redirect(url_for("index"))

    session["chat_history"].append({"role": "assistant", "content": response})
    save_chat_message(session["session_id"], "assistant", response)
    session["message"] = "Response generated!"
    return redirect(url_for("index"))


@app.route("/reset", methods=["POST"])
def reset_session():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
