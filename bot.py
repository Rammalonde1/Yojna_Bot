import os
import datetime
import random
import json
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "AIzaSyCshP-OBAHoq6VLHhtIHRebx0Q0AcUD5Yo" # Your Key
PDF_FOLDER = "applications"

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

# --- 1. THE INTERNAL DATABASE (Hardcoded for Stability) ---
SCHEMES_DB = [
    {"id": 1, "title": "PMEGP Loan Scheme", "tags": "manufacturing factory business loan money startup", "benefit": "35% Subsidy (Max 50L)", "desc": "Govt subsidy loan for setting up new manufacturing units."},
    {"id": 2, "title": "PM Vishwakarma", "tags": "artisan carpenter tailor blacksmith tools kit", "benefit": "Loan @ 5% Interest", "desc": "Support for traditional artisans with toolkits and cheap loans."},
    {"id": 3, "title": "MUDRA Loan", "tags": "shop business small trade vendor", "benefit": "Up to 10 Lakhs", "desc": "Collateral-free loans for expanding existing small businesses."},
    {"id": 4, "title": "Stand-Up India", "tags": "sc st women dalit lady entrepreneur", "benefit": "10L - 1 Crore", "desc": "High value loans for greenfield projects by SC/ST or Women."},
    {"id": 5, "title": "PLI Textile Scheme", "tags": "cloth fabric garment cotton silk weaving", "benefit": "Incentives on Sales", "desc": "Production Linked Incentive for Man Made Fabrics."},
    {"id": 6, "title": "PM Kisan Sampada", "tags": "food processing cold storage farm agro", "benefit": "Grant up to 5 Cr", "desc": "For setting up Cold Chains and Food Processing units."},
    {"id": 7, "title": "Rooftop Solar Subsidy", "tags": "sun energy power electric bill panel", "benefit": "40% Subsidy", "desc": "Get money back for installing solar panels on your roof."},
    {"id": 8, "title": "Mahila Samman Savings", "tags": "girl wife mother save deposit bank", "benefit": "7.5% Interest", "desc": "Special high-interest savings certificate for women."},
    {"id": 9, "title": "PM Awas Yojana", "tags": "home house flat building construction", "benefit": "Interest Subsidy", "desc": "Subsidy on Home Loan interest for first-time buyers."},
    {"id": 10, "title": "FAME II Subsidy", "tags": "car bike scooter ev electric vehicle", "benefit": "Subsidy on Cost", "desc": "Discount on buying Electric Vehicles."}
]

# --- 2. SETUP AI ---
model = None
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("[SYSTEM] AI Connected ✅")
    except:
        print("[SYSTEM] AI Error. Running in Manual Mode.")

# --- 3. PROFESSIONAL PDF ENGINE ---
def generate_pro_pdf(scheme_name, user_phone, scheme_id):
    filename = f"Official_App_{scheme_id}_{user_phone[-4:]}_{random.randint(1000,9999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # 1. Official Header Bar
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-50, "GOVERNMENT SCHEME APPLICATION")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-75, "DIGITAL ACKNOWLEDGMENT RECEIPT")

    # 2. Watermark / Stamp
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(3)
    c.circle(width/2, height/2, 150)
    c.setFillColor(colors.lightgrey)
    c.setFont("Helvetica-Bold", 60)
    c.translate(width/2, height/2)
    c.rotate(45)
    c.drawCentredString(0, 0, "PROCESSED")
    c.rotate(-45)
    c.translate(-width/2, -height/2)

    # 3. Applicant Details Box
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)
    c.setLineWidth(1)
    
    c.rect(50, height-250, width-100, 120) # Box
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, height-140, "APPLICANT DETAILS")
    c.line(50, height-145, width-50, height-145)
    
    c.setFont("Helvetica", 12)
    c.drawString(70, height-170, f"Mobile Number: +{user_phone}")
    c.drawString(70, height-190, f"Date of Application: {datetime.datetime.now().strftime('%d-%b-%Y')}")
    c.drawString(70, height-210, f"Application ID: YJ-{datetime.datetime.now().strftime('%Y')}-{random.randint(10000,99999)}")
    c.drawString(70, height-230, "KYC Status: PENDING VERIFICATION")

    # 4. Scheme Details Box
    c.rect(50, height-400, width-100, 120) # Box
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, height-290, "SCHEME INFORMATION")
    c.line(50, height-295, width-50, height-295)
    
    c.setFont("Helvetica", 12)
    c.drawString(70, height-320, f"Scheme Name: {scheme_name}")
    c.drawString(70, height-340, f"Scheme Code: SCH-{scheme_id:03d}")
    c.drawString(70, height-360, "Department: Nodal Agency / DIC")
    
    # 5. Footer / Disclaimer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 100, "* This is a computer generated receipt and does not require a physical signature.")
    c.drawString(50, 85, "* Please visit your nearest Common Service Centre (CSC) for final document submission.")
    
    c.save()
    return filename

# --- 4. AI ROUTER (The Smart Part) ---
def get_best_match(user_query):
    """
    Uses AI to understand intent.
    Input: "I need money for cloth factory"
    Output: Scheme ID (e.g., 5)
    """
    if not model: return None
    
    # Create a simplified list for AI to read
    scheme_list = "\n".join([f"ID:{s['id']} Name:{s['title']} Tags:{s['tags']}" for s in SCHEMES_DB])
    
    prompt = f"""
    You are a classification engine. Match the User Query to the best Scheme ID.
    
    Schemes:
    {scheme_list}
    
    User Query: "{user_query}"
    
    Task: Return ONLY the ID number (e.g., '5'). If no match, return '0'.
    """
    try:
        response = model.generate_content(prompt)
        match_id = int(response.text.strip())
        return match_id
    except:
        return 0

# --- 5. ROUTES ---

@app.route("/", methods=['GET'])
def health_check():
    return "✅ Yojna-GPT Professional is Live"

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace("whatsapp:", "")
    
    resp = MessagingResponse()
    msg = resp.message()
    
    # --- COMMAND: APPLY ---
    if incoming_msg.lower().startswith("apply"):
        try:
            scheme_id = int(incoming_msg.split()[1])
            scheme = next((s for s in SCHEMES_DB if s['id'] == scheme_id), None)
            
            if scheme:
                pdf = generate_pro_pdf(scheme['title'], sender, scheme_id)
                link = f"{request.host_url}download/{pdf}"
                msg.body(f"✅ *Application Generated Successfully*\n\n"
                         f"Scheme: {scheme['title']}\n"
                         f"Ref ID: #YJ-{scheme_id}\n\n"
                         f"📄 *Download Official Receipt:*\n{link}")
            else:
                msg.body("❌ Invalid ID.")
        except:
            msg.body("❌ usage: Apply <ID>")
        return str(resp)

    # --- SMART SEARCH ---
    # 1. Ask AI to find the ID based on meaning
    best_id = get_best_match(incoming_msg)
    
    results = []
    
    # If AI found a match, get that scheme
    if best_id and best_id > 0:
        found = next((s for s in SCHEMES_DB if s['id'] == best_id), None)
        if found: results.append(found)

    # If AI failed or returned 0, try simple keyword search
    if not results:
        query = incoming_msg.lower()
        for s in SCHEMES_DB:
            if query in s['title'].lower() or query in s['tags']:
                results.append(s)

    # --- RESPONSE GENERATION ---
    if results:
        reply = f"🔍 *Found {len(results)} Matching Schemes:*\n\n"
        for item in results[:3]:
            reply += (f"📌 *ID {item['id']}: {item['title']}*\n"
                      f"💰 {item['benefit']}\n"
                      f"ℹ️ {item['desc']}\n"
                      f"👉 Reply *Apply {item['id']}*\n\n")
        msg.body(reply)
    else:
        # Final AI Chat fallback if no schemes match
        if model:
            try:
                chat = model.generate_content(f"Explain '{incoming_msg}' related to Indian Govt Schemes in 1 sentence.")
                msg.body(f"🤖 *AI Info:* {chat.text}\n\n(No direct application available for this yet.)")
            except:
                msg.body("❌ No schemes found. Try 'Loan', 'Farming', or 'Business'.")
        else:
            msg.body("❌ No schemes found. Try 'Loan', 'Farming', or 'Business'.")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
