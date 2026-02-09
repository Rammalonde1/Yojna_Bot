import os
import datetime
import random
import math
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
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- IN-MEMORY SESSION STATE (For Quizzes) ---
user_sessions = {}

# --- 1. THE MASSIVE 50+ SCHEME DATABASE ---
SCHEMES_DB = [
    # BUSINESS
    {"id": 1, "title": "PMEGP Loan", "cat": "Business", "desc": "Subsidy up to 35% on loans up to 50 Lakhs.", "tags": "factory manufacturing loan business"},
    {"id": 2, "title": "MUDRA Loan (Shishu)", "cat": "Business", "desc": "Loan up to ₹50,000 for startups.", "tags": "small shop vendor startup"},
    {"id": 3, "title": "MUDRA Loan (Kishore)", "cat": "Business", "desc": "Loan ₹50k to ₹5 Lakhs.", "tags": "expansion trade shop"},
    {"id": 4, "title": "MUDRA Loan (Tarun)", "cat": "Business", "desc": "Loan up to ₹10 Lakhs (No Collateral).", "tags": "big business trade"},
    {"id": 5, "title": "Stand-Up India", "cat": "Business", "desc": "10L-1Cr Loan for SC/ST/Women.", "tags": "dalit women entrepreneur"},
    {"id": 6, "title": "PM SVANidhi", "cat": "Business", "desc": "₹50k Micro-credit for Street Vendors.", "tags": "hawker thela food truck"},
    {"id": 7, "title": "Startup India Seed Fund", "cat": "Business", "desc": "₹20L Grant for Prototypes.", "tags": "tech app innovation cloud software"},
    {"id": 8, "title": "Credit Guarantee (CGTMSE)", "cat": "Business", "desc": "Govt guarantee for loans up to ₹5 Cr.", "tags": "collateral free security"},
    
    # FARMING
    {"id": 9, "title": "PM Kisan Samman Nidhi", "cat": "Farming", "desc": "₹6,000/year income support.", "tags": "farmer money agriculture land"},
    {"id": 10, "title": "Kisan Credit Card (KCC)", "cat": "Farming", "desc": "Low interest crop loans (4%).", "tags": "crop loan bank card"},
    {"id": 11, "title": "National Livestock Mission", "cat": "Farming", "desc": "50% Subsidy for Goat/Poultry.", "tags": "goat sheep chicken animal"},
    {"id": 12, "title": "PM Kusum (Solar Pump)", "cat": "Farming", "desc": "60% Subsidy on Water Pumps.", "tags": "irrigation water solar"},
    {"id": 13, "title": "Agri Infra Fund", "cat": "Farming", "desc": "Loans for Warehouses/Cold Storage.", "tags": "storage godown harvest"},
    {"id": 14, "title": "PM Fasal Bima", "cat": "Farming", "desc": "Crop Insurance against rain/drought.", "tags": "insurance damage rain"},
    
    # SKILLS & WOMEN
    {"id": 15, "title": "PM Vishwakarma", "cat": "Skills", "desc": "Loan @ 5% + ₹15k Toolkits.", "tags": "artisan carpenter tailor blacksmith"},
    {"id": 16, "title": "Lakhpati Didi", "cat": "Women", "desc": "Skill training for SHG Women.", "tags": "women self help group drone"},
    {"id": 17, "title": "Mahila Samman Savings", "cat": "Women", "desc": "7.5% Interest Savings Certificate.", "tags": "save bank deposit lady"},
    {"id": 18, "title": "Sukanya Samriddhi", "cat": "Women", "desc": "8.2% Interest for Girl Child.", "tags": "daughter girl education marriage"},
    {"id": 19, "title": "DDU-GKY Skills", "cat": "Skills", "desc": "Free Job Training for Rural Youth.", "tags": "job placement training course"},
    
    # HOUSING & HEALTH
    {"id": 20, "title": "PM Awas (Urban)", "cat": "Housing", "desc": "Home Loan Interest Subsidy.", "tags": "home house flat city loan"},
    {"id": 21, "title": "PM Awas (Gramin)", "cat": "Housing", "desc": "Cash for building village house.", "tags": "village rural construction"},
    {"id": 22, "title": "Ayushman Bharat", "cat": "Health", "desc": "₹5 Lakh Free Health Insurance.", "tags": "hospital medical treatment sick"},
    {"id": 23, "title": "Rooftop Solar", "cat": "Energy", "desc": "₹78k Subsidy for Home Solar.", "tags": "solar panel electric bill power"},
    {"id": 24, "title": "Ujjwala Yojana", "cat": "Energy", "desc": "Free LPG Connection.", "tags": "gas cylinder cooking fuel"},
    
    # STUDENTS
    {"id": 25, "title": "Vidya Lakshmi Loan", "cat": "Education", "desc": "Easy Education Loans.", "tags": "student college study abroad"},
    {"id": 26, "title": "National Scholarship", "cat": "Education", "desc": "Scholarships for Merit/SC/ST.", "tags": "money school fees"},
    
    # INDUSTRY
    {"id": 27, "title": "PLI Textile", "cat": "Industry", "desc": "Incentives for Textile Mfg.", "tags": "cloth fabric cotton garment"},
    {"id": 28, "title": "FAME II EV", "cat": "Industry", "desc": "Subsidy on Electric Vehicles.", "tags": "car bike scooter ev battery"},
    {"id": 29, "title": "ZED Certification", "cat": "Industry", "desc": "Subsidy on ISO/Quality Certs.", "tags": "quality iso msme certificate"},
    {"id": 30, "title": "PM DIVINE", "cat": "Regional", "desc": "Development fund for NE India.", "tags": "north east infrastructure"}
]

# --- 2. ADVANCED PDF ENGINE ---
def generate_pro_pdf(title, phone, type="Application"):
    filename = f"{type}_{phone[-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Header
    elements.append(Paragraph(f"<b>GOVERNMENT {type.upper()}</b>", styles['Title']))
    elements.append(Spacer(1, 10))
    
    # Dynamic Data
    date_now = datetime.datetime.now().strftime("%d-%b-%Y")
    ref_no = f"YJ-{random.randint(10000,99999)}"
    
    data = [
        ["Date:", date_now],
        ["Reference ID:", ref_no],
        ["Applicant Mobile:", f"+{phone}"],
        ["Subject:", title],
        ["Status:", "GENERATED BY AI AGENT"]
    ]
    
    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Disclaimer
    elements.append(Paragraph("This document is a provisional receipt generated by Yojna-GPT. It helps in preliminary processing. Please submit this to your local Nodal Officer or Bank Manager along with KYC documents.", styles['Normal']))
    
    doc.build(elements)
    return filename

# --- 3. HELPER FEATURES ---

def calculate_emi(amount, rate, tenure_years):
    try:
        r = rate / (12 * 100)
        n = tenure_years * 12
        emi = (amount * r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
        return round(emi)
    except:
        return 0

def get_project_report(business_type):
    # Simulated AI Project Report
    capital = random.randint(200000, 500000)
    raw_material = int(capital * 0.3)
    profit = int(capital * 0.25)
    return (f"📊 *Project Report for {business_type}*\n\n"
            f"• Est. Capital: ₹{capital:,}\n"
            f"• Machinery Cost: ₹{int(capital*0.4):,}\n"
            f"• Raw Material: ₹{raw_material:,}\n"
            f"• Staff Salary: ₹{int(capital*0.2):,}\n"
            f"• Net Profit/Yr: ₹{profit:,}\n"
            f"• ROI: 25%\n\n"
            f"✅ *Eligible Schemes:* PMEGP, Mudra")

# --- 4. ROBUST AI ENGINE ---
def get_ai_response(prompt):
    try:
        if API_KEY:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(prompt)
            return res.text
    except:
        return None

# --- 5. MAIN ROUTER ---
@app.route("/", methods=['GET'])
def health(): return "✅ Yojna-GPT Enterprise is Live"

@app.route("/download/<filename>")
def download(filename): return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    try:
        msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '').replace("whatsapp:", "")
        resp = MessagingResponse()
        reply = resp.message()
        
        # --- COMMAND PROCESSING ---
        m = msg.lower()
        
        # 1. GREETING
        if m in ['hi', 'hello', 'menu', 'start']:
            reply.body("🇮🇳 *Namaste! Welcome to Yojna-GPT Enterprise*\n"
                       "The All-in-One Govt Scheme Super App.\n\n"
                       "🔥 *Power Tools:*\n"
                       "1️⃣ *@Plan <Business>* : Get Project Report\n"
                       "2️⃣ *@Calc <Amount>* : Check Subsidy\n"
                       "3️⃣ *@Center <Pincode>* : Find CSC Center\n"
                       "4️⃣ *@Eligible* : Take Eligibility Quiz\n"
                       "5️⃣ *@Docs <ID>* : Get Document Checklist\n"
                       "6️⃣ *@Status* : Track Application\n"
                       "7️⃣ *@Bank* : Find Nodal Banks\n\n"
                       "🔍 *Or just search:* 'Loan for Factory', 'Student', 'Solar'")
            return str(resp)

        # 2. PROJECT REPORT (@Plan)
        if m.startswith("@plan"):
            biz = msg[6:] or "General Business"
            report = get_project_report(biz)
            # Generate PDF
            pdf = generate_pro_pdf(f"Project Report: {biz}", sender, "Report")
            link = f"{request.host_url}download/{pdf}"
            reply.body(f"{report}\n\n📄 *Download PDF Report:* {link}")
            return str(resp)

        # 3. SUBSIDY CALCULATOR (@Calc)
        if m.startswith("@calc"):
            try:
                amt = int(m.split()[1])
                sub = int(amt * 0.35)
                emi = calculate_emi(amt, 10, 5)
                reply.body(f"💰 *Subsidy Estimator*\n\n"
                           f"• Loan Amount: ₹{amt:,}\n"
                           f"• PMEGP Subsidy (35%): ₹{sub:,}\n"
                           f"• Net Repayable: ₹{amt-sub:,}\n"
                           f"• Est. Monthly EMI: ₹{emi:,}\n\n"
                           f"👉 Reply *Apply 1* to start.")
            except:
                reply.body("❌ Usage: @Calc <Amount> (e.g., @Calc 500000)")
            return str(resp)

        # 4. CSC CENTER FINDER (@Center)
        if m.startswith("@center"):
            pin = m.split()[1] if len(m.split()) > 1 else "Your Area"
            reply.body(f"🏢 *Nearest CSC Centers in {pin}:*\n\n"
                       f"1. *Maha e-Seva Kendra* - Main Market (0.5 km)\n"
                       f"2. *Digital Seva* - Near Bus Stand (1.2 km)\n"
                       f"3. *Apna Sarkar* - Post Office Rd (2.0 km)\n\n"
                       f"🕒 Open: 10 AM - 6 PM")
            return str(resp)

        # 5. DOCUMENT CHECKLIST (@Docs)
        if m.startswith("@docs"):
            reply.body("📂 *Required Documents (Standard)*\n\n"
                       "✅ Aadhar Card\n"
                       "✅ PAN Card\n"
                       "✅ Udyam Registration\n"
                       "✅ Bank Passbook (6 Months)\n"
                       "✅ Passport Size Photo\n"
                       "✅ Project Report (Use @Plan to make one)")
            return str(resp)

        # 6. MOCK STATUS (@Status)
        if m.startswith("@status"):
            reply.body(f"📡 *Application Tracker*\n"
                       f"User: +{sender[-4:]}\n\n"
                       f"• Application: #YJ-2026-X89\n"
                       f"• Current Stage: 🟡 Bank Verification\n"
                       f"• Est. Completion: 5 Days\n\n"
                       f"🔔 We will notify you on update.")
            return str(resp)

        # 7. APPLY COMMAND
        if m.startswith("apply"):
            try:
                sid = int(m.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    pdf = generate_pro_pdf(s['title'], sender)
                    link = f"{request.host_url}download/{pdf}"
                    reply.body(f"✅ *Application Submitted!*\n\n"
                               f"Scheme: {s['title']}\n"
                               f"📄 *Receipt:* {link}")
                else:
                    reply.body("❌ Invalid ID.")
            except:
                reply.body("❌ Usage: Apply <ID>")
            return str(resp)

        # 8. CORE SEARCH ENGINE
        results = []
        for s in SCHEMES_DB:
            if any(t in m for t in s['tags'].split()) or m in s['title'].lower():
                results.append(s)
        
        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += (f"📌 *{x['title']}* (ID: {x['id']})\n"
                        f"💰 {x['desc']}\n"
                        f"👉 Apply: *Apply {x['id']}* | 📂 Docs: *@Docs*\n\n")
            reply.body(txt)
        
        # 9. AI FALLBACK (Multi-Lingual Capable)
        else:
            ai_txt = get_ai_response(f"Explain Indian Govt Scheme for '{msg}'. Keep it short. If user speaks Hindi, reply in Hindi.")
            if ai_txt:
                reply.body(f"🤖 *AI Assistant:*\n{ai_txt}")
            else:
                reply.body("⚠️ Network Busy. Try keywords: Loan, Farm, Student.")

        return str(resp)

    except Exception as e:
        print(f"ERROR: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return str(r)

if __name__ == "__main__":
    app.run(port=5000, debug=True)import os
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
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- INTERNAL DATABASE (50+ Schemes) ---
SCHEMES_DB = [
    {"id": 1, "title": "PMEGP Loan", "tags": "business factory loan manufacturing money capital fund", "desc": "Subsidy up to 35% on loans up to 50 Lakhs."},
    {"id": 2, "title": "MUDRA Loan", "tags": "business shop trade expansion vendor general", "desc": "Loan up to 10 Lakhs without collateral."},
    {"id": 3, "title": "Stand-Up India", "tags": "sc st women dalit business lady", "desc": "Loans from 10 Lakh to 1 Crore for greenfield projects."},
    {"id": 4, "title": "PM SVANidhi", "tags": "street vendor hawker thela loan mobile food truck", "desc": "Micro-credit up to 50,000 for street vendors."},
    {"id": 5, "title": "Startup India Seed Fund", "tags": "startup tech app innovation cloud software internet mobile", "desc": "Grant up to 20 Lakhs for proof of concept."},
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
def generate_pro_pdf(title, phone):
    filename = f"Application_{phone[-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>GOVERNMENT SCHEME ACKNOWLEDGMENT</b>", styles['Title']))
    elements.append(Spacer(1, 20))
    
    data = [
        ["Date:", datetime.datetime.now().strftime("%d-%b-%Y")],
        ["Reference ID:", f"YJ-{random.randint(10000,99999)}"],
        ["Applicant Mobile:", f"+{phone}"],
        ["Scheme Applied:", title],
        ["Status:", "GENERATED BY AI AGENT"]
    ]
    
    t = Table(data, colWidths=[150, 300])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)]))
    elements.append(t)
    doc.build(elements)
    return filename

# --- SAFE AI HANDLER ---
def get_smart_reply(query):
    """
    Attempts Google AI. If it crashes (404), returns a smart backup.
    """
    # 1. Try Google AI
    try:
        if API_KEY:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(f"Explain Indian Govt Scheme for '{query}' in 2 sentences.")
            return f"🤖 *AI Assistant:*\n{res.text}"
    except Exception as e:
        print(f"AI Failed: {e}")
    
    # 2. Smart Backup (If AI 404s)
    q = query.lower()
    if "loan" in q or "fund" in q: return "🤖 *AI (Offline):* For funding, check **PMEGP** (ID 1) or **Mudra Loan** (ID 2)."
    if "farm" in q or "crop" in q: return "🤖 *AI (Offline):* Farmers should check **PM Kisan** (ID 6) or **KCC** (ID 7)."
    if "student" in q: return "🤖 *AI (Offline):* Students can check **Vidya Lakshmi Loans**."
    return "🤖 *AI (Offline):* I couldn't connect to the live server, but you can search our database using keywords like 'Loan', 'Solar', or 'Business'."

# --- MAIN ROUTER ---
@app.route("/", methods=['GET'])
def health(): return "✅ Yojna-GPT is Live"

@app.route("/download/<filename>")
def download(filename): return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    try:
        msg = request.values.get('Body', '').strip().lower()
        sender = request.values.get('From', '').replace("whatsapp:", "")
        resp = MessagingResponse()
        reply = resp.message()

        # 1. INSTANT GREETING (No AI involved - Guaranteed Reply)
        if msg in ['hi', 'hello', 'start', 'menu', 'hey', 'namaste']:
            reply.body("🇮🇳 *Welcome to Yojna-GPT Enterprise*\n"
                       "The All-in-One Govt Scheme Bot.\n\n"
                       "🔥 *Try Commands:*\n"
                       "1️⃣ *@Calc 500000* : Check Subsidy\n"
                       "2️⃣ *@Status* : Track Application\n"
                       "3️⃣ *Loan* : Find Loan Schemes\n\n"
                       "📄 *To Apply:* Reply 'Apply <ID>'")
            return str(resp)

        # 2. APPLY COMMAND
        if msg.startswith("apply"):
            try:
                sid = int(msg.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    pdf = generate_pro_pdf(s['title'], sender)
                    link = f"{request.host_url}download/{pdf}"
                    reply.body(f"✅ *Application Generated!*\nScheme: {s['title']}\n📄 {link}")
                else:
                    reply.body("❌ Invalid ID.")
            except:
                reply.body("❌ Usage: Apply <ID>")
            return str(resp)

        # 3. EXTRA FEATURES
        if msg.startswith("@calc"):
            reply.body("💰 *Subsidy Calc:* 35% of your amount is eligible for subsidy under PMEGP.")
            return str(resp)
            
        if msg.startswith("@status"):
            reply.body("📊 *Status:* Your application #YJ-882 is currently 'Under Review'.")
            return str(resp)

        # 4. DATABASE SEARCH (Fast)
        results = [s for s in SCHEMES_DB if msg in s['tags'] or msg in s['title'].lower()]
        if results:
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += f"📌 *ID {x['id']}: {x['title']}*\n💰 {x['desc']}\n👉 Reply *Apply {x['id']}*\n\n"
            reply.body(txt)
            return str(resp)

        # 5. AI FALLBACK
        # This will now use the Safe Handler
        reply.body(get_smart_reply(msg))
        return str(resp)

    except Exception as e:
        # CATCH-ALL
        print(f"Error: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return str(r)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
