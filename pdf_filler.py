import os
from pypdf import PdfReader, PdfWriter

# --- CONFIGURATION ---
# You need a blank PDF form in your folder. 
# Name it 'form_template.pdf'.
TEMPLATE_PATH = "form_template.pdf"
OUTPUT_FOLDER = "generated_applications"

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def fill_application_form(user_data):
    """
    Fills the Government PDF with user data.
    user_data: Dictionary like {'Name': 'Ramesh', 'City': 'Pune'}
    """
    try:
        reader = PdfReader(TEMPLATE_PATH)
        writer = PdfWriter()

        # Copy all pages from template to writer
        writer.append_pages_from_reader(reader)
        
        # Get the first page (usually where form fields are)
        page = writer.pages[0]

        # ---------------------------------------------------------
        # CRITICAL: You must know the "Field Names" inside the PDF.
        # Use https://www.pdfescape.com to open your PDF and see field names.
        # Below are generic names found in most govt forms.
        # ---------------------------------------------------------
        fields = {
            "Name_Field": user_data.get("name", ""),
            "Mobile_Field": user_data.get("mobile", ""),
            "City_Field": user_data.get("city", ""),
            "Pan_Card_No": user_data.get("pan", ""),
            "Industry_Type": user_data.get("industry", ""),
            "Scheme_Name": "Maharashtra PSI Scheme 2026"
        }

        # Fill the fields
        writer.update_page_form_field_values(page, fields)

        # Generate a unique filename
        filename = f"{user_data['name']}_Application.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, filename)

        # Save the filled PDF
        with open(output_path, "wb") as output_stream:
            writer.write(output_stream)
        
        print(f"[SUCCESS] Generated application for {user_data['name']}")
        return output_path

    except Exception as e:
        print(f"[ERROR] PDF Generation failed: {e}")
        return None

# --- TEST RUN ---
if __name__ == "__main__":
    # Create a dummy template if it doesn't exist just to test
    if not os.path.exists(TEMPLATE_PATH):
        print("⚠️ Please put a real 'form_template.pdf' in this folder.")
    else:
        sample_user = {
            "name": "Ramesh Textiles Pvt Ltd",
            "mobile": "9876543210",
            "city": "Amravati",
            "pan": "ABCDE1234F",
            "industry": "Textile"
        }
        fill_application_form(sample_user)
```

**How to connect this to the Bot:**
In your `bot_ai.py`, when a user says "Apply now", you simply call:
`pdf_path = fill_application_form(user_details)`
`msg.media(pdf_path)` (This sends the PDF back to them on WhatsApp!)

---

### **Step 2: Deployment (Go Live 24/7)**

You cannot run `ngrok` forever. We will use **Render.com** (it's free and easy).

1.  **Create a `Procfile`**:
    Create a new file named `Procfile` (no extension) and paste this line:
    ```text
    web: gunicorn bot_ai:app