# utils/ai_helper.py
import openai
import json
import streamlit as st
import time

# Use the model name provided by the user
AI_MODEL = "gpt-4.1-mini" 
# For development, if "gpt-4.1-mini" is not available via standard API, 
# you might use "gpt-4-turbo-preview" or "gpt-3.5-turbo"
# AI_MODEL = "gpt-4-turbo-preview" 

def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("OpenAI API key not found. Please set it in secrets.toml.")
        return None
    return openai.OpenAI(api_key=api_key)

def summarize_text_with_ai(text_content, purpose="marketing ad copy generation"):
    """Summarizes text using OpenAI, ensuring full context is considered."""
    client = get_openai_client()
    if not client or not text_content:
        return "Error: OpenAI client not initialized or no text to summarize."

    # Simplified prompt for summarization, assuming the model can handle large context.
    # If context is too large, chunking and iterative summarization might be needed,
    # but the user emphasized using full length and not worrying about cost/time.
    prompt = f"""
    Please provide a comprehensive and detailed summary of the following text. 
    The summary should capture all key information, including products, services, 
    unique selling propositions (USPs), target audience, brand voice, and any other 
    relevant details. This summary will be used as the primary context for generating 
    tailored marketing ad copy. Ensure the summary is thorough.

    Text to summarize:
    ---
    {text_content}
    ---
    Comprehensive Summary:
    """
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a highly skilled summarization assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        st.error(f"OpenAI API error during summarization: {e}")
        return f"Error during summarization: {e}"

def generate_content_with_ai(prompt_text, expect_json=True):
    """Generates content using OpenAI, optionally parsing JSON."""
    client = get_openai_client()
    if not client:
        return "Error: OpenAI client not initialized."

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a creative marketing and advertising expert AI."},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.7, # Higher for creative tasks
                # response_format={ "type": "json_object" } if expect_json and model supports it well
            )
            content = response.choices[0].message.content.strip()
            
            if expect_json:
                # Try to find JSON within the content if it's not perfectly formatted
                # This is a common issue with LLMs.
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = content[json_start:json_end]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as je:
                        if attempt < max_retries - 1:
                            time.sleep(2) # Wait before retrying
                            continue
                        st.warning(f"Failed to parse JSON after multiple attempts. Raw content: {content}. Error: {je}")
                        return {"error": "Failed to parse JSON response", "raw_content": content}
                else: # No JSON found
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    st.warning(f"No JSON object found in response after multiple attempts. Raw content: {content}")
                    return {"error": "No JSON object found in response", "raw_content": content}

            return content # Return as text if not expecting JSON
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2) # Wait before retrying
                continue
            st.error(f"OpenAI API error during content generation: {e}")
            return {"error": f"OpenAI API error: {e}"} if expect_json else f"OpenAI API error: {e}"
    return {"error": "Max retries reached for AI content generation"} if expect_json else "Max retries reached for AI content generation"