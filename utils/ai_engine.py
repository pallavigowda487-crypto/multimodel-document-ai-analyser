import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client pointing to Grok (or Groq) API
# xAI's Grok API uses standard OpenAI client library compatibility
GROK_API_KEY = os.environ.get("GROK_API_KEY")

# Default model
MODEL = "grok-beta"

try:
    if GROK_API_KEY and GROK_API_KEY != "your_grok_api_key_here":
        if GROK_API_KEY.startswith("gsk_"):
            base_url = "https://api.groq.com/openai/v1"
            MODEL = "llama-3.3-70b-versatile"
        else:
            base_url = "https://api.x.ai/v1"
            
        client = OpenAI(
            api_key=GROK_API_KEY,
            base_url=base_url,
        )
        
        # Wrap with LangSmith if API key is provided
        if os.environ.get("LANGCHAIN_API_KEY"):
            from langsmith import wrappers
            client = wrappers.wrap_openai(client)
            logger.info("LangSmith tracing enabled.")
    else:
        client = None
        logger.warning("GROK_API_KEY not configured. AI functions will be disabled.")
except Exception as e:
    client = None
    logger.error(f"Failed to initialize API client: {e}")

def call_grok_api(messages: list, temperature: float = 0.7) -> str:
    """Wrapper to call Grok API."""
    if not client:
        return "Error: Grok API key is missing or invalid. Please check your .env settings."
        
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling Grok API: {e}")
        return f"Error communicating with AI service: {str(e)}"

def generate_summary(context: str, detail_level: str = "Medium") -> str:
    """Generates a summary of the provided text context."""
    prompts = {
        "Short": "Provide a very brief, high-level summary of the following content in 2-3 sentences.",
        "Medium": "Provide a comprehensive summary of the main points in the following content.",
        "Detailed": "Provide a very detailed summary of the following content, including key arguments, data points, and nuanced details. Use bullet points."
    }
    
    prompt = prompts.get(detail_level, prompts["Medium"])
    
    messages = [
        {"role": "system", "content": "You are a helpful and intelligent document analysis assistant."},
        {"role": "user", "content": f"{prompt}\n\nContent:\n{context}"}
    ]
    
    return call_grok_api(messages)

def extract_key_points(context: str) -> str:
    """Extracts key points from context."""
    messages = [
        {"role": "system", "content": "You are an expert at extracting the most important information from documents."},
        {"role": "user", "content": f"Extract the key points from the following content as a markdown list:\n\n{context}"}
    ]
    return call_grok_api(messages)

def explain_content(context: str) -> str:
    """Explains complex content simply."""
    messages = [
        {"role": "system", "content": "You are an expert teacher. Explain things simply and clearly."},
        {"role": "user", "content": f"Explain the following content in simple terms as if I am a beginner:\n\n{context}"}
    ]
    return call_grok_api(messages)

def sentiment_analysis(context: str) -> str:
    """Performs sentiment and tone analysis."""
    messages = [
        {"role": "system", "content": "You are an expert in linguistics and psychology."},
        {"role": "user", "content": f"Analyze the sentiment, tone, and underlying emotions of the following content:\n\n{context}"}
    ]
    return call_grok_api(messages)

def ask_question(context: str, question: str, chat_history: list = None) -> str:
    """Answers a specific question based on context, maintaining conversational memory."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use the provided context to answer the user's questions. If the answer is not in the context, say so gracefully but try to be as helpful as possible."}
    ]
    
    if chat_history:
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
    # Always inject context in the current prompt
    messages.append({
        "role": "user", 
        "content": f"Context:\n{context}\n\nQuestion: {question}"
    })
    
    return call_grok_api(messages)
