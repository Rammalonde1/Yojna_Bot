import os
import datetime
import random
import csv
import io
from flask import Flask, request, Response, send_from_directory, send_file
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
# SECURITY: Fetch from Environment Variables on Render
API_KEY = os.environ.get("GOOGLE_API_KEY")

PDF_FOLDER = "applications"
LEADS_FILE = "customer_leads.csv"

if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- LEAD GENERATION SYSTEM (CRM) ---
def save_lead(phone, category, details):
    """Saves user data for monetization."""
    file_exists = os.path.isfile(LEADS_FILE)
    try:
        with open(LEADS_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Timestamp', 'Phone', 'Category', 'Details'])
            
            writer.writerow([
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                f"'{phone}", 
                category,
                details
            ])
        print(f"[CRM] Lead Captured: {phone} ({category})")
    except Exception as e:
        print(f"[CRM Error] {e}")

# --- INTERNAL DATABASE (Top 50+ Schemes) ---
SCHEMES_DB = [
    # BUSINESS & LOANS (High Ticket)
    {"id": 101, "title": "PMEGP Loan", "cat": "Biz", "tags": "factory loan business manufacturing subsidy", "desc": "Subsidy up to 35% on loans (Max 50L)."},
    {"id": 102, "title": "MUDRA (Shishu)", "cat": "Biz", "tags": "small shop startup vendor tea", "desc": "Loan up to ₹50,000 for starters."},
    {"id": 103, "title": "MUDRA (Tarun)", "cat": "Biz", "tags": "expansion trade shop big business", "desc": "Loan up to ₹10 Lakhs (Collateral Free)."},
    {"id": 104, "title": "Stand-Up India", "cat": "Biz", "tags": "sc st women dalit lady entrepreneur", "desc": "10L-1Cr Loan for Greenfield projects."},
    {"id": 105, "title": "PM SVANidhi", "cat": "Biz", "tags": "street vendor hawker food truck thela", "desc": "₹50k Micro-credit for Vendors."},
    {"id": 106, "title": "Startup India Seed", "cat": "Biz", "tags": "tech app cloud software internet", "desc": "₹20L Grant for Prototypes."},
    {"id": 107, "title": "CGTMSE Cover", "cat": "Biz", "tags": "guarantee security collateral bank", "desc": "Govt guarantee for loans up to ₹5 Cr."},
    
    # FARMING (High Volume)
    {"id": 201, "title": "PM Kisan Samman", "cat": "Farm", "tags": "farmer money agri land income", "desc": "₹6,000/year direct income support."},
    {"id": 202, "title": "Kisan Credit Card", "cat": "Farm", "tags": "crop loan bank card kcc", "desc": "Low interest crop loans (4%)."},
    {"id": 203, "title": "National Livestock", "cat": "Farm", "tags": "goat sheep poultry chicken animal", "desc": "50% Subsidy for animal farming."},
    {"id": 204, "title": "PM Kusum Solar", "cat": "Farm", "tags": "solar pump irrigation water tube well", "desc": "60% Subsidy on Water Pumps."},
    {"id": 205, "title": "Agri Infra Fund", "cat": "Farm", "tags": "warehouse storage cold chain godown", "desc": "Loans for post-harvest infra."},
    
    # WOMEN & SKILLS
    {"id": 301, "title": "Lakhpati Didi", "cat": "Women", "tags": "women shg drone training self help", "desc": "Skill training for SHG Women."},
    {"id": 302, "title": "Mahila Samman", "cat": "Women", "tags": "save deposit bank lady wife", "desc": "7.5% Interest Savings Certificate."},
    {"id": 303, "title": "Sukanya Samriddhi", "cat": "Women", "tags": "girl daughter child education marriage", "desc": "8.2% Interest for Girl Child."},
    {"id": 304, "title": "PM Vishwakarma", "cat": "Skill", "tags": "artisan carpenter tailor tools kit", "desc": "Loan @ 5% + ₹15k Toolkits."},
    
    # HOUSING & HEALTH
    {"id": 401, "title": "PM Awas (Urban)", "cat": "Home", "tags": "home house flat city loan", "desc": "Home Loan Interest Subsidy."},
    {"id": 402, "title": "PM Awas (Gramin)", "cat": "Home", "tags": "village house construction rural", "desc": "Cash for building village house."},
    {"id": 403, "title": "Ayushman Bharat", "cat": "Health", "tags": "hospital medical treatment sick health", "desc": "₹5 Lakh Free Health Insurance."},
    
    # EDUCATION & STUDENT
    {"id": 501, "title": "Vidya Lakshmi Loan", "cat": "Edu", "tags": "student loan college study degree", "desc": "Easy Education Loans Portal."},
    {"id": 502, "title": "National Scholarship", "cat": "Edu", "tags": "scholarship merit sc st obc", "desc": "Scholarships for Merit/SC/ST students."},
    
    # INFRA & OTHERS
    {"id": 601, "title": "Rooftop Solar", "cat": "Power", "tags": "solar panel electric bill power sun", "desc": "₹78k Subsidy for Home Solar."},
    {"id": 602, "title": "Ujjwala Yojana", "cat": "Power", "tags": "gas cylinder lpg cooking fuel", "desc": "Free LPG Connection for BPL."},
    {"id": 603, "title": "FAME II EV", "cat": "Auto", "tags": "electric vehicle car bike scooter", "desc": "Subsidy on Electric Vehicles."},
    {"id": 604, "title": "PLI Textile", "cat": "Ind", "tags": "textile cloth fabric cotton", "desc": "Incentives for Textile Mfg."}
]

# --- 2. PREMIUM PDF ENGINE (3 Types) ---
def generate_pdf(type, data):
    filename = f"{type}_{data['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width/2, height-50, "YOJNA SEVA KENDRA")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-75, "DIGITAL FACILITATION CENTER | GOVT SERVICES")

    # Watermark
    c.saveState()
    c.translate(width/2, height/2)
    c.rotate(45)
    c.setFillColor(colors.lightgrey)
    c.setFont("Helvetica-Bold", 60)
    c.drawCentredString(0, 0, "OFFICIAL")
    c.restoreState()

    c.setFillColor(colors.black)
    c.setLineWidth(2)
    
    if type == "Card":
        # ID CARD
        c.rect(150, 450, 300, 180, fill=0) # Border
        c.setFillColor(colors.navy)
        c.rect(150, 590, 300, 40, fill=1) # Top Bar
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(300, 605, "MEMBERSHIP CARD")
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(170, 560, f"Member: Preferred User")
        c.drawString(170, 535, f"Mobile: +{data['phone']}")
        c.drawString(170, 510, f"ID No: YJ-{random.randint(10000,99999)}")
        c.drawString(170, 485, f"Valid: 2026-2027")
        
        # QR Code Box
        c.rect(370, 470, 60, 60)
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(400, 500, "SCAN ME")
        
    elif type == "Project_Report":
        # PROJECT REPORT
        c.setFont("Helvetica-Bold", 18)
        c.drawString(70, height-150, f"PROJECT REPORT: {data.get('Business', 'General')}")
        c.line(70, height-160, 500, height-160)
        
        c.setFont("Helvetica", 12)
        report_lines = [
            f"Applicant Mobile: +{data['phone']}",
            "Estimated Capital: Rs. 5,00,000",
            "Machinery Cost: Rs. 2,00,000",
            "Working Capital: Rs. 3,00,000",
            "Projected Profit: 25% Annually",
            "Eligible Schemes: PMEGP / Mudra / StandUp India"
        ]
        
        y = height - 200
        for line in report_lines:
            c.drawString(80, y, line)
            y -= 30
            
        c.rect(70, y-20, 470, 40)
        c.drawString(80, y-5, "NOTE: Submit this report to your bank for loan processing.")

    else:
        # APPLICATION RECEIPT
        c.setFont("Helvetica-Bold", 18)
        c.drawString(70, height-150, "APPLICATION ACKNOWLEDGMENT")
        c.line(70, height-170, 500, height-170)
        
        c.setFont("Helvetica", 12)
        y = height - 220
        for k, v in data.items():
            c.drawString(80, y, f"{k}:")
            c.drawString(250, y, f"{v}")
            y -= 35
            
        c.setFont("Helvetica-Oblique", 10)
        c.rect(70, 100, 470, 60)
        c.drawString(80, 140, "STATUS: PENDING AGENT CALL")
        c.drawString(80, 125, "An expert will contact you within 24 hours to collect documents.")
        c.drawString(80, 110, "Please keep your Aadhar and Pan Card ready.")

    c.save()
    return filename

# --- 3. HYBRID AI ENGINE (Sales Optimized) ---
def get_ai_reply(query):
    # If no key, fallback to smart offline
    if not API_KEY:
        return smart_offline_ai(query)

    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Prompt designed to sell services
        prompt = (f"User Query: '{query}'. "
                  "Act as a professional Indian Government Scheme Consultant. "
                  "Explain 1-2 relevant schemes briefly. "
                  "End by encouraging them to type '@Call' or 'Apply' to proceed.")
        res = model.generate_content(prompt)
        return f"🤖 *AI Consultant:*\n{res.text}"
    except:
        return smart_offline_ai(query)

def smart_offline_ai(query):
    q = query.lower()
    if "loan" in q: return "🤖 *AI:* For business loans, check **PMEGP** (ID 101) or **Mudra** (ID 102). Type '@Call' to speak to an agent."
    if "farm" in q: return "🤖 *AI:* Farmers can check **PM Kisan** (ID 201). Type '@Call' for help."
    return "🤖 *AI:* I found relevant info. Search for 'Loan', 'Farm', or type '@Call' to talk to an expert."

# --- 4. ROUTES ---
@app.route("/", methods=['GET'])
def health(): return "✅ Yojna-GPT Enterprise Live"

# Admin Dashboard to download leads
@app.route("/admin/leads", methods=['GET'])
def download_leads():
    if os.path.exists(LEADS_FILE):
        return send_file(LEADS_FILE, as_attachment=True)
    return "No leads yet."

@app.route("/download/<filename>")
def download(filename): return send_from_directory(PDF_FOLDER, filename)

@app.route("/whatsapp", methods=['POST'])
def whatsapp():
    try:
        msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '').replace("whatsapp:", "")
        resp = MessagingResponse()
        
        m = msg.lower()

        # 1. GREETING (The Menu)
        if m in ['hi', 'hello', 'menu', 'start', 'help', 'hey']:
            save_lead(sender, "Greeting", "New User")
            resp.message("🇮🇳 *Welcome to Yojna Seva Kendra*\n\n"
                       "I can help you get Government Loans & Subsidies.\n\n"
                       "🔥 *Power Tools:*\n"
                       "1️⃣ *@Card* : Get Member ID\n"
                       "2️⃣ *@Plan <Biz>* : Project Report\n"
                       "3️⃣ *@Calc <Amt>* : Subsidy Check\n"
                       "4️⃣ *@EMI <Amt>* : EMI Calc\n"
                       "5️⃣ *@Call* : Request Call\n"
                       "6️⃣ *@Status* : Track App\n"
                       "7️⃣ *@Center* : Find CSC\n"
                       "8️⃣ *@Docs* : Checklist\n"
                       "9️⃣ *@Share* : Invite Friends\n\n"
                       "🔍 *Search:* 'Textile', 'Solar', 'Loan'")
            return Response(str(resp), mimetype='application/xml')

        # 2. MILLION DOLLAR FEATURES
        if m.startswith("@card"):
            save_lead(sender, "Feature", "ID Card")
            pdf = generate_pdf("Card", {"phone": sender})
            resp.message(f"💳 *ID Card Generated!*\n⬇️ {request.host_url}download/{pdf}")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@plan"):
            biz = msg[6:] or "General"
            save_lead(sender, "Feature", f"Report: {biz}")
            pdf = generate_pdf("Project_Report", {"phone": sender, "Business": biz})
            resp.message(f"📊 *Project Report Ready!*\nBusiness: {biz}\n⬇️ {request.host_url}download/{pdf}")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@call"):
            save_lead(sender, "HOT LEAD", "Requested Call")
            resp.message("📞 *Request Received!* \n\nA senior officer will call you shortly to discuss your loan requirement.")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@calc"):
            try:
                amt = int(m.split()[1])
                save_lead(sender, "Feature", f"Calc: {amt}")
                resp.message(f"💰 *Subsidy Estimate:*\nLoan: ₹{amt:,}\nGovt Subsidy (35%): ₹{int(amt*0.35):,}\n\n👉 Type *@Call* to process this loan.")
            except:
                resp.message("❌ Usage: @Calc <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@emi"):
            try:
                amt = int(m.split()[1])
                emi = (amt * 0.0083 * 1.64) / 0.64 
                resp.message(f"🧮 *EMI Est (5Yrs):* ₹{int(emi):,}/month")
            except:
                resp.message("❌ Usage: @EMI <Amount>")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@status"):
            resp.message(f"📡 *Status Tracker*\nUser: +{sender[-4:]}\n\nApp ID: #YJ-882\nStage: 🟡 *Bank Verification*\nEst. Time: 3 Days")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@center"):
            resp.message("🏢 *Nearest CSC Centers:*\n1. Main Market (0.5km)\n2. Post Office Rd (1.2km)")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@admin"):
            # Secret command for YOU to get the leads
            link = f"{request.host_url}admin/leads"
            resp.message(f"🔒 *Admin Dashboard*\nDownload Leads: {link}")
            return Response(str(resp), mimetype='application/xml')

        if m.startswith("@share"):
            resp.message("🔗 *Share Link:* https://wa.me/14155238886?text=Hi")
            return Response(str(resp), mimetype='application/xml')

        # 3. APPLY COMMAND
        if m.startswith("apply"):
            try:
                sid = int(m.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    save_lead(sender, "Application", s['title'])
                    pdf = generate_pdf("Receipt", {"Scheme": s['title'], "phone": sender, "Date": datetime.datetime.now().strftime("%Y-%m-%d")})
                    resp.message(f"✅ *Request Registered: {s['title']}*\n\nYour Ticket: {request.host_url}download/{pdf}\n\nOur agent will contact you.")
                else:
                    resp.message("❌ Invalid ID.")
            except:
                resp.message("❌ Usage: Apply <ID>")
            return Response(str(resp), mimetype='application/xml')

        # 4. DATABASE SEARCH (High Precision)
        if m.isdigit():
            # Quick ID Lookup
            sid = int(m)
            s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
            if s:
                resp.message(f"📌 *{s['title']}* (ID: {s['id']})\n💰 {s['desc']}\n👉 Reply *Apply {s['id']}*\n\n")
                return Response(str(resp), mimetype='application/xml')

        results = [s for s in SCHEMES_DB if m in s['tags'] or m in s['title'].lower()]
        if results:
            save_lead(sender, "Search", m)
            txt = f"🔍 *Found {len(results)} Schemes:*\n\n"
            for x in results[:3]:
                txt += f"📌 *{x['title']}* (ID: {x['id']})\n💰 {x['desc']}\n👉 Reply *Apply {x['id']}*\n\n"
            resp.message(txt)
            return Response(str(resp), mimetype='application/xml')

        # 5. AI FALLBACK
        save_lead(sender, "AI Query", m)
        resp.message(get_ai_reply(msg))
        return Response(str(resp), mimetype='application/xml')

    except Exception as e:
        print(f"Error: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return Response(str(r), mimetype='application/xml')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
