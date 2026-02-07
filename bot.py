import os
import pandas as pd
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

# --- CONFIGURATION ---
# 1. Get a Free API Key from: https://aistudio.google.com/app/apikey
# 2. Set it here or in your environment variables
os.environ["GEMINI_API_KEY"] = "YOUR_API_KEY_HERE"

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')

app = Flask(__name__)
DB_FILE = "schemes_database.csv"

def get_context():
    """Reads the CSV and converts it into a string for the AI to read."""
    if not os.path.exists(DB_FILE):
        return "No schemes database found."
    
    df = pd.read_csv(DB_FILE)
    # Convert dataframe to a simplified string format to save tokens
    # Format: "Scheme Name: [Name], Industry: [Ind], Benefit: [Benefit]"
    context_str = ""
    for index, row in df.iterrows():
        context_str += f"- ID: {index+1}, Name: {row['title']}, Desc: {row['description']}\n"
    return context_str

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    user_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    print(f"[*] AI Query from {sender}: {user_msg}")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # 1. Prepare the AI Prompt
    schemes_data = get_context()
    
    system_prompt = f"""
    You are 'Yojna-GPT', an expert Indian Government Scheme Consultant.
    
    Here is the database of available schemes:
    {schemes_data}
    
    User Query: "{user_msg}"
    
    Instructions:
    1. Analyze the user's query (industry, location, needs).
    2. Recommend the best matching schemes from the database above.
    3. If no scheme fits perfectly, suggest the closest one.
    4. Keep the answer friendly, professional, and under 150 words.
    5. Format the output with emojis and bullet points for WhatsApp.
    6. If the database is empty, tell them to wait for the scraping engine to finish.
    """
    
    try:
        # 2. Ask the AI
        response = model.generate_content(system_prompt)
        ai_reply = response.text
        msg.body(ai_reply)
    except Exception as e:
        msg.body("⚠️ Sorry, my AI brain is currently overloaded. Please try again in 1 minute.")
        print(f"[!] AI Error: {e}")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
