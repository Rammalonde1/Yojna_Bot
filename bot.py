import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

app = Flask(__name__)
DB_FILE = "schemes_database.csv"

# --- CONFIGURATION ---
# Improved: securely get key from environment without overwriting it
api_key = os.environ.get("GEMINI_API_KEY")

model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("[SYSTEM] AI Connected Successfully ✅")
    except Exception as e:
        print(f"[SYSTEM] AI Configuration Failed: {e}")
else:
    print("[SYSTEM] No Gemini API Key found. Running in Fallback Mode.")

def get_context():
    """Reads the CSV and converts it into a string for the AI to read."""
    if not os.path.exists(DB_FILE):
        return "No schemes database found."
    
    try:
        df = pd.read_csv(DB_FILE, on_bad_lines='skip') # Skip bad lines to prevent crashes
        context_str = ""
        for index, row in df.iterrows():
            context_str += f"- ID: {index+1}, Name: {row['title']}, Desc: {row.get('description', 'No desc')}\n"
        return context_str
    except Exception as e:
        print(f"Error reading DB: {e}")
        return ""

def fallback_search(query):
    """Simple keyword search if AI fails."""
    if not os.path.exists(DB_FILE): return "System Error: Database missing."
    try:
        df = pd.read_csv(DB_FILE, on_bad_lines='skip')
        query = query.lower()
        # Search in title or industry
        results = df[df['title'].str.lower().str.contains(query, na=False) | 
                     df['industry'].str.lower().str.contains(query, na=False)]
        
        if results.empty:
            return None
            
        reply = f"⚠️ *AI Offline - Showing Database Results:*\n\n"
        for _, row in results.head(3).iterrows():
            reply += f"📌 *{row['title']}*\n💰 Benefit: {row['subsidy_amount']}\n🔗 {row['link']}\n\n"
        return reply
    except:
        return None

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"[*] Query from {sender}: {user_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # --- 1. TRY AI MODE ---
    ai_success = False
    if model:
        schemes_data = get_context()
        system_prompt = f"""
        You are 'Yojna-GPT', an expert Indian Government Scheme Consultant.
        Here is the database of available schemes:
        {schemes_data}
        
        User Query: "{user_msg}"
        
        Instructions:
        1. Analyze the user's query.
        2. Recommend the best matching schemes from the database.
        3. If no scheme fits perfectly, suggest the closest one.
        4. Keep the answer friendly, professional, and under 150 words.
        5. Format the output with emojis and bullet points for WhatsApp.
        """
        
        try:
            response = model.generate_content(system_prompt)
            msg.body(response.text)
            ai_success = True
        except Exception as e:
            print(f"[!] AI Generation Error: {e}")
            # AI failed, we will fall through to backup

    # --- 2. FALLBACK MODE (If AI failed or is missing) ---
    if not ai_success:
        print("[*] Switching to Fallback Search...")
        fallback_result = fallback_search(user_msg)
        
        if fallback_result:
            msg.body(fallback_result)
        else:
            if not model:
                msg.body("⚠️ AI is not configured and no direct matches found in database. Please check your spelling.")
            else:
                msg.body("⚠️ Network Issue: AI did not respond, and no database keyword match found. Please try again.")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
