import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

app = Flask(__name__)
DB_FILE = "schemes_database.csv"

# --- CONFIGURATION ---
# 1. SETTING THE API KEY DIRECTLY
API_KEY = "AIzaSyCshP-OBAHoq6VLHhtIHRebx0Q0AcUD5Yo"

model = None
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        # CHANGED: Switched to 'gemini-pro' which is the standard stable model
        model = genai.GenerativeModel('gemini-pro')
        print("[SYSTEM] AI Connected Successfully (Model: gemini-pro) ✅")
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
            # Safely get columns, handle missing ones
            title = row.get('title', 'Unknown Scheme')
            desc = row.get('description', 'No description')
            benefit = row.get('subsidy_amount', 'Benefit not listed')
            context_str += f"- Scheme: {title} | Benefit: {benefit} | Info: {desc}\n"
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
            title = row.get('title', 'Scheme')
            benefit = row.get('subsidy_amount', 'Check Link')
            link = row.get('link', '#')
            reply += f"📌 *{title}*\n💰 Benefit: {benefit}\n🔗 {link}\n\n"
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
        2. Recommend the best matching schemes from the database provided above.
        3. If no scheme fits perfectly, suggest the closest one.
        4. Keep the answer friendly, professional, and under 150 words.
        5. Format the output with emojis and bullet points for WhatsApp.
        """
        
        try:
            # Generate content
            response = model.generate_content(system_prompt)
            if response.text:
                msg.body(response.text)
                ai_success = True
        except Exception as e:
            print(f"[!] AI Generation Error: {e}")
            # AI failed, we will fall through to backup silently

    # --- 2. FALLBACK MODE (If AI failed or is missing) ---
    if not ai_success:
        print("[*] AI Failed/Skipped. Switching to Fallback Search...")
        fallback_result = fallback_search(user_msg)
        
        if fallback_result:
            msg.body(fallback_result)
        else:
            # Final generic message if nothing works
            msg.body("⚠️ I couldn't find a specific scheme for that. Try searching for keywords like 'Textile', 'Loan', or 'Solar'.")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
