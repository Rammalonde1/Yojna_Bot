import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
# Your provided API Key
API_KEY = "AIzaSyCshP-OBAHoq6VLHhtIHRebx0Q0AcUD5Yo"
DB_FILE = "schemes_database.csv"

# --- 1. SETUP AI ---
model = None
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # using 'gemini-pro' as it is the most stable production model
        model = genai.GenerativeModel('gemini-pro')
        print("[SYSTEM] AI Connected (gemini-pro) ✅")
    except Exception as e:
        print(f"[SYSTEM] AI Connection Error: {e}")

# --- 2. ROBUST DATA LOADER ---
def get_schemes_context():
    """
    Loads data from CSV. If CSV fails, uses a hardcoded backup 
    so the bot NEVER crashes.
    """
    schemes_text = ""
    
    # Attempt 1: Load from CSV
    if os.path.exists(DB_FILE):
        try:
            # on_bad_lines='skip' ignores broken rows
            df = pd.read_csv(DB_FILE, on_bad_lines='skip')
            for _, row in df.iterrows():
                # specific safe get to avoid errors if column names change
                t = str(row.get('title', ''))
                b = str(row.get('subsidy_amount', ''))
                d = str(row.get('description', ''))
                schemes_text += f"- Scheme: {t} | Benefit: {b} | Details: {d}\n"
            return schemes_text
        except Exception as e:
            print(f"[WARN] CSV Load Failed: {e}. Using Backup Data.")

    # Attempt 2: Backup Data (Hardcoded)
    # This ensures the bot works even if you forget to upload the CSV
    return """
    - Scheme: PMEGP Loan | Benefit: 35% Subsidy | Details: Loan for manufacturing units.
    - Scheme: PM Vishwakarma | Benefit: 5% Interest Loan | Details: For artisans/carpenters.
    - Scheme: Textile PLI | Benefit: Sales Incentive | Details: For textile manufacturers.
    - Scheme: Mudra Loan | Benefit: 10 Lakh Loan | Details: Collateral free business loan.
    - Scheme: Solar Rooftop | Benefit: 40% Subsidy | Details: For solar panel installation.
    """

# --- 3. ROUTES ---

@app.route("/", methods=['GET'])
def health_check():
    """Fixes the 'Not Found' error in browser"""
    return "✅ Yojna-GPT is Live! Go to WhatsApp to use it."

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"[*] Msg from {sender}: {user_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # 1. Get Context (Schemes)
    context_data = get_schemes_context()
    
    # 2. Build the Prompt
    system_prompt = f"""
    You are 'Yojna-GPT', a helpful Indian Government Scheme Expert.
    
    Here is your knowledge base of active schemes:
    {context_data}
    
    User Question: "{user_msg}"
    
    Instructions:
    1. If the user asks about a scheme in your knowledge base, explain it clearly with the benefit.
    2. If the user greets (Hi/Hello), introduce yourself and list 3 key schemes (Textile, Solar, Loan).
    3. If the user asks something general (like "I am sad"), be polite but bring them back to business topics.
    4. Keep replies short (under 100 words) and use Emojis.
    """

    # 3. Generate Answer
    reply_text = ""
    try:
        if model:
            response = model.generate_content(system_prompt)
            reply_text = response.text
        else:
            reply_text = "⚠️ AI System Offline. Please check API Key."
    except Exception as e:
        print(f"[ERROR] AI Generation Failed: {e}")
        # FAILSAFE REPLIES (If AI breaks, we send this)
        if "loan" in user_msg.lower():
            reply_text = "📌 *Mudra Loan* is best for you. It offers up to ₹10 Lakhs collateral-free."
        elif "solar" in user_msg.lower():
            reply_text = "📌 *PM Surya Ghar* offers 40% subsidy for rooftop solar."
        else:
            reply_text = "⚠️ Network issue. Try searching for 'Loan' or 'Textile'."

    msg.body(reply_text)
    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
