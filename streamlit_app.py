import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import io

st.set_page_config(page_title="Jawline Analyzer Service", page_icon="💎")

# --- AUTHENTICATION ---
def get_user_from_link():
    """Extracts the User ID from the magic link."""
    # Get ID from URL ?uid=12345
    query_params = st.query_params
    user_id = query_params.get("uid", None)
    
    # Load paid users from Secrets
    active_subscribers = st.secrets.get("allowed_users", {})
    
    if user_id and user_id in active_subscribers:
        return user_id, active_subscribers[user_id]
    return None, None

# Try to log in
user_id, user_name = get_user_from_link()

if not user_id:
    st.error("⛔ Access Denied")
    st.warning("You need a personal subscription link to use this tool.")
    st.info("Contact the admin on Telegram to buy a pass.")
    st.stop()

# --- APP STARTS HERE ---
st.toast(f"Welcome back, {user_name}!", icon="✅")

# Load Keys
api_key = st.secrets.get("GOOGLE_API_KEY")
bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN")
admin_chat_id = st.secrets.get("TELEGRAM_CHAT_ID")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

def send_telegram_result(target_chat_id, image_bytes, result_text):
    """Sends the result to the Subscriber AND a copy to You."""
    if not bot_token: return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    
    # 1. Send to SUBSCRIBER
    try:
        caption = f"💎 **Your Analysis**\n\n{result_text}\n\n_Thank you for subscribing!_"
        files = {'photo': image_bytes}
        data = {'chat_id': target_chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
        requests.post(url, files=files, data=data)
    except Exception as e:
        st.error(f"Could not message you on Telegram. Make sure you have clicked START on the bot! Error: {e}")

    # 2. Send Copy to ADMIN (You)
    if admin_chat_id and str(target_chat_id) != str(admin_chat_id):
        try:
            files_admin = {'photo': image_bytes} 
            admin_caption = f"👤 **User:** {user_name} (`{target_chat_id}`)\n📊 **Result:** {result_text}"
            data_admin = {'chat_id': admin_chat_id, 'caption': admin_caption, 'parse_mode': 'Markdown'}
            requests.post(url, files=files_admin, data=data_admin)
        except: pass

def analyze_jaw(image):
    prompt = "Analyze the jawline. Rate: Blade/Max, Medium, or Tomato. Return ONLY the rating and 1 short sentence explanation."
    try:
        return model.generate_content([prompt, image]).text
    except: return "Analysis failed. Please try a clearer photo."

# --- UI ---
st.title(f"💎 AI Jawline Service")
st.write(f"Logged in as: **{user_name}**")

uploaded_file = st.file_uploader("Upload your side profile", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Your Photo", use_column_width=True)
    
    if st.button("Analyze & Send to Telegram"):
        with st.spinner("Analyzing & Sending to your DM..."):
            # 1. Analyze
            result_text = analyze_jaw(image)
            
            # 2. Send to Telegram (User + Admin)
            img_bytes = uploaded_file.getvalue()
            send_telegram_result(user_id, img_bytes, result_text)
            
            # 3. Show Success
            st.success("✅ Sent to your Telegram!")
            st.info(f"**Preview:** {result_text}")