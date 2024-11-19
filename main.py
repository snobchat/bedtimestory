import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import tempfile

load_dotenv()

# Configure constants
GENRES = [
    "Fantasy", "Adventure", "Fairy Tale", "Science Fiction", 
    "Mystery", "Superhero", "Animal Tales", "Mythology"
]

TONES = [
    "Exciting", "Calm", "Funny", "Inspirational", 
    "Mysterious", "Heartwarming"
]

SETTINGS = [
    "Magical Kingdom", "Outer Space", "Underwater World", 
    "Enchanted Forest", "Futuristic City", "Ancient Civilization"
]

CHARACTER_TYPES = [
    "Human Child", "Animal", "Superhero", "Magical Creature", 
    "Robot", "Mythical Being"
]

CHARACTER_TRAITS = [
    "Brave", "Curious", "Kind", "Clever", "Adventurous", 
    "Shy", "Funny"
]

THEMES = [
    "Friendship", "Courage", "Honesty", "Teamwork", 
    "Perseverance", "Kindness", "Responsibility", "Acceptance"
]

STORY_LENGTHS = [
    "Short (5 minutes)", 
    "Medium (10 minutes)", 
    "Long (15 minutes)"
]

def init_session_state():
    """Initialize session state variables"""
    if 'api_key_submitted' not in st.session_state:
        st.session_state.api_key_submitted = False
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'current_story' not in st.session_state:
        st.session_state.current_story = None

def validate_api_key(api_key: str) -> bool:
    """Test if the provided API key is valid"""
    try:
        client = OpenAI(api_key=api_key)
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return True
    except Exception as e:
        return False

def api_key_form():
    """Display API key input form"""
    st.title("🔑 OpenAI API Key Required")
    st.write("""
    To use this Bedtime Story Generator, you'll need an OpenAI API key.
    If you don't have one, you can get it from: https://platform.openai.com/account/api-keys
    """)
    
    with st.form("api_key_form"):
        api_key = st.text_input("Enter your OpenAI API key:", type="password")
        submitted = st.form_submit_button("Submit")
        
        if submitted:
            if api_key:
                if validate_api_key(api_key):
                    st.session_state.client = OpenAI(api_key=api_key)
                    st.session_state.api_key_submitted = True
                    st.rerun()
                else:
                    st.error("Invalid API key. Please check and try again.")
            else:
                st.error("Please enter an API key.")

def generate_content(client: OpenAI, story_params: dict) -> str:
    """Generate story content using OpenAI's API"""
    prompt = f"""Write a bedtime story with the following specifications:
    Genre: {story_params['genre']}
    Tone: {story_params['tone']}
    Setting: {story_params['setting']}
    Main Character: A {story_params['character_type']} who is {', '.join(story_params['character_traits'])}
    Character Name: {story_params['character_name']}
    Themes to include: {', '.join(story_params['themes'])}
    Story Length: {story_params['length']}
    
    Additional details to incorporate: {story_params['additional_details'] if story_params['additional_details'] else 'None'}
    
    The story should be engaging and appropriate for children at bedtime.
    Make sure to incorporate the selected themes naturally into the story.
    If specific character names are provided, use them appropriately in the story.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating story: {str(e)}")
        return None

def generate_audio(client: OpenAI, text: str) -> str:
    """Generate audio from text using OpenAI's text-to-speech API"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            response = client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=text
            )
            response.stream_to_file(tmp_file.name)
            return tmp_file.name
    except Exception as e:
        st.error(f"Error generating audio: {str(e)}")
        return None

def story_generator_interface():
    """Main story generator interface"""
    st.title("📚 Enhanced Bedtime Story Generator")
    
    # Add reset API key button in sidebar
    if st.sidebar.button("Change API Key"):
        st.session_state.api_key_submitted = False
        st.session_state.client = None
        st.rerun()
    
    # Create two columns for input
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Story Elements")
        
        # Basic story parameters
        genre = st.selectbox("Select genre:", GENRES)
        tone = st.selectbox("Select story tone:", TONES)
        setting = st.selectbox("Select story setting:", SETTINGS)
        
        # Character creation
        st.subheader("Main Character")
        character_name = st.text_input("Character's name:")
        character_type = st.selectbox("Character type:", CHARACTER_TYPES)
        character_traits = st.multiselect(
            "Select character traits (up to 3):",
            CHARACTER_TRAITS,
            max_selections=3
        )
    
    with col2:
        st.subheader("Story Details")
        themes = st.multiselect(
            "Select themes to include (up to 3):",
            THEMES,
            max_selections=3
        )
        
        length = st.selectbox("Story length:", STORY_LENGTHS)
        
        additional_details = st.text_area(
            "Any additional details to include? (optional)",
            height=100
        )
    
    if st.button("Generate Story"):
        if not all([genre, tone, setting, character_type, character_traits, themes]):
            st.warning("Please fill in all required fields")
            return
        
        story_params = {
            'genre': genre,
            'tone': tone,
            'setting': setting,
            'character_name': character_name if character_name else 'the protagonist',
            'character_type': character_type,
            'character_traits': character_traits,
            'themes': themes,
            'length': length,
            'additional_details': additional_details
        }
        
        with st.spinner("Creating your story..."):
            generated_content = generate_content(st.session_state.client, story_params)
            
            if generated_content:
                st.session_state.current_story = generated_content
                st.success("Story generated successfully!")
                
                # Display the text content
                st.subheader("Your Story:")
                st.write(generated_content)
                
                # Generate and display audio
                with st.spinner("Converting story to speech..."):
                    audio_file = generate_audio(st.session_state.client, generated_content)
                    if audio_file:
                        st.success("Audio generated successfully!")
                        st.subheader("Listen to your story:")
                        st.audio(audio_file)
                        
                        # Add download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            with open(audio_file, 'rb') as f:
                                st.download_button(
                                    label="Download Audio",
                                    data=f,
                                    file_name="bedtime_story.mp3",
                                    mime="audio/mp3"
                                )
                        with col2:
                            st.download_button(
                                label="Download Story Text",
                                data=generated_content,
                                file_name="bedtime_story.txt",
                                mime="text/plain"
                            )
                        
                        # Clean up temporary file
                        os.unlink(audio_file)

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Bedtime Story Generator",
        page_icon="📚",
        layout="wide"
    )
    
    init_session_state()
    
    if not st.session_state.api_key_submitted:
        api_key_form()
    else:
        story_generator_interface()

if __name__ == "__main__":
    main()
