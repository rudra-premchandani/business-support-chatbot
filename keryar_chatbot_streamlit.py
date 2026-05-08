import streamlit as st
import google.generativeai as genai
import re
import mysql.connector
from datetime import datetime
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import requests
from bs4 import BeautifulSoup
import uuid

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="Keryar Chatbot", page_icon="🤖", layout="wide")

# ---------------- BUSINESS TYPES (Matching portfolio.category field) ---------------- #
BUSINESS_TYPES = [
    "Sports",
    "Education",
    "Electronics",
    "AutoMobile",
    "Fashion",
    "Food",
    "Technology",
    "Industries",
    "Healthcare",
    "Jewellers",
    "Service Industries",
    "Resort",
    "Interior",
    "Cinemas",
    "Printing",
    "Real Estates"
]

# ---------------- SIDEBAR ---------------- #
with st.sidebar:
    st.image("https://keryar.com/assets/img/logo.png", width=180)
    st.markdown(
        "<div style='margin-top:-6px;margin-bottom:4px;'>"
        "<span style='font-size:18px;font-weight:800;color:#a5b4fc;letter-spacing:-0.3px;'>"
        "Keryar Digital Solutions</span><br>"
        "<span style='font-size:12px;color:#94a3b8;'>Building products that scale 🚀</span>"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    if st.button("🔄 Restart Chat", key="restart_sidebar", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='line-height:2;font-size:13px;'>"
        "📞 &nbsp;<a href='tel:+919913262167' style='color:#a5b4fc;text-decoration:none;'>+91 99132 62167</a><br>"
        "📧 &nbsp;<a href='mailto:connect@keryar.com' style='color:#a5b4fc;text-decoration:none;'>connect@keryar.com</a><br>"
        "🌐 &nbsp;<a href='https://keryar.com' target='_blank' style='color:#a5b4fc;text-decoration:none;'>keryar.com</a>"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown(
        "<p style='font-size:11px;color:#64748b;text-align:center;margin:0;'>"
        "© 2026 Keryar. All rights reserved.</p>",
        unsafe_allow_html=True
    )

# ---------------- CONTACT INFO ---------------- #
KERYAR_PHONE = "+91 99132 62167"
KERYAR_EMAIL = "connect@keryar.com"

# ---------------- DATABASE CONFIG ---------------- #
DB_HOST = "localhost"
DB_PORT = 4306
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "keryar"

# ---------------- EMAIL CONFIG ---------------- #
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@gmail.com"        # ⚠️ CHANGE THIS
SENDER_PASSWORD = "your-app-password"         # ⚠️ CHANGE THIS
EMAIL_ENABLED = False                          # ⚠️ Set True after configuring

# ---------------- GEMINI CONFIG ---------------- #
GEMINI_API_KEY = "AIzaSyDS-GsD39fEiV8AJr0i6pYSPk3AKzId7zI"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- CUSTOM CSS ---------------- #
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f0f4ff 0%, #fafafa 100%);
    }
    h1 {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ecfdf5 0%, #dcfce7 55%, #bbf7d0 100%) !important;
        border-right: 1px solid rgba(22, 163, 74, 0.25);
    }
    [data-testid="stSidebar"] * { color: #14532d !important; }
    [data-testid="stSidebar"] .stMarkdown a { color: #166534 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(34, 197, 94, 0.3) !important; }
    .portfolio-card {
        border: 1px solid rgba(102,126,234,0.2);
        border-radius: 16px;
        padding: 14px;
        margin: 8px 0;
        background: linear-gradient(145deg, #ffffff, #f8f9ff);
        box-shadow: 0 4px 15px rgba(102,126,234,0.1);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        height: 100%;
    }
    .portfolio-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(102,126,234,0.2);
    }
    .no-projects-box {
        background: linear-gradient(135deg, #fff7ed, #fef3c7);
        border: 1.5px dashed #f59e0b;
        border-radius: 14px;
        padding: 28px 20px;
        text-align: center;
        margin: 12px 0;
    }
    .no-projects-box .np-icon { font-size: 40px; display: block; margin-bottom: 10px; }
    .no-projects-box .np-title { font-size: 17px; font-weight: 700; color: #92400e; margin-bottom: 6px; }
    .no-projects-box .np-sub { font-size: 13px; color: #b45309; }
    [data-testid="stChatMessage"] { border-radius: 16px !important; padding: 4px 2px !important; }
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    .small-back-button { margin: 6px 0; }
    .small-back-button button {
        font-size: 11px !important;
        padding: 4px 12px !important;
        height: 30px !important;
        background: #f1f5f9 !important;
        color: #64748b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    .home-button { margin: 6px 0; }
    .home-button button {
        font-size: 11px !important;
        padding: 4px 12px !important;
        height: 30px !important;
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        color: white !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(102,126,234,0.35) !important;
    }
    a.view-proj-btn {
        display: inline-block;
        padding: 7px 18px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white !important;
        text-decoration: none;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
        box-shadow: 0 2px 8px rgba(102,126,234,0.4);
        transition: opacity 0.2s;
    }
    a.view-proj-btn:hover { opacity: 0.88; }
    hr { border-color: rgba(102,126,234,0.15) !important; }
    [data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid rgba(102,126,234,0.2);
        border-radius: 16px;
        padding: 24px !important;
        box-shadow: 0 4px 20px rgba(102,126,234,0.08);
    }
    input, textarea { border-radius: 10px !important; border: 1.5px solid #e2e8f0 !important; }
    input:focus, textarea:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# DATABASE CONNECTION FUNCTIONS
# ============================================================================

def get_db_connection():
    """Get fresh database connection"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False,
            connect_timeout=5
        )
        return connection
    except mysql.connector.Error as e:
        # ✅ FIX #3: Replaced st.error() with print() to avoid calling Streamlit UI
        # functions from within @st.cache_data-decorated contexts, which causes
        # unpredictable rendering behavior.
        print(f"❌ Database connection error: {e}")
        return None

def test_db_connection():
    """Test database connection"""
    try:
        db = get_db_connection()
        if db and db.is_connected():
            db.close()
            return True
        return False
    except:
        return False

# ============================================================================
# CHAT HISTORY SAVING FUNCTIONS
# ============================================================================

def save_chat_history_to_db(email):
    """Save entire chat history as JSON in the message field"""
    if not email or not st.session_state.chat_history:
        return False

    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            print("❌ Database connection failed for saving chat history")
            return False

        cursor = db.cursor()

        chat_data = []
        for chat in st.session_state.chat_history:
            chat_entry = {
                "role": chat["role"],
                "content": chat["content"],
                "timestamp": datetime.fromtimestamp(chat["timestamp"]).strftime('%Y-%m-%d %H:%M:%S'),
                "has_portfolio": 1 if chat.get("portfolio") else 0
            }
            if chat.get("portfolio"):
                chat_entry["portfolio_count"] = len(chat["portfolio"])
                chat_entry["portfolio_titles"] = [p.get("title", "Untitled") for p in chat["portfolio"][:3]]
            chat_data.append(chat_entry)

        chat_json = json.dumps(chat_data, ensure_ascii=False)

        cursor.execute(
            """UPDATE chat_leads
               SET message = %s,
                   last_message_time = %s,
                   status = CASE
                       WHEN phone IS NOT NULL THEN 'contacted'
                       ELSE 'new'
                   END
               WHERE email = %s""",
            (chat_json, datetime.now(), email)
        )

        db.commit()
        print(f"✅ Chat history saved for {email} ({len(chat_data)} messages)")
        return True

    except Exception as e:
        print(f"❌ Error saving chat history: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

def load_chat_history_from_db(email):
    """Load chat history from database (for returning users)"""
    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            return []

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT message FROM chat_leads WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result and result['message']:
            try:
                chat_data = json.loads(result['message'])
                chat_history = []
                for chat in chat_data:
                    if isinstance(chat, dict) and 'role' in chat and 'content' in chat:
                        timestamp_str = chat.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp()
                        chat_history.append({
                            "role": chat["role"],
                            "content": chat["content"],
                            "portfolio": None,
                            "timestamp": timestamp
                        })
                print(f"✅ Loaded {len(chat_history)} messages for {email}")
                return chat_history
            except json.JSONDecodeError:
                print(f"⚠️ Message field is not JSON format for {email}")
                return []

        return []

    except Exception as e:
        print(f"❌ Error loading chat history: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

def get_chat_summary(email):
    """Get summary of chat from database"""
    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            """SELECT name, email, phone, user_type, business_type,
                      service_interest, session_id, last_message_time, message
               FROM chat_leads WHERE email = %s""",
            (email,)
        )
        result = cursor.fetchone()

        if result and result['message']:
            try:
                chat_data = json.loads(result['message'])
                result['message_count'] = len(chat_data)
                result['has_json_history'] = True
            except:
                result['message_count'] = 0
                result['has_json_history'] = False

        return result

    except Exception as e:
        print(f"❌ Error getting chat summary: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

# ============================================================================
# EMAIL FUNCTIONS
# ============================================================================

def send_thank_you_email(name, email, user_type):
    """Send automatic thank you email to user"""
    if not EMAIL_ENABLED:
        print("⚠️ Email sending is disabled.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Thank you for connecting with Keryar! 🚀"

        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <img src="https://keryar.com/assets/img/logo.png" alt="Keryar" style="width:150px;margin-bottom:20px;">
            <h2 style="color:#667eea;">Hi {name}! 👋</h2>
            <p>Thank you for chatting with our AI assistant. Our team will review your requirements and reach out within 24 hours.</p>
            <div style="background:#f3f4f6;padding:15px;border-radius:8px;margin:20px 0;">
                <h3 style="margin-top:0;color:#667eea;">Our Services:</h3>
                <ul>
                    <li>💻 Web & Mobile Development</li>
                    <li>🛒 E-commerce Solutions</li>
                    <li>📈 Digital Marketing</li>
                    <li>🎨 UI/UX Design</li>
                </ul>
            </div>
            <div style="background:#667eea;color:white;padding:15px;border-radius:8px;">
                <p style="margin:5px 0;">📞 {KERYAR_PHONE}</p>
                <p style="margin:5px 0;">📧 {KERYAR_EMAIL}</p>
                <p style="margin:5px 0;">🌐 <a href="https://keryar.com" style="color:white;">keryar.com</a></p>
            </div>
        </div></body></html>
        """
        text_body = f"Hi {name}!\n\nThank you for chatting with Keryar.\n\nPhone: {KERYAR_PHONE}\nEmail: {KERYAR_EMAIL}"

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent to {email}")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def send_lead_notification_email(name, email, phone, user_type, message):
    """Send notification to company about new lead"""
    if not EMAIL_ENABLED:
        print("⚠️ Email sending is disabled.")
        return False

    try:
        chat_summary = get_chat_summary(email)
        message_count = chat_summary.get('message_count', 0) if chat_summary else 0

        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = KERYAR_EMAIL
        msg['Subject'] = f"🔔 New Lead from Chatbot: {name}"

        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;">
        <div style="max-width:600px;margin:0 auto;padding:20px;">
            <h2 style="color:#667eea;">🔔 New Lead Alert</h2>
            <div style="background:#f3f4f6;padding:15px;border-radius:8px;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr><td style="padding:8px;font-weight:bold;width:30%;">Name:</td><td style="padding:8px;">{name}</td></tr>
                    <tr><td style="padding:8px;font-weight:bold;">Email:</td><td style="padding:8px;">{email}</td></tr>
                    <tr><td style="padding:8px;font-weight:bold;">Phone:</td><td style="padding:8px;">{phone}</td></tr>
                    <tr><td style="padding:8px;font-weight:bold;">User Type:</td><td style="padding:8px;">{user_type}</td></tr>
                    <tr><td style="padding:8px;font-weight:bold;">Chat Messages:</td><td style="padding:8px;">{message_count} messages</td></tr>
                    <tr><td style="padding:8px;font-weight:bold;vertical-align:top;">Message:</td><td style="padding:8px;">{message or 'None'}</td></tr>
                    <tr><td style="padding:8px;font-weight:bold;">Date:</td><td style="padding:8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                </table>
            </div>
        </div></body></html>
        """
        text_body = f"NEW LEAD\nName: {name}\nEmail: {email}\nPhone: {phone}\nType: {user_type}\nMessages: {message_count}\nDate: {datetime.now()}"

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"✅ Lead notification sent to {KERYAR_EMAIL}")
        return True

    except Exception as e:
        print(f"❌ Error sending lead notification: {e}")
        return False

# ============================================================================
# CHATBOT FAQ DATABASE FUNCTIONS
# ============================================================================

def get_chatbot_categories():
    """Fetch unique FAQ categories from database"""
    try:
        db = get_db_connection()
        if not db:
            return ["Pricing", "Services", "Support", "Company", "Timeline", "Digital Marketing", "Payment"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT category FROM chatbot_faq WHERE status = 1 ORDER BY category")
        categories = cursor.fetchall()
        cursor.close()
        db.close()

        if categories:
            return [cat['category'] for cat in categories]
        return []

    except Exception as e:
        print(f"❌ Error fetching categories: {e}")
        return ["Pricing", "Services", "Support", "Company", "Timeline", "Digital Marketing", "Payment"]

def get_faq_by_category(category):
    """Fetch all FAQs for a specific category"""
    try:
        db = get_db_connection()
        if not db:
            return []

        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT question, answer, keywords, priority FROM chatbot_faq WHERE category = %s AND status = 1 ORDER BY priority ASC, id ASC",
            (category,)
        )
        faqs = cursor.fetchall()
        cursor.close()
        db.close()
        return faqs

    except Exception as e:
        print(f"❌ Error fetching FAQs for {category}: {e}")
        return []

def search_faq_by_keywords(user_query):
    """Search FAQ database by keywords"""
    try:
        db = get_db_connection()
        if not db:
            return None

        cursor = db.cursor(dictionary=True)
        search_term = f"%{user_query}%"
        cursor.execute(
            """SELECT category, question, answer, priority FROM chatbot_faq
               WHERE status = 1 AND (question LIKE %s OR answer LIKE %s OR keywords LIKE %s)
               ORDER BY priority ASC LIMIT 5""",
            (search_term, search_term, search_term)
        )
        results = cursor.fetchall()
        cursor.close()
        db.close()
        return results if results else None

    except Exception as e:
        print(f"❌ Error searching FAQs: {e}")
        return None

def get_ai_response_with_faq_context(user_query, context=""):
    """Enhanced AI response using FAQ database"""
    try:
        faq_results = search_faq_by_keywords(user_query)

        faq_context = ""
        if faq_results:
            faq_context = "\n\nRelevant information from Keryar knowledge base:\n"
            for faq in faq_results:
                faq_context += f"\nQ: {faq['question']}\nA: {faq['answer']}\n"

        prompt = f"""You are Keryar's AI assistant. Answer based on the provided knowledge base.

User Query: {user_query}
{faq_context}
Additional Context: {context}

Instructions:
- Use information from the knowledge base if available
- Be helpful, concise, and professional
- Keep response under 150 words

Response:"""

        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        return f"I'm here to help! Please call us at {KERYAR_PHONE} or email {KERYAR_EMAIL}"

# ============================================================================
# PORTFOLIO LOADING FROM SQL
# ============================================================================

@st.cache_data(ttl=3600)
def load_portfolio_from_db():
    """Load portfolio from the ACTUAL portfolio table"""
    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            print("⚠️ Database connection not available")
            return {}

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, type, subtype, category, coverimage, description,
                   clientname, publishdate, isactive
            FROM portfolio
            WHERE isactive = 1
            ORDER BY publishdate DESC
        """)

        portfolios = cursor.fetchall()
        portfolio_dict = {}

        for item in portfolios:
            subtype = item.get('subtype', 'General')

            if subtype not in portfolio_dict:
                portfolio_dict[subtype] = []

            desc_text = item.get('description', '')
            if desc_text:
                from html import unescape
                desc_clean = re.sub('<[^<]+?>', '', desc_text)
                desc_clean = unescape(desc_clean)
                desc_clean = desc_clean[:200] + "..." if len(desc_clean) > 200 else desc_clean
            else:
                desc_clean = "No description available"

            portfolio_dict[subtype].append({
                "title": item.get('title', 'Untitled'),
                "desc": desc_clean,
                "category": item.get('category', 'General'),
                "type": item.get('type', 'General'),
                "img": f"https://api.fosterx.co{item['coverimage']}" if item.get('coverimage') else "https://via.placeholder.com/300x200/667eea/ffffff?text=Portfolio",
                "url": f"https://keryar.com/workfolio/portfolio-details/{item.get('id', '')}"
            })

        print(f"✅ Loaded {len(portfolios)} portfolio items")
        return portfolio_dict

    except Exception as e:
        print(f"⚠️ Error loading portfolio: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

# ============================================================================
# FIELD INFO
# ============================================================================

@st.cache_data(ttl=3600)
def load_field_info_from_sql():
    """Load field information from database"""
    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            return get_default_field_info()

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT field_key, description FROM field_info WHERE status = 1 ORDER BY field_key")
        field_items = cursor.fetchall()

        if not field_items:
            return get_default_field_info()

        return {item['field_key']: item['description'] for item in field_items}

    except Exception as e:
        print(f"⚠️ Error loading field info: {e}")
        return get_default_field_info()
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

def get_default_field_info():
    return {
        'development': 'We build robust, scalable, and innovative digital solutions tailored to your business needs.',
        'web_application': 'Custom web applications built with modern technologies for optimal performance.',
        'ecommerce': 'Complete e-commerce platforms with secure payment gateways and inventory management.',
        'website_development': 'Professional, responsive websites designed to captivate your audience.',
        'mobile_application': 'Native and cross-platform mobile applications for iOS and Android.',
        'uiux': 'Intuitive and beautiful user interfaces that create memorable digital experiences.',
        'digital_marketing': 'Comprehensive digital marketing services to boost your online presence.',
        'seo': 'Search engine optimization strategies that improve your website visibility.',
        'social_media': 'Complete social media management including content creation and advertising.'
    }

# ============================================================================
# LOAD WEBSITE CONTENT
# ============================================================================

# ✅ FIX #2: Changed @st.cache_resource to @st.cache_data.
# @st.cache_resource is for shared non-serializable global objects (DB connections,
# ML models). This function returns a plain string, so @st.cache_data is correct.
@st.cache_data(ttl=86400)
def load_website_content():
    """Load content from Keryar website"""
    urls = [
        "https://keryar.com",
        "https://keryar.com/about",
        "https://keryar.com/services",
        "https://keryar.com/contact"
    ]

    website_text = ""
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            website_text += soup.get_text(separator=" ")
        except:
            pass

    return website_text[:12000]

# ============================================================================
# LOAD ALL DATA
# ============================================================================

PORTFOLIO_DATA = load_portfolio_from_db()
FIELD_INFO = load_field_info_from_sql()

print(f"📊 Total portfolio subtypes loaded: {len(PORTFOLIO_DATA)}")
for subtype, items in PORTFOLIO_DATA.items():
    print(f"   • {subtype}: {len(items)} items")

# ============================================================================
# SESSION STATE
# ============================================================================

if "step" not in st.session_state:
    st.session_state.step = "welcome"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "show_initial_form" not in st.session_state:
    st.session_state.show_initial_form = False
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "current_service" not in st.session_state:
    st.session_state.current_service = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user_type" not in st.session_state:
    st.session_state.user_type = ""
if "initial_info_collected" not in st.session_state:
    st.session_state.initial_info_collected = False
if "email_sent" not in st.session_state:
    st.session_state.email_sent = False
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
# ✅ FIX #4: Added missing session state keys that were accessed via .get() in some
# steps but never initialized, which could cause KeyError in direct attribute access.
if "selected_faq_category" not in st.session_state:
    st.session_state.selected_faq_category = ""
if "selected_business_type" not in st.session_state:
    st.session_state.selected_business_type = ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def add_to_chat(role, content, portfolio=None):
    """Add message to chat history and save to database"""
    chat_entry = {
        "role": role,
        "content": content,
        "portfolio": portfolio,
        "timestamp": time.time()
    }
    st.session_state.chat_history.append(chat_entry)

    if st.session_state.user_email:
        save_chat_history_to_db(st.session_state.user_email)

def show_typing():
    time.sleep(0.5)

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_phone(phone):
    cleaned = re.sub(r'\D', '', phone)
    return len(cleaned) >= 10

def is_booking_request(text):
    keywords = ["book", "appointment", "schedule", "meet", "call me", "contact me", "interested"]
    return any(keyword in text.lower() for keyword in keywords)

def is_goodbye_message(text):
    keywords = ["bye", "goodbye", "see you", "thanks", "thank you", "that's all", "exit", "quit"]
    return any(keyword in text.lower() for keyword in keywords)

def is_go_back_request(text):
    # ✅ FIX #6: Removed "no" from keywords — it was far too broad and matched
    # any message containing "no" (e.g. "no problem", "I don't know", "not sure").
    # Replaced with more specific phrases that clearly signal navigation intent.
    keywords = ["go back", "wrong service", "not this service", "change service", "made a mistake"]
    return any(keyword in text.lower() for keyword in keywords)

def is_company_related_query(text):
    keywords = ["keryar", "about you", "who are you", "your company", "location", "address", "contact"]
    return any(keyword in text.lower() for keyword in keywords)

def render_home_button(key_suffix=""):
    st.markdown('<div class="home-button">', unsafe_allow_html=True)
    if st.button("🏠 Services", key=f"home_{key_suffix}", help="Return to services menu"):
        st.session_state.step = "show_services"
        add_to_chat("user", "🏠 Services")
        show_typing()
        add_to_chat("assistant", "Welcome back! Let's explore our services again. 😊")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_user_type_button(key_suffix=""):
    st.markdown('<div class="home-button">', unsafe_allow_html=True)
    if st.button("🏠 User Type", key=f"usertype_{key_suffix}", help="Back to user type selection"):
        st.session_state.step = "ask_user_type"
        add_to_chat("user", "🏠 Back to User Type")
        show_typing()
        add_to_chat("assistant", "Let's start fresh! Are you a:")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# DATABASE SAVE FUNCTIONS
# ============================================================================

def save_initial_user_info(name, email, user_type):
    """Save initial user info (name, email, user_type) to database"""
    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            print("❌ Database connection failed for initial save")
            return False

        cursor = db.cursor()
        cursor.execute("SELECT id FROM chat_leads WHERE email = %s", (email,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """UPDATE chat_leads
                   SET name = %s, user_type = %s, Date = %s, session_id = %s, status = %s
                   WHERE email = %s""",
                (name, user_type, datetime.now(), st.session_state.session_id, 'new', email)
            )
        else:
            cursor.execute(
                """INSERT INTO chat_leads
                   (name, email, phone, user_type, message, Date, session_id, status)
                   VALUES (%s, %s, NULL, %s, '[]', %s, %s, %s)""",
                (name, email, user_type, datetime.now(), st.session_state.session_id, 'new')
            )

        db.commit()
        print(f"✅ Initial info saved: {name}, {email}, {user_type}")
        return True

    except Exception as e:
        print(f"❌ Error saving initial info: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

def update_user_journey(email, service_interest):
    """Update user's service interest in the database"""
    # ✅ FIX #8: Guard against empty email before making DB call, preventing
    # silent SQL no-ops and unnecessary DB round-trips.
    if not email:
        print("⚠️ Skipping update_user_journey: email is empty")
        return False

    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            return False

        cursor = db.cursor()
        cursor.execute("SELECT service_interest FROM chat_leads WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            existing_interest = result[0] if result[0] else ""
            if service_interest not in existing_interest:
                new_interest = f"{existing_interest}, {service_interest}" if existing_interest else service_interest
            else:
                new_interest = existing_interest

            cursor.execute(
                "UPDATE chat_leads SET service_interest = %s, Date = %s WHERE email = %s",
                (new_interest, datetime.now(), email)
            )
            db.commit()
            return True

        return False

    except Exception as e:
        print(f"❌ Error updating journey: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

def save_lead(name, email, phone, user_type, business_type="", service_interest=""):
    """Save complete lead to database (with phone number)"""
    db = None
    cursor = None
    try:
        db = get_db_connection()
        if not db:
            st.error("❌ Database connection failed")
            return False

        cursor = db.cursor()
        cursor.execute("SELECT id FROM chat_leads WHERE phone = %s OR email = %s", (phone, email))
        existing = cursor.fetchone()

        chat_json = json.dumps([{
            "role": chat["role"],
            "content": chat["content"],
            "timestamp": datetime.fromtimestamp(chat["timestamp"]).strftime('%Y-%m-%d %H:%M:%S'),
            "has_portfolio": 1 if chat.get("portfolio") else 0
        } for chat in st.session_state.chat_history], ensure_ascii=False)

        if existing:
            cursor.execute(
                """UPDATE chat_leads
                   SET name = %s, user_type = %s, phone = %s, business_type = %s,
                       service_interest = %s, message = %s, Date = %s, session_id = %s, status = %s
                   WHERE phone = %s OR email = %s""",
                (name, user_type, phone, business_type, service_interest, chat_json,
                 datetime.now(), st.session_state.session_id, 'contacted', phone, email)
            )
        else:
            cursor.execute(
                """INSERT INTO chat_leads
                   (name, email, phone, user_type, business_type, service_interest, message, Date, session_id, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, email, phone, user_type, business_type, service_interest, chat_json,
                 datetime.now(), st.session_state.session_id, 'contacted')
            )

        db.commit()
        return True

    except Exception as e:
        st.error(f"❌ Error: {e}")
        if db:
            db.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if db and db.is_connected():
            db.close()

# ============================================================================
# AI RESPONSE FUNCTIONS
# ============================================================================

def get_ai_response(query, context=""):
    try:
        prompt = f"""You are a helpful assistant for Keryar, a digital solutions company.
Context: {context}
User query: {query}
Provide a helpful, concise response (max 100 words)."""
        response = model.generate_content(prompt)
        return response.text if response else "I'm here to help! How can I assist you?"
    except:
        return "Let me connect you with our team."

def get_company_answer_from_website(query):
    try:
        website_content = load_website_content()
        prompt = f"""Based on this website content:
{website_content}

Answer this question: {query}
Be concise (max 80 words)."""
        response = model.generate_content(prompt)
        return response.text if response else "Please visit keryar.com for more information."
    except:
        return "Visit https://keryar.com to learn more!"

# ============================================================================
# DISPLAY CHAT
# ============================================================================

st.markdown(
    "<h1 style='margin-bottom:0;'>💬 Pulse AI</h1>"
    "<p style='color:#94a3b8;font-size:14px;margin-top:2px;margin-bottom:16px;'>"
    "Your intelligent assistant for Keryar Digital Solutions</p>",
    unsafe_allow_html=True
)

for chat_idx, chat in enumerate(st.session_state.chat_history):
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

        if chat.get("portfolio") is not None:
            portfolio_items = chat["portfolio"]
            st.markdown("---")

            if len(portfolio_items) == 0:
                st.markdown(
                    """<div class="no-projects-box">
                        <span class="np-icon">🔍</span>
                        <div class="np-title">No projects found in this category yet</div>
                        <div class="np-sub">We may be working on something exciting soon — stay tuned! 🚀</div>
                    </div>""",
                    unsafe_allow_html=True
                )
            else:
                display_items = portfolio_items[:4]
                st.markdown(
                    f"<p style='font-weight:700;font-size:15px;margin-bottom:10px;'>"
                    f"📁 Related Projects &nbsp;<span style='background:#667eea;color:white;"
                    f"border-radius:20px;padding:2px 10px;font-size:12px;'>{len(display_items)}</span></p>",
                    unsafe_allow_html=True
                )

                cols = st.columns(2)
                for idx, item in enumerate(display_items):
                    with cols[idx % 2]:
                        st.markdown('<div class="portfolio-card">', unsafe_allow_html=True)
                        st.image(
                            item.get("img", "https://via.placeholder.com/300x200/667eea/ffffff?text=Project"),
                            use_container_width=True
                        )
                        st.markdown(
                            f"<p style='font-weight:700;font-size:14px;margin:6px 0 2px;'>{item.get('title', 'Project')}</p>",
                            unsafe_allow_html=True
                        )
                        desc = item.get('desc', 'No description available')
                        if len(desc) > 90:
                            desc = desc[:90] + "…"
                        st.caption(desc)
                        if item.get('url'):
                            st.markdown(
                                f'<a class="view-proj-btn" href="{item["url"]}" target="_blank" rel="noopener noreferrer">🔗 View Project</a>',
                                unsafe_allow_html=True
                            )
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("")

            st.markdown("---")
            st.markdown("### 💼 What would you like to do next?")

            col1, col2 = st.columns(2)

            # ✅ FIX #7: Use chat_idx (loop index) instead of raw float timestamp for
            # button keys. Float timestamps are imprecise and can collide when messages
            # are created within the same millisecond, causing DuplicateWidgetID errors.
            with col1:
                if st.button("💼 Get Quotation", key=f"quotation_{chat_idx}", use_container_width=True):
                    st.session_state.show_form = True
                    st.session_state.form_submitted = False
                    st.session_state.step = "contact_form"
                    add_to_chat("user", "I'd like to get a quotation")
                    show_typing()
                    add_to_chat("assistant",
                        f"Great! Please share your contact details.\n\n"
                        f"📞 {KERYAR_PHONE}\n"
                        f"📧 {KERYAR_EMAIL}"
                    )
                    st.rerun()

            with col2:
                if st.button("🔄 Explore More", key=f"explore_{chat_idx}", use_container_width=True):
                    add_to_chat("user", "I want to explore more services")
                    show_typing()
                    add_to_chat("assistant", "### 🎯 Let's explore more services!")
                    st.session_state.step = "show_services"
                    st.rerun()

# ============================================================================
# WELCOME SCREEN
# ============================================================================

if st.session_state.step == "welcome":
    with st.chat_message("assistant"):
        st.markdown(
            "👋 **Welcome to Keryar!**\n\n"
            "🚀 **Keryar** is a leading digital solutions company specializing in Development and Digital Marketing.\n\n"
            "I'm here to help you explore our services.\n\n"
            "**Let's get started!**"
        )
        if st.button("🚀 Start Chat", key="start_chat", use_container_width=True):
            add_to_chat("assistant", "👋 **Welcome to Keryar!**\n\nI'm here to help you explore our services.")
            st.session_state.show_initial_form = True
            st.session_state.step = "initial_form"
            st.rerun()

# ============================================================================
# INITIAL FORM
# ============================================================================

if st.session_state.show_initial_form and not st.session_state.initial_info_collected:
    with st.chat_message("assistant"):
        with st.form("initial_info_form"):
            st.markdown("### 📋 Please provide your information:")
            name = st.text_input("Name *", placeholder="Enter your name", key="initial_name")
            email = st.text_input("Email *", placeholder="your.email@example.com", key="initial_email")

            if st.form_submit_button("Continue", use_container_width=True):
                if not name or not email:
                    st.error("❌ Please provide both name and email.")
                elif not is_valid_email(email):
                    st.error("❌ Please enter a valid email address.")
                else:
                    st.session_state.user_name = name
                    st.session_state.user_email = email
                    st.session_state.initial_info_collected = True
                    st.session_state.show_initial_form = False

                    add_to_chat("user", f"Name: {name}\nEmail: {email}")
                    show_typing()

                    email_status = ""
                    if EMAIL_ENABLED:
                        if send_thank_you_email(name, email, "New User"):
                            email_status = "\n\n✉️ Check your inbox - we've sent you a welcome email!"
                            st.session_state.email_sent = True

                    add_to_chat("assistant", f"Great to meet you, {name}! 😊{email_status}")
                    st.session_state.step = "ask_user_type"
                    st.rerun()

# ============================================================================
# ASK USER TYPE
# ============================================================================

if st.session_state.step == "ask_user_type":
    with st.chat_message("assistant"):
        st.markdown("### 👤 I'd like to know more about you. Are you a:")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🎓 Student", key="user_student", use_container_width=True):
                st.session_state.user_type = "Student"
                add_to_chat("user", "🎓 Student")
                save_initial_user_info(st.session_state.user_name, st.session_state.user_email, "Student")
                st.session_state.step = "student_options"
                st.rerun()

        with col2:
            if st.button("💼 Salaried/Employee", key="user_salaried", use_container_width=True):
                st.session_state.user_type = "Salaried"
                add_to_chat("user", "💼 Salaried/Employee")
                save_initial_user_info(st.session_state.user_name, st.session_state.user_email, "Salaried")
                st.session_state.step = "salaried_options"
                st.rerun()

        with col3:
            if st.button("🏢 Business Owner", key="user_business", use_container_width=True):
                st.session_state.user_type = "Business"
                add_to_chat("user", "🏢 Business Owner")
                show_typing()
                save_initial_user_info(st.session_state.user_name, st.session_state.user_email, "Business")
                add_to_chat("assistant", f"Perfect, {st.session_state.user_name}! 🎯\n\nLet me show you our services.")
                st.session_state.step = "show_services"
                st.rerun()

        st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
        if st.button("← Back", key="back_from_user_type"):
            st.session_state.step = "welcome"
            st.session_state.initial_info_collected = False
            st.session_state.show_initial_form = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# STUDENT OPTIONS
# ============================================================================

if st.session_state.step == "student_options":
    with st.chat_message("assistant"):
        st.markdown("### 🎓 Student Services")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💼 Internship Opportunities", key="student_internship", use_container_width=True):
                add_to_chat("user", "💼 Internship Opportunities")
                show_typing()
                add_to_chat("assistant",
                    "🎉 **Internship Programs at Keryar:**\n\n"
                    "• Web Development\n• Mobile App Development\n• Digital Marketing\n• Duration: 3-6 months\n\n"
                    f"📞 {KERYAR_PHONE}"
                )
                st.session_state.step = "chat"
                st.rerun()

        with col2:
            if st.button("🎓 Training Programs", key="student_training", use_container_width=True):
                add_to_chat("user", "🎓 Training Programs")
                show_typing()
                add_to_chat("assistant",
                    "📚 **Training Programs:**\n\n"
                    "• Full Stack Development\n• Mobile App Development\n• Digital Marketing\n• UI/UX Design\n\n"
                    f"📞 {KERYAR_PHONE}"
                )
                st.session_state.step = "chat"
                st.rerun()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
            if st.button("← Back", key="back_from_student"):
                st.session_state.step = "ask_user_type"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            render_home_button("student_options")

# ============================================================================
# SALARIED OPTIONS
# ============================================================================

if st.session_state.step == "salaried_options":
    with st.chat_message("assistant"):
        st.markdown("### 💼 Services for Professionals")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💻 Freelance Projects", key="salaried_freelance", use_container_width=True):
                add_to_chat("user", "💻 Freelance Projects")
                show_typing()
                add_to_chat("assistant",
                    "🚀 **Freelance Opportunities:**\n\n"
                    "• Web development\n• Mobile app development\n• Content writing\n\n"
                    f"📞 {KERYAR_PHONE}"
                )
                st.session_state.step = "chat"
                st.rerun()

        with col2:
            if st.button("🎯 Career Opportunities", key="salaried_career", use_container_width=True):
                add_to_chat("user", "🎯 Career Opportunities")
                show_typing()
                add_to_chat("assistant",
                    "🌟 **Join Our Team!**\n\n"
                    "• Full Stack Developer\n• Mobile App Developer\n• Digital Marketing Specialist\n• UI/UX Designer"
                )
                st.session_state.step = "chat"
                st.rerun()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
            if st.button("← Back", key="back_from_salaried"):
                st.session_state.step = "ask_user_type"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            render_home_button("salaried_options")

# ============================================================================
# FAQ CATEGORIES
# ============================================================================

if st.session_state.step == "faq_categories":
    # ✅ FIX #9: Check only assistant messages for the duplicate guard.
    # Previously checked all roles — since user messages can also contain
    # "Common Questions", this guard incorrectly fired and skipped adding
    # the assistant's message.
    if not any(
        chat["role"] == "assistant" and "Common Questions" in chat["content"]
        for chat in st.session_state.chat_history
    ):
        show_typing()
        add_to_chat("assistant", "### 💬 Common Questions\n\nChoose a category:")

    st.markdown("### Select a FAQ Category:")
    categories = get_chatbot_categories()

    if categories:
        cols = st.columns(3)
        for idx, category in enumerate(categories):
            with cols[idx % 3]:
                if st.button(f"📁 {category}", key=f"faq_cat_{category}", use_container_width=True):
                    st.session_state.selected_faq_category = category
                    add_to_chat("user", category)
                    st.session_state.step = "show_faq"
                    st.rerun()
    else:
        st.warning(
            f"⚠️ **No FAQ categories available**\n\n"
            f"📞 {KERYAR_PHONE}\n📧 {KERYAR_EMAIL}"
        )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
        if st.button("← Back to Services", key="back_from_faq_cats"):
            st.session_state.step = "show_services"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        render_user_type_button("faq_categories")

# ============================================================================
# SHOW FAQ
# ============================================================================

if st.session_state.step == "show_faq":
    category = st.session_state.get('selected_faq_category', 'General')

    faqs = get_faq_by_category(category)

    # ✅ FIX #1 (Critical): The original check used:
    #     any(f"{category}" in chat["content"] for chat in chat_history)
    # This searched ALL roles (user + assistant). Since the user's click message
    # already contains the category name (added in faq_categories step), this was
    # ALWAYS True — meaning the FAQ response was NEVER added to chat.
    # Fix: check only assistant messages AND use the specific heading format.
    already_in_chat = any(
        chat["role"] == "assistant" and f"### 📂 {category}" in chat["content"]
        for chat in st.session_state.chat_history
    )

    if not already_in_chat:
        if faqs:
            show_typing()
            response = f"### 📂 {category} - FAQs\n\n"
            for faq in faqs:
                response += f"**Q: {faq['question']}**\n\n{faq['answer']}\n\n---\n\n"
            add_to_chat("assistant", response)
        else:
            show_typing()
            add_to_chat("assistant",
                f"⚠️ **No FAQs found for '{category}'**\n\n"
                f"Please contact us:\n📞 {KERYAR_PHONE}\n📧 {KERYAR_EMAIL}"
            )

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
        if st.button("← Categories", key="back_to_faq_cats2"):
            st.session_state.step = "faq_categories"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        render_home_button("show_faq")
    with col3:
        render_user_type_button("show_faq")

# ============================================================================
# SHOW SERVICES
# ============================================================================

if st.session_state.step == "show_services":
    # ✅ FIX #5: Check only assistant messages for the duplicate guard.
    # The original check matched any message containing "How can I help",
    # including user messages — skipping the assistant's service menu header.
    if not any(
        chat["role"] == "assistant" and "How can I help" in chat["content"]
        for chat in st.session_state.chat_history
    ):
        show_typing()
        add_to_chat("assistant", "### 🎯 How can I help you today?")

    with st.chat_message("assistant"):
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("💻 Development", key="dev_main", use_container_width=True):
                add_to_chat("user", "Development")
                update_user_journey(st.session_state.user_email, "Development")
                st.session_state.step = "development"
                st.rerun()

        with col2:
            if st.button("📈 Digital Marketing", key="dm_main", use_container_width=True):
                add_to_chat("user", "Digital Marketing")
                update_user_journey(st.session_state.user_email, "Digital Marketing")
                st.session_state.step = "digital_marketing"
                st.rerun()

        with col3:
            if st.button("💬 FAQs", key="faq_main", use_container_width=True):
                add_to_chat("user", "FAQs")
                st.session_state.step = "faq_categories"
                st.rerun()

        st.markdown("---")
        render_user_type_button("show_services")

# ============================================================================
# DEVELOPMENT
# ============================================================================

if st.session_state.step == "development":
    # ✅ FIX #5 (same pattern): Check only assistant messages.
    if not any(
        chat["role"] == "assistant" and chat["content"].startswith("### 🛠 Development Services")
        for chat in st.session_state.chat_history
    ):
        show_typing()
        add_to_chat(
            "assistant",
            f"### 🛠 Development Services\n\n"
            f"{FIELD_INFO.get('development', 'Development services')}\n\n"
            f"**Choose a category:**"
        )

    with st.chat_message("assistant"):
        options = ["Website", "Mobile App", "Ecommerce"]
        cols = st.columns(2)

        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"dev_{opt}", use_container_width=True):
                    add_to_chat("user", opt)
                    update_user_journey(st.session_state.user_email, opt)
                    st.session_state.current_service = opt
                    st.session_state.step = "select_business_type"
                    st.rerun()

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
            if st.button("← Back to Services", key="back_from_development"):
                st.session_state.step = "show_services"
                add_to_chat("user", "← Back")
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            render_home_button("development")
        with col3:
            render_user_type_button("development")

# ============================================================================
# BUSINESS TYPE SELECTION
# ============================================================================

if st.session_state.step == "select_business_type":
    with st.chat_message("assistant"):
        st.markdown("### 🏷 Select Business Category")
        st.markdown("Choose a business domain to see relevant projects:")

        cols = st.columns(3)
        for i, btype in enumerate(BUSINESS_TYPES):
            with cols[i % 3]:
                if st.button(btype, key=f"biz_{btype}", use_container_width=True):
                    st.session_state.selected_business_type = btype
                    add_to_chat("user", btype)
                    show_typing()

                    update_user_journey(st.session_state.user_email, f"{st.session_state.current_service} - {btype}")

                    portfolio = [
                        item for item in PORTFOLIO_DATA.get(st.session_state.current_service, [])
                        if item.get("category") == btype
                    ]
                    portfolio_display = portfolio[:4]

                    if len(portfolio_display) == 0:
                        add_to_chat(
                            "assistant",
                            f"### {st.session_state.current_service} — {btype}",
                            portfolio=[]
                        )
                    else:
                        add_to_chat(
                            "assistant",
                            f"### {st.session_state.current_service} — {btype}\n\n"
                            f"**Here are {len(portfolio_display)} project(s):**",
                            portfolio=portfolio_display
                        )

                    st.session_state.step = "chat"
                    st.rerun()

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
            if st.button("← Back", key="back_from_biztype"):
                st.session_state.step = "development"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            render_home_button("select_business_type")
        with col3:
            render_user_type_button("select_business_type")

# ============================================================================
# DIGITAL MARKETING
# ============================================================================

if st.session_state.step == "digital_marketing":
    # ✅ FIX #5 (same pattern): Check only assistant messages.
    if not any(
        chat["role"] == "assistant" and chat["content"].startswith("### 📈 Digital Marketing")
        for chat in st.session_state.chat_history
    ):
        show_typing()
        add_to_chat("assistant",
            f"### 📈 Digital Marketing\n\n{FIELD_INFO.get('digital_marketing', '')}\n\n**Choose a category:**"
        )

    with st.chat_message("assistant"):
        options = ["Social Media", "SEO", "Branding"]
        cols = st.columns(2)

        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"dm_{opt}", use_container_width=True):
                    add_to_chat("user", opt)
                    show_typing()
                    update_user_journey(st.session_state.user_email, opt)

                    portfolio = PORTFOLIO_DATA.get(opt, [])
                    portfolio_display = portfolio[:4]

                    if len(portfolio_display) == 0:
                        add_to_chat("assistant", f"### {opt}", portfolio=[])
                    else:
                        add_to_chat("assistant",
                            f"### {opt}\n\n**Our Top {len(portfolio_display)} {opt} Projects:**",
                            portfolio=portfolio_display
                        )

                    st.session_state.step = "chat"
                    st.rerun()

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="small-back-button">', unsafe_allow_html=True)
            if st.button("← Back to Services", key="back_from_dm"):
                st.session_state.step = "show_services"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            render_home_button("digital_marketing")
        with col3:
            render_user_type_button("digital_marketing")

# ============================================================================
# CONTACT FORM
# ============================================================================

if st.session_state.show_form and not st.session_state.form_submitted:
    with st.chat_message("assistant"):
        with st.form("lead_form", clear_on_submit=True):
            st.markdown("### 📩 Complete Your Contact Information")

            st.text_input("Name", value=st.session_state.user_name, disabled=True)
            st.text_input("Email", value=st.session_state.user_email, disabled=True)

            phone = st.text_input("Phone Number *", placeholder="+91 99999 99999", key="phone_input")
            message = st.text_area("Message (Optional)", placeholder="Tell us about your requirements...", key="message_input", height=100)

            col1, col2 = st.columns([3, 1])
            with col1:
                submitted = st.form_submit_button("📞 Submit", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)

            if cancel:
                st.session_state.show_form = False
                add_to_chat("user", "Cancelled")
                show_typing()
                add_to_chat("assistant", "No problem! 😊")
                st.session_state.step = "chat"
                st.rerun()

            if submitted:
                if not phone:
                    st.error("❌ Please enter your phone number.")
                elif not is_valid_phone(phone):
                    st.error("❌ Please enter a valid phone number.")
                else:
                    business_type = st.session_state.get('selected_business_type', '')
                    service_interest = st.session_state.get('current_service', '')

                    if save_lead(st.session_state.user_name, st.session_state.user_email, phone,
                                 st.session_state.user_type, business_type, service_interest):
                        st.session_state.form_submitted = True
                        st.session_state.show_form = False

                        email_confirmation = ""
                        if EMAIL_ENABLED:
                            if send_thank_you_email(st.session_state.user_name, st.session_state.user_email, st.session_state.user_type):
                                email_confirmation = "\n\n📧 Check your email for confirmation!"
                            send_lead_notification_email(
                                st.session_state.user_name, st.session_state.user_email,
                                phone, st.session_state.user_type, message
                            )

                        add_to_chat("user", f"📞 {phone}")
                        show_typing()
                        add_to_chat("assistant",
                            f"✅ **Thank you, {st.session_state.user_name}!**\n\n"
                            f"We'll reach out within 24 hours.{email_confirmation}"
                        )

                        st.success("✅ Submitted successfully!")
                        st.session_state.step = "chat"
                        st.rerun()

# ============================================================================
# CHAT INPUT
# ============================================================================

if st.session_state.step not in ["ended", "welcome", "ask_user_type", "student_options", "salaried_options"] and st.session_state.initial_info_collected:
    user_input = st.chat_input("Type your message...")

    if user_input:
        add_to_chat("user", user_input)

        if is_go_back_request(user_input):
            show_typing()
            add_to_chat("assistant", "No problem! Let's go back.")
            st.session_state.step = "show_services"
            st.rerun()

        elif is_booking_request(user_input):
            show_typing()
            add_to_chat("assistant", f"📅 **Book an Appointment!**\n\n📞 {KERYAR_PHONE}")
            st.session_state.show_form = True
            st.session_state.form_submitted = False
            st.session_state.step = "contact_form"
            st.rerun()

        elif is_goodbye_message(user_input) and not st.session_state.form_submitted:
            show_typing()
            add_to_chat("assistant", f"Thank you, {st.session_state.user_name}! 😊")
            st.session_state.show_form = True
            st.session_state.form_submitted = False
            st.session_state.step = "contact_form"
            st.rerun()

        else:
            show_typing()
            context = f"User {st.session_state.user_name} ({st.session_state.user_type}) asking: {user_input}"

            if is_company_related_query(user_input):
                response = get_company_answer_from_website(user_input)
            else:
                response = get_ai_response_with_faq_context(user_input, context)

            add_to_chat("assistant", f"{response}\n\n💬 Any other questions?")
            st.rerun()

# ============================================================================
# NAVIGATION BUTTONS IN CHAT
# ============================================================================

if st.session_state.step == "chat" and st.session_state.initial_info_collected:
    with st.chat_message("assistant"):
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            render_home_button("chat_response")
        with col2:
            render_user_type_button("chat_response")