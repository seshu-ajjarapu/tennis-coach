import streamlit as st
import google.generativeai as genai
import time
import os

# 1. Configure Page
st.set_page_config(page_title="AI Tennis Coach", page_icon="🎾")
st.title("🎾 AI Tennis Coach")
st.write("Upload a video of your rally to get pro-level feedback.")

# 2. API Setup (Securely from Streamlit Secrets)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("Missing API Key. Please set it in Streamlit Secrets.")
    st.stop()

# 3. File Uploader
uploaded_file = st.file_uploader("Upload a video (MP4, MOV)", type=["mp4", "mov"])

if uploaded_file is not None:
    # Save the uploaded file locally so we can send it to Google
    temp_filename = "temp_tennis_video.mp4"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("File uploaded! Processing...")
    
    # --- AUTO-SELECT MODEL (Using your Future-Proof Logic) ---
    model_name = "models/gemini-1.5-flash" # Default fallback
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            if 'flash' in m.name:
                model_name = m.name
                break
    # -------------------------------------------------------

    # 4. Upload to Gemini
    with st.spinner(f"Sending video to AI ({model_name})..."):
        try:
            video_file = genai.upload_file(path=temp_filename)
        except Exception as e:
            st.error(f"Upload failed: {e}")
            st.stop()

    # 5. Polling Loop
    status_text = st.empty()
    start_time = time.time()
    
    while True:
        video_file = genai.get_file(video_file.name)
        if video_file.state.name == "ACTIVE":
            break
        elif video_file.state.name == "FAILED":
            st.error("Google failed to process the video.")
            st.stop()
            
        status_text.text("Coach is watching the video... (Parsing pixels)")
        time.sleep(2)
        
        if time.time() - start_time > 120:
            st.error("Timeout: Video is too large or Google is busy.")
            st.stop()

    status_text.text("✅ Ready! Analyzing form...")

    # 6. Generate Analysis
    model = genai.GenerativeModel(model_name=model_name)
    prompt = """
    You are an elite, old-school tennis coach (think Toni Nadal). 
    Analyze this PROFESSIONAL player.
    1. Identify the stroke.
    2. Find 3 biomechanical inefficiencies.
    3. Prescribe 3 specific drills.
    Use Markdown.
    """
    
    response = model.generate_content([video_file, prompt])
    
    # 7. Display Result
    st.markdown("## 📋 Coach's Report")
    st.markdown(response.text)
    
    # Cleanup
    try:
        genai.delete_file(video_file.name)
        os.remove(temp_filename)
    except:
        pass