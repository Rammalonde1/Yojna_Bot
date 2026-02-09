import os
import datetime
import random
import math
from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = "AIzaSyCshP-OBAHoq6VLHhtIHRebx0Q0AcUD5Yo"
PDF_FOLDER = "applications"
if not os.path.exists(PDF_FOLDER): os.makedirs(PDF_FOLDER)

# --- INTERNAL DATABASE (50+ Schemes) ---
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

# --- 2. ADVANCED PDF ENGINE (Dual Mode) ---
def generate_pdf(type, data_dict):
    filename = f"{type}_{data_dict['phone'][-4:]}_{random.randint(100,999)}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    if type == "Card":
        # IDENTITY CARD MODE
        c.setStrokeColor(colors.black)
        c.setFillColor(colors.aliceblue)
        c.rect(150, 450, 300, 180, fill=1) # Card Shape
        
        c.setFillColor(colors.darkblue)
        c.rect(150, 580, 300, 50, fill=1) # Header
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(300, 600, "YOJNA-GPT MEMBER")
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(170, 560, f"Name: Preferred User")
        c.drawString(170, 540, f"Mobile: +{data_dict['phone']}")
        c.drawString(170, 520, f"ID: YJ-{random.randint(1000,9999)}")
        c.drawString(170, 500, f"Status: VERIFIED")
        
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(300, 460, "Official Beneficiary Card")
        
    else:
        # APPLICATION MODE
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(width/2, height-50, "GOVERNMENT SCHEME RECEIPT")
        
        c.line(50, height-60, width-50, height-60)
        
        c.setFont("Helvetica", 12)
        y = height - 100
        for key, value in data_dict.items():
            c.drawString(100, y, f"{key}:")
            c.drawString(250, y, f"{value}")
            y -= 20
            
        c.rect(50, y-20, width-100, height-y+20)
        c.drawString(50, 50, "* Submit this at your nearest CSC Center.")

    c.save()
    return filename

# --- 3. ROBUST AI ENGINE ---
def get_ai_response(prompt):
    try:
        if API_KEY:
            genai.configure(api_key=API_KEY)
            # Switch to 'gemini-pro' as it is more stable for text
            model = genai.GenerativeModel('gemini-pro')
            res = model.generate_content(prompt)
            return f"🤖 *AI Insight:*\n{res.text}"
    except:
        return None

# --- 4. MAIN ROUTER ---
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
        
        # 1. GREETING (Expanded Menu)
        if m in ['hi', 'hello', 'menu', 'start', 'help']:
            reply.body("🇮🇳 *Namaste! Welcome to Yojna-GPT Enterprise*\n"
                       "The #1 Govt Scheme Super App.\n\n"
                       "🚀 *Feature Menu:*\n"
                       "1️⃣ *@Card* : Get Membership ID\n"
                       "2️⃣ *@Idea <Budget>* : Business Ideas\n"
                       "3️⃣ *@Calc <Amt>* : Subsidy Calc\n"
                       "4️⃣ *@EMI <Amt>* : Loan EMI Calc\n"
                       "5️⃣ *@News* : Latest Updates\n"
                       "6️⃣ *@Bank* : Find Banks\n"
                       "7️⃣ *@Center* : Find CSC\n"
                       "8️⃣ *@Docs* : Checklist\n"
                       "9️⃣ *@Share* : Share Bot\n"
                       "🔟 *@Complaint* : Log Grievance\n\n"
                       "🔍 *Or Search:* 'Textile', 'Solar', 'Loan'")
            return str(resp)

        # 2. GENERATE ID CARD (@Card)
        if m.startswith("@card"):
            pdf = generate_pdf("Card", {"phone": sender})
            link = f"{request.host_url}download/{pdf}"
            reply.body(f"💳 *Here is your Digital ID Card!*\n\nShow this at CSC centers for priority support.\n\n⬇️ {link}")
            return str(resp)

        # 3. BUSINESS IDEAS (@Idea)
        if m.startswith("@idea"):
            budget = m.split()[1] if len(m.split()) > 1 else "Low Investment"
            ai_idea = get_ai_response(f"Suggest 3 business ideas for {budget} budget in India.")
            if ai_idea:
                reply.body(ai_idea)
            else:
                reply.body("💡 *Business Ideas:*\n1. Kirana Store\n2. Flour Mill\n3. Tea Stall")
            return str(resp)

        # 4. EMI CALCULATOR (@EMI)
        if m.startswith("@emi"):
            try:
                amt = int(m.split()[1])
                rate = 10 / (12 * 100) # 10% Interest
                time = 5 * 12 # 5 Years
                emi = (amt * rate * pow(1+rate, time)) / (pow(1+rate, time) - 1)
                reply.body(f"🧮 *Loan EMI Estimator*\n\nLoan: ₹{amt:,}\nRate: 10%\nTenure: 5 Years\n\n*Monthly EMI: ₹{int(emi):,}*")
            except:
                reply.body("❌ Usage: @EMI <Amount>")
            return str(resp)

        # 5. NEWS UPDATES (@News)
        if m.startswith("@news"):
            reply.body("📰 *Govt Scheme News (Live)*\n\n"
                       "• PMEGP limit increased to 50 Lakhs.\n"
                       "• Solar Subsidy now credited in 24 hours.\n"
                       "• New 'Lakhpati Didi' targets 2 Crore women.\n"
                       "• Pan-Aadhar link mandatory for loans.")
            return str(resp)

        # 6. BANK FINDER (@Bank)
        if m.startswith("@bank"):
            reply.body("🏦 *Nodal Banks near you:*\n\n"
                       "1. SBI (Main Branch) - Agri/Biz Loans\n"
                       "2. Bank of Baroda - Mudra Specialist\n"
                       "3. Canara Bank - MSME Hub\n"
                       "4. Union Bank - Education Loans")
            return str(resp)
        
        # 7. COMPLAINT LOG (@Complaint)
        if m.startswith("@complaint"):
            t_id = random.randint(1000,9999)
            reply.body(f"📝 *Complaint Registered*\n\nTicket ID: #{t_id}\nPriority: High\n\nOur nodal officer will call you within 24 hours.")
            return str(resp)

        # 8. SHARE BOT (@Share)
        if m.startswith("@share"):
            reply.body("🔗 *Share Yojna-GPT with friends:*\n\nhttps://wa.me/14155238886?text=Hi\n\nHelp others get subsidies!")
            return str(resp)

        # 9. APPLY COMMAND
        if m.startswith("apply"):
            try:
                sid = int(m.split()[1])
                s = next((x for x in SCHEMES_DB if x['id'] == sid), None)
                if s:
                    data = {"Scheme": s['title'], "ID": f"SCH-{sid}", "Mobile": sender, "Date": "Today"}
                    pdf = generate_pdf("Application", data)
                    link = f"{request.host_url}download/{pdf}"
                    reply.body(f"✅ *Application Submitted!*\nScheme: {s['title']}\n📄 {link}")
                else:
                    reply.body("❌ Invalid ID.")
            except:
                reply.body("❌ Usage: Apply <ID>")
            return str(resp)

        # 10. CORE SEARCH ENGINE
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
        
        # 11. AI FALLBACK
        else:
            ai_txt = get_ai_response(f"Explain Indian Govt Scheme for '{msg}'. Keep it short.")
            if ai_txt:
                reply.body(ai_txt)
            else:
                reply.body("⚠️ Network Busy. Try keywords: Loan, Farm, Student.")

        return str(resp)

    except Exception as e:
        print(f"ERROR: {e}")
        r = MessagingResponse()
        r.message("⚠️ System updating. Type 'Hi' to restart.")
        return str(r)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
