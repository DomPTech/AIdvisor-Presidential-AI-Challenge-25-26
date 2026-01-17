import streamlit as st
import os
from datetime import datetime
from st_audiorec import st_audiorec
import speech_recognition as sr
import io
from pydub import AudioSegment
from app.chatbot.chatbot import DisasterAgent
from st_supabase_connection import SupabaseConnection
import json

st.set_page_config(page_title="Audio Recorder", layout="wide")

st.title("Audio Recorder")

st.markdown("""
Record audio directly from your browser on any device (desktop, tablet, or mobile).
""")

# Initialize Supabase connection
@st.cache_resource
def get_supabase_conn():
    try:
        return st.connection("supabase", type=SupabaseConnection)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

# Initialize chatbot for parsing transcripts
@st.cache_resource
def get_chatbot():
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
    if not hf_token:
        st.warning("⚠️ HuggingFace API Token not found in environment.")
        return None
    return DisasterAgent(api_token=hf_token)

def transcribe_audio(audio_data, audio_format="wav"):
    """Transcribe audio using Google Speech Recognition API"""
    try:
        recognizer = sr.Recognizer()
        
        # Convert audio data to AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=audio_format)
        
        # Convert to wav format if needed
        if audio_format != "wav":
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)
            audio_data = wav_io.read()
        
        # Convert AudioSegment to raw audio frames
        audio_io = io.BytesIO()
        audio.export(audio_io, format="wav")
        audio_io.seek(0)
        
        # Load audio file for recognition
        with sr.AudioFile(audio_io) as source:
            audio_content = recognizer.record(source)
        
        # Recognize speech using Google Speech Recognition
        text = recognizer.recognize_google(audio_content)
        
        return text
    except sr.UnknownValueError:
        return "❌ Could not understand the audio. Please try again with clearer speech."
    except sr.RequestError as e:
        return f"❌ Error connecting to speech recognition service: {e}"
    except Exception as e:
        return f"❌ Error processing audio: {e}"

def create_bounty_from_transcription(transcribed_text):
    """Convert transcribed text into a structured bounty using AI"""
    st.subheader("📋 AI-Generated Bounty from Transcription")
    st.markdown("The AI has processed your audio. Review and edit the structured data below:")
    
    # Generate structured data using chatbot
    if "generated_bounty" not in st.session_state:
        chatbot = get_chatbot()
        if chatbot:
            with st.spinner("🤖 Analyzing transcription with AI..."):
                prompt = f"""Analyze the following disaster/emergency transcription and extract structured information.
                
Transcription: {transcribed_text}

Return ONLY a JSON object with these exact fields (no markdown, no explanation):
{{
    "location": "specific location extracted from text (city, state/region)",
    "disaster_type": "one of: General, Flood, Hurricane, Wildfire, Earthquake, Tornado, Winter Storm, Other",
    "severity": number from 1-10 based on context,
    "description": "the original transcription text"
}}

If any field cannot be determined from the transcription, use reasonable defaults:
- location: "Unknown Location"
- disaster_type: "General"
- severity: 5"""
                
                response = chatbot.get_response(prompt)
                
                # Extract JSON from response
                try:
                    # Try to parse the response as JSON
                    bounty_data = json.loads(response)
                except json.JSONDecodeError:
                    # Try to extract JSON from the response if it contains extra text
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        bounty_data = json.loads(json_match.group())
                    else:
                        bounty_data = {
                            "location": "Unknown Location",
                            "disaster_type": "General",
                            "severity": 5,
                            "description": transcribed_text
                        }
                
                st.session_state.generated_bounty = bounty_data
        else:
            st.error("❌ Cannot generate bounty without HuggingFace API Token")
            return
    
    # Display editable form
    bounty = st.session_state.generated_bounty
    
    col1, col2 = st.columns(2)
    
    with col1:
        location = st.text_input("📍 Location", value=bounty.get("location", "Unknown Location"), key="bounty_location")
        disaster_type = st.selectbox(
            "🚨 Disaster Type",
            ["General", "Flood", "Hurricane", "Wildfire", "Earthquake", "Tornado", "Winter Storm", "Other"],
            index=["General", "Flood", "Hurricane", "Wildfire", "Earthquake", "Tornado", "Winter Storm", "Other"].index(
                bounty.get("disaster_type", "General")
            ) if bounty.get("disaster_type") in ["General", "Flood", "Hurricane", "Wildfire", "Earthquake", "Tornado", "Winter Storm", "Other"] else 0
        )
    
    with col2:
        severity = st.slider("⚠️ Severity Level", 1, 10, value=int(bounty.get("severity", 5)), key="bounty_severity")
    
    # Display editable description
    description = st.text_area("📝 Description", value=bounty.get("description", transcribed_text), height=150, key="bounty_description")
    
    # Display preview of the bounty
    st.markdown("**Preview:**")
    with st.container(border=True):
        st.write(f"**Location:** {location}")
        st.write(f"**Type:** {disaster_type}")
        st.write(f"**Severity:** {severity}/10")
        st.write(f"**Description:**\n{description}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Post to Bounty Board", key="post_bounty"):
            # Check for user login
            user_id = st.session_state.get("user_id")
            if not user_id:
                st.error("❌ You must be logged in to post bounties.")
            elif not location or location == "Unknown Location":
                st.error("❌ Please specify a location to post bounties.")
            else:
                # Parse lat/lon from location (simplified - just use defaults)
                # In a real app, you'd geocode the location
                lat, lon = 0.0, 0.0
                
                conn = get_supabase_conn()
                if conn:
                    with st.spinner("🌐 Posting bounty to Supabase..."):
                        try:
                            conn.table("help_requests").insert({
                                "poster_id": user_id,
                                "content": description,
                                "lat": lat,
                                "long": lon,
                                "disaster_type": disaster_type,
                                "urgency": severity,
                                "location": location,
                                "created_at": datetime.now().isoformat()
                            }).execute()
                            st.success(f"✅ Bounty posted successfully from '{location}'!")
                            st.balloons()
                            # Clear session state
                            st.session_state.transcribed_text = ""
                            st.session_state.generated_bounty = None
                        except Exception as e:
                            st.error(f"❌ Failed to post bounty: {e}")
    
    with col2:
        if st.button("📋 Copy as JSON", key="copy_json"):
            final_bounty = {
                "location": location,
                "disaster_type": disaster_type,
                "severity": severity,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            st.code(json.dumps(final_bounty, indent=2), language="json")
    
    with col3:
        if st.button("🔄 Clear & Regenerate", key="clear_bounty"):
            st.session_state.transcribed_text = ""
            st.session_state.generated_bounty = None
            st.rerun()

wav_audio_data = st_audiorec()

if wav_audio_data is not None:
    st.audio(wav_audio_data, format='audio/wav')
    
    # Transcribe recorded audio
    if st.button("Transcribe Recording", key="transcribe_recorded"):
        with st.spinner("🎤 Recording processing... 🔄 Transcribing audio..."):
            transcribed_text = transcribe_audio(wav_audio_data, audio_format="wav")
        st.session_state.transcribed_text = transcribed_text
    
    if "transcribed_text" in st.session_state:
        st.subheader("✨ Transcription")
        st.text_area("Transcribed Text:", value=st.session_state.transcribed_text, height=150, disabled=False, key="transcription_display")
        
        # Show bounty creation interface
        st.divider()
        create_bounty_from_transcription(st.session_state.transcribed_text)

st.divider()