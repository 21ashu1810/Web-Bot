import streamlit as st
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import google.generativeai as genai
from deep_translator import GoogleTranslator
import re

# Define language codes for translation
LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Arabic": "ar",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Spanish": "es",
    "French": "fr",
    "Arabic": "ar",
    "German": "de"
}

# Initialize Gemini API
genai.configure(api_key='gemini API key')
model = genai.GenerativeModel('gemini-pro')

# Fetching the website content with caching
@st.cache_data()
def fetch_website_content(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch content: {e}")
        return None

def translate_text(text, target_language_code):
    try:
       
        cleaned_text = re.sub(r'[^\w\s]', '', text)
        cleaned_text = ' '.join(cleaned_text.split())
        
       
        chunk_size = 500
        chunks = [cleaned_text[i:i+chunk_size] for i in range(0, len(cleaned_text), chunk_size)]
        
        translator = GoogleTranslator(source='auto', target=target_language_code)
        translated_chunks = [translator.translate(chunk) for chunk in chunks]
        
        return ' '.join(translated_chunks)
    except Exception as e:
        st.error(f"Error in translation: {e}. Please try another language.")
        return text

# Convert text to speech
def text_to_audio(text, lang):
    try:
        tts = gTTS(text=text, lang=lang)
        audio_file = "response.mp3"
        tts.save(audio_file)
        return audio_file
    except ValueError as e:
        st.error(f"Error in generating audio: {e}. Please check the language code.")
        return None

# Extract relevant information from the website
def fetch_relevant_information(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Removing unnecessary tags like scripts, styles, and ads
    for script in soup(["script", "style", "aside", "header", "footer", "nav"]):
        script.extract()

    paragraphs = soup.find_all('p')
    headers = soup.find_all(['h1', 'h2', 'h3'])

    content = " ".join([header.get_text(strip=True) for header in headers])
    content += " ".join([para.get_text(strip=True) for para in paragraphs])

    return content[:2000]  


def process_content(content, user_input):
    try:
        prompt = f"""Based on the following content:

{content}

Please provide a brief summary of the content and then answer this question: {user_input}

Format your response as follows:
Summary: [Your summary here]
Answer: [Your answer to the user's question here]"""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error processing content: {e}")
        return None

# GUI and main function implementation
def main():
    st.set_page_config(page_title="AK", page_icon=":robot_face:")

    st.header("AK ChatBOT :robot_face:")
    st.write("Hello User! How can I assist you today?")

    user_input_url = st.text_input("Please provide a URL:")

    if st.button("Fetch Website Content"):
        website_content = fetch_website_content(user_input_url)
        if website_content:
            st.success("Website content fetched successfully.")
        else:
            st.error("Failed to fetch website content.")

    user_input = st.text_area("Chatbot: How can I assist you?", value="")

    if st.button("Get Response"):
        website_content = fetch_website_content(user_input_url)
        if website_content:
            extracted_info = fetch_relevant_information(website_content)

            if extracted_info:
                try:
                    chatbot_response = process_content(extracted_info, user_input)

                    if chatbot_response:
                        
                        st.session_state.chatbot_response = chatbot_response

                except Exception as e:
                    st.error(f"Error generating response: {e}")
            else:
                st.error("Extracted information is empty. Please check the website content.")
        else:
            st.error("Please fetch valid website content first.")

   
    if 'chatbot_response' in st.session_state:
        st.write("Chatbot:", st.session_state.chatbot_response)

        
        target_language = st.selectbox(
            "Select Language for Audio Output",
            list(LANGUAGE_CODES.keys())
        )

        if target_language:
            st.session_state.target_language = target_language
            target_language_code = LANGUAGE_CODES[target_language]

            
            translated_response = st.session_state.chatbot_response
            if target_language_code != "en":
                try:
                    translated_response = translate_text(st.session_state.chatbot_response, target_language_code)
                    st.write("Translated Response:", translated_response)
                except Exception as e:
                    st.error(f"Translation failed: {e}. Proceeding with English text.")
                    translated_response = st.session_state.chatbot_response

            
            audio_file = text_to_audio(translated_response, lang=target_language_code)

            if audio_file:
                st.audio(audio_file, format="audio/mp3")

                if st.button("Generate Audio in Selected Language"):
                    audio_file = text_to_audio(translated_response, lang=target_language_code)
                    if audio_file:
                        st.audio(audio_file, format="audio/mp3")

if __name__ == '__main__':
    main()
