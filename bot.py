import os
import datetime
import random
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "AIzaSyCshP-OBAHoq6VLHhtIHRebx0Q0AcUD5Yo"
PDF_FOLDER = "applications"

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

# --- 1. THE INTERNAL DATABASE ---
# I added 'mobile', 'cloud', 'internet' tags here so they ALWAYS work.
SCHEMES_DB = [
    {"id": 1, "title": "PMEGP Loan", "tags": "business factory loan manufacturing money capital fund", "desc": "Subsidy up to 35% on loans up to 50 Lakhs."},
    {"id": 2, "title": "MUDRA Loan (Tarun)", "tags": "business shop trade expansion vendor general", "desc": "Loan up to 10 Lakhs without collateral."},
    {"id": 3, "title": "Stand-Up India", "tags": "sc st women dalit business lady", "desc": "Loans from 10 Lakh to 1 Crore for greenfield projects."},
    {"id": 4, "title": "PM SVANidhi", "tags": "street vendor hawker thela loan mobile food truck", "desc": "Micro-credit up to 50,000 for street vendors."},
    {"id": 5, "title": "Startup India Seed Fund", "tags": "startup tech app innovation cloud software internet mobile new business", "desc": "Grant up to 20 Lakhs for proof of concept."},
    {"id": 6, "title": "PM Kisan Samman Nidhi", "tags": "farmer agriculture money 6000 land", "desc": "Rs 6,000 per year income support for farmers."},
    {"id": 7, "title": "Kisan Credit Card (KCC)", "tags": "farmer loan crop bank card", "desc": "Short term credit for crops at low interest."},
    {"id": 8, "title": "National Livestock Mission", "tags": "goat sheep poultry pig farming animal", "desc": "50% Subsidy for livestock infrastructure."},
    {"id": 9, "title": "PM Kusum (Solar Pump)", "tags": "solar pump water farm irrigation", "desc": "60% Subsidy on solar water pumps for farmers."},
    {"id": 10, "title": "PM Vishwakarma", "tags": "artisan carpenter tailor tool kit blacksmith", "desc": "Loan @ 5% and Rs 15,000 for toolkits."},
    {"id": 11, "title": "Lakhpati Didi", "tags": "women shg skill drone training self help", "desc": "Skill training for women in Self Help Groups."},
    {"id": 12, "title": "PM Awas Yojana (Urban)", "tags": "home house flat loan subsidy city", "desc": "Interest subsidy on home loans for city dwellers."},
    {"id": 13, "title": "Ayushman Bharat", "tags": "health insurance hospital medical sick", "desc": "Free health cover up to 5 Lakhs per family."},
    {"id": 14, "title": "Sukanya Samriddhi Yojana", "tags": "girl child daughter saving bank education", "desc": "High interest savings scheme for girl child."},
    {"id": 15, "title": "PLI Textile Scheme", "tags": "textile cloth fabric manufacturing cotton", "desc": "Incentives for MMF fabric and technical textiles."},
    {"id": 16, "title": "Rooftop Solar Subsidy", "tags": "solar panel roof electric bill power energy", "desc": "Subsidy for installing solar panels on homes."},
    {"id": 17, "title": "FAME II EV Subsidy", "tags": "electric vehicle car bike scooter ev", "desc": "Subsidy on purchase of electric vehicles."}
]

# --- 2. SETUP AI (With Auto-Switching) ---
model = None
if API_KEY:
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("[SYSTEM] AI Connected ✅")
    except:
        print("[SYSTEM] AI Failed. Defaulting to internal DB.")

# --- 3. PROFESSIONAL PDF ENGINE ---
def generate_pro_pdf(scheme_name, user_phone, scheme_id):
    filename = f"Application_{scheme_id}_{user_phone[-4:]}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>GOVERNMENT SCHEME APPLICATION RECEIPT</b>", styles['Title']))
    elements.append(Paragraph("<br/>DIGITAL ACKNOWLEDGMENT", styles['Normal']))
    elements.append(Spacer(1, 20))

    date_now = datetime.datetime.now().strftime("%d-%b-%Y")
    ref_no = f"YJ-{datetime.datetime.now().year}-{random.randint(10000,99999)}"
    
    data = [
        ["APPLICANT DETAILS", ""],
        ["Mobile Number:", f"+{user_phone}"],
        ["Application Date:", date_now],
        ["Reference ID:", ref_no],
        ["KYC Status:", "PENDING VERIFICATION"],
        ["", ""],
        ["SCHEME INFORMATION", ""],
        ["Scheme Name:", scheme_name],
        ["Scheme Code:", f"SCH-{scheme_id:03d}"],
        ["Department:", "Central Nodal Agency (CNA)"],
        ["Current Status:", "Submitted for Review"]
    ]

    table = Table(data, colWidths=[150, 300])
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('BACKGROUND', (0,6), (-1,6), colors.darkblue),
        ('TEXTCOLOR', (0,6), (-1,6), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(style)
    elements.append(table)
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<b>DISCLAIMER:</b> This is a computer-generated receipt. Please visit your nearest Common Service Centre (CSC) or Bank Branch to complete the process.", styles['Italic']))
    
    doc.build(elements)
    return filename

# --- 4. ROUTES ---
@app.route("/", methods=['GET'])
def health_check():
    return "✅ Yojna-GPT Ultimate is Live"

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '').replace("whatsapp:", "")
    
    resp = MessagingResponse()
    reply = resp.message()
    
    # 1. WELCOME MESSAGE (PRIORITY 1)
    # Moved to top so it ALWAYS works
    if msg.lower() in ['hi', 'hello', 'start', 'menu', 'h', 'hey']:
        reply.body("🇮🇳 *Welcome to Yojna-GPT*\n"
                   "The Artificial Intelligence for Government Schemes.\n\n"
                   "🤖 *Ask me anything like:*\n"
                   "• \"I want to open a textile factory\"\n"
                   "• \"Loan for startup\"\n"
                   "• \"Mobile shop loan\"\n\n"
                   "📂 *Or type:* 'Status' to check application.")
        return str(resp)

    # 2. APPLY COMMAND (Generate PDF)
    if msg.lower().startswith("apply"):
        try:
            scheme_id = int(msg.split()[1])
            scheme = next((s for s in SCHEMES_DB if s['id'] == scheme_id), None)
            if scheme:
                pdf = generate_pro_pdf(scheme['title'], sender, scheme_id)
                link = f"{request.host_url}download/{pdf}"
                reply.body(f"✅ *Application Generated!*\n\n"
                           f"Scheme: {scheme['title']}\n"
                           f"Ref ID: #YJ-{scheme_id}\n\n"
                           f"📄 *Download Official Form:*\n{link}")
            else:
                reply.body("❌ Invalid Scheme ID.")
        except:
            reply.body("❌ Usage: Type 'Apply' followed by the ID number (e.g., *Apply 5*)")
        return str(resp)

    # 3. SEARCH (Internal DB)
    results = []
    query = msg.lower()
    for s in SCHEMES_DB:
        # Matches if query word is in tags (e.g., 'mobile' in 'startup... mobile')
        # OR if query is 'startup' and matches 'startup'
        if any(tag in query for tag in s['tags'].split()) or query in s['tags']:
            results.append(s)

    if results:
        txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
        for item in results[:3]:
            txt += (f"📌 *ID {item['id']}: {item['title']}*\n"
                    f"ℹ️ {item['desc']}\n"
                    f"👉 Reply *Apply {item['id']}*\n\n")
        reply.body(txt)
        return str(resp)

    # 4. AI BRAIN (Fallback with Error Handling)
    # We catch errors so the user NEVER sees "Network Error"
    if model:
        try:
            prompt = f"Act as an Indian Govt Scheme Expert. Briefly explain a scheme for: '{msg}'. If none exists, give general advice."
            ai_resp = model.generate_content(prompt)
            reply.body(f"🤖 *AI Assistant:*\n\n{ai_resp.text}")
            return str(resp)
        except Exception as e:
            print(f"AI Failed: {e}")
            pass # Fail silently to the final message
    
    # 5. FINAL MESSAGE (If everything fails)
    reply.body(f"🤖 *AI Assistant (Offline Mode):*\n\n"
               "I couldn't find a specific scheme for that right now. \n"
               "Please try broad categories like:\n"
               "- Loan\n"
               "- Farming\n"
               "- Business\n"
               "- Student")

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
