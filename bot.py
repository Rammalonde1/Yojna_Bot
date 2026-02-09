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

# --- INTERNAL DATABASE ---
SCHEMES_DB = [
    {"id": 1, "title": "PMEGP Loan", "tags": "business factory loan manufacturing money capital fund", "desc": "Subsidy up to 35% on loans up to 50 Lakhs."},
    {"id": 2, "title": "MUDRA Loan", "tags": "business shop trade expansion vendor general", "desc": "Loan up to 10 Lakhs without collateral."},
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

# --- PDF ENGINE ---
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
        ["Date:", date_now],
        ["Reference ID:", ref_no],
        ["Status:", "PENDING VERIFICATION"],
        ["", ""],
        ["SCHEME DETAILS", ""],
        ["Scheme Name:", scheme_name],
        ["Scheme Code:", f"SCH-{scheme_id:03d}"],
    ]

    table = Table(data, colWidths=[150, 300])
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('BACKGROUND', (0,6), (-1,6), colors.darkblue),
        ('TEXTCOLOR', (0,6), (-1,6), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    table.setStyle(style)
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("DISCLAIMER: Visit your nearest Common Service Centre (CSC) to submit documents.", styles['Italic']))
    
    doc.build(elements)
    return filename

# --- FAIL-SAFE AI ---
def get_ai_reply(query):
    """Tries Google AI. If it crashes, returns a Smart Backup Answer."""
    try:
        if API_KEY:
            genai.configure(api_key=API_KEY)
            # Try 1.5-flash first
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(f"Explain Indian Govt Scheme '{query}' in 2 sentences.")
                return f"🤖 *AI Assistant:*\n{response.text}"
            except:
                # Fallback to Pro
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(f"Explain Indian Govt Scheme '{query}' in 2 sentences.")
                return f"🤖 *AI Assistant:*\n{response.text}"
    except Exception as e:
        print(f"AI Error: {e}")
    
    # HARDCODED BACKUP (If AI fails completely)
    if "loan" in query or "money" in query:
        return "🤖 *AI (Offline):* For financial needs, look at **PMEGP** (ID 1) or **Mudra Loan** (ID 2). They offer low-interest capital."
    if "farm" in query or "land" in query:
        return "🤖 *AI (Offline):* Farmers should check **PM Kisan** (ID 6) for income support or **KCC** (ID 7) for loans."
    return "🤖 *AI (Offline):* I couldn't connect to the server, but you can browse our schemes by typing 'List'."


# --- ROUTES ---
@app.route("/", methods=['GET'])
def health_check():
    return "✅ Yojna-GPT is Live"

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    try:
        msg = request.values.get('Body', '').strip().lower()
        sender = request.values.get('From', '').replace("whatsapp:", "")
        
        resp = MessagingResponse()
        reply = resp.message()
        
        # 1. GREETING (Always works)
        if msg in ['hi', 'hello', 'start', 'menu', 'h', 'hey']:
            reply.body("🇮🇳 *Welcome to Yojna-GPT*\n\n"
                       "🤖 *Ask me anything like:*\n"
                       "• \"Loan for factory\"\n"
                       "• \"Startup funding\"\n"
                       "• \"Mobile shop loan\"\n\n"
                       "📄 *To Apply:* Reply 'Apply <ID>'")
            return str(resp)

        # 2. APPLY COMMAND
        if msg.startswith("apply"):
            try:
                scheme_id = int(msg.split()[1])
                scheme = next((s for s in SCHEMES_DB if s['id'] == scheme_id), None)
                if scheme:
                    pdf = generate_pro_pdf(scheme['title'], sender, scheme_id)
                    link = f"{request.host_url}download/{pdf}"
                    reply.body(f"✅ *Application Generated!*\n"
                               f"Scheme: {scheme['title']}\n"
                               f"📄 *Download:* {link}")
                else:
                    reply.body("❌ Invalid ID.")
            except:
                reply.body("❌ Type 'Apply <ID>' (e.g., Apply 1)")
            return str(resp)

        # 3. INTERNAL SEARCH (Primary)
        results = []
        for s in SCHEMES_DB:
            if any(tag in msg for tag in s['tags'].split()) or msg in s['tags']:
                results.append(s)

        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for item in results[:3]:
                txt += (f"📌 *ID {item['id']}: {item['title']}*\n"
                        f"💰 {item['desc']}\n"
                        f"👉 Reply *Apply {item['id']}*\n\n")
            reply.body(txt)
        else:
            # 4. AI FALLBACK (With Safety Net)
            ai_text = get_ai_reply(msg)
            reply.body(ai_text)

        return str(resp)

    except Exception as e:
        # CATCH-ALL: If code crashes, send this instead of silence
        err_resp = MessagingResponse()
        err_resp.message(f"⚠️ System Error. Please try typing 'Hi' again.")
        return str(err_resp)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
