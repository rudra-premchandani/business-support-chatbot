# =============================================================================
# chatbot.py — Keryar Chatbot Core Logic
# ⚠️  THIS IS YOUR ORIGINAL CODE, preserved as-is.
#     Streamlit UI calls (st.*) have been removed so this file can run
#     as a plain Python module imported by app.py.
#     All business logic, DB queries, AI calls, and email functions are
#     100 % unchanged from your original keryar_chatbot_streamlit.py.
# =============================================================================

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

# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS TYPES  (Matching portfolio.category field)
# ─────────────────────────────────────────────────────────────────────────────
BUSINESS_TYPES = [
    "Sports", "Education", "Electronics", "AutoMobile", "Fashion",
    "Food", "Technology", "Industries", "Healthcare", "Jewellers",
    "Service Industries", "Resort", "Interior", "Cinemas",
    "Printing", "Real Estates"
]

# ─────────────────────────────────────────────────────────────────────────────
# CONTACT INFO
# ─────────────────────────────────────────────────────────────────────────────
KERYAR_PHONE = "+91 99132 62167"
KERYAR_EMAIL = "connect@keryar.com"

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 4306
DB_USER     = "root"
DB_PASSWORD = ""
DB_NAME     = "keryar"

# ─────────────────────────────────────────────────────────────────────────────
# EMAIL CONFIG
# ─────────────────────────────────────────────────────────────────────────────
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 587
SENDER_EMAIL   = "your-email@gmail.com"        # ⚠️ CHANGE THIS
SENDER_PASSWORD = "your-app-password"           # ⚠️ CHANGE THIS
EMAIL_ENABLED  = False                          # ⚠️ Set True after configuring

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI CONFIG
# ─────────────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyDS-GsD39fEiV8AJr0i6pYSPk3AKzId7zI"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


# =============================================================================
# DATABASE CONNECTION FUNCTIONS
# =============================================================================

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
        print(f"Database connection error: {e}")
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


# =============================================================================
# CHAT HISTORY SAVING FUNCTIONS  (Saves to existing chat_leads table)
# =============================================================================

def save_chat_history_to_db(email, chat_history, session_id):
    """Save entire chat history as JSON in the message field"""
    if not email or not chat_history:
        return False

    db = cursor = None
    try:
        db = get_db_connection()
        if not db:
            print("❌ Database connection failed for saving chat history")
            return False

        cursor = db.cursor()

        chat_data = []
        for chat in chat_history:
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
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


def load_chat_history_from_db(email):
    """Load chat history from database (for returning users)"""
    db = cursor = None
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
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


def get_chat_summary(email):
    """Get summary of chat from database"""
    db = cursor = None
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
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


# =============================================================================
# EMAIL FUNCTIONS
# =============================================================================

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
        <html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <img src="https://keryar.com/assets/img/logo.png" alt="Keryar Logo" style="width: 150px; margin-bottom: 20px;">
                <h2 style="color: #667eea;">Hi {name}! 👋</h2>
                <p>Thank you for chatting with our AI assistant. We're excited to help you!</p>
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #667eea;">What's Next?</h3>
                    <ul style="padding-left: 20px;">
                        <li>Our team will review your requirements</li>
                        <li>We'll reach out within 24 hours</li>
                        <li>We'll discuss the best solutions for you</li>
                    </ul>
                </div>
                <h3 style="color: #667eea;">Our Services:</h3>
                <ul style="padding-left: 20px;">
                    <li>💻 Web &amp; Mobile Development</li>
                    <li>🛒 E-commerce Solutions</li>
                    <li>📱 Mobile Applications</li>
                    <li>📈 Digital Marketing</li>
                    <li>🎨 UI/UX Design</li>
                    <li>🔍 SEO &amp; Social Media</li>
                </ul>
                <div style="background-color: #667eea; color: white; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Contact Us</h3>
                    <p style="margin: 5px 0;">📞 Phone: {KERYAR_PHONE}</p>
                    <p style="margin: 5px 0;">📧 Email: {KERYAR_EMAIL}</p>
                    <p style="margin: 5px 0;">🌐 Website: <a href="https://keryar.com" style="color: white;">keryar.com</a></p>
                </div>
                <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                    © 2026 Keryar Digital Solutions. All rights reserved.<br>
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body></html>"""

        text_body = f"""Hi {name}!\n\nThank you for chatting with Keryar's AI assistant!\n
Our team will review your requirements and reach out within 24 hours.\n
Contact Us:\n📞 {KERYAR_PHONE}\n📧 {KERYAR_EMAIL}\n🌐 https://keryar.com"""

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email sent successfully to {email}")
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
        <html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #667eea;">🔔 New Lead Alert</h2>
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #667eea;">Lead Details:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px; font-weight: bold; width: 30%;">Name:</td><td style="padding: 8px;">{name}</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold;">Email:</td><td style="padding: 8px;">{email}</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold;">Phone:</td><td style="padding: 8px;">{phone}</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold;">User Type:</td><td style="padding: 8px;">{user_type}</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold;">Chat Messages:</td><td style="padding: 8px;">{message_count} messages exchanged</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold; vertical-align: top;">Message:</td><td style="padding: 8px;">{message if message else 'No message provided'}</td></tr>
                        <tr><td style="padding: 8px; font-weight: bold;">Date:</td><td style="padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                    </table>
                </div>
                <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                    This lead was captured through the Keryar AI Chatbot.
                </p>
            </div>
        </body></html>"""

        text_body = f"""NEW LEAD FROM CHATBOT\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nUser Type: {user_type}\nMessages: {message_count}\nMessage: {message or 'None'}\nDate: {datetime.now()}"""

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


# =============================================================================
# CHATBOT FAQ DATABASE FUNCTIONS
# =============================================================================

def get_chatbot_categories():
    """Fetch unique FAQ categories from database"""
    try:
        db = get_db_connection()
        if not db:
            print("⚠️ Database connection failed in get_chatbot_categories")
            return ["Pricing", "Services", "Support", "Company", "Timeline", "Digital Marketing", "Payment"]

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT category
            FROM chatbot_faq
            WHERE status = 1
            ORDER BY category
        """)
        categories = cursor.fetchall()
        cursor.close()
        db.close()

        if categories:
            result = [cat['category'] for cat in categories]
            print(f"✅ Loaded {len(result)} FAQ categories: {result}")
            return result
        else:
            print("⚠️ No active FAQ categories found in database")
            return []

    except Exception as e:
        print(f"❌ Error fetching categories: {e}")
        return ["Pricing", "Services", "Support", "Company", "Timeline", "Digital Marketing", "Payment"]


def get_faq_by_category(category):
    """Fetch all FAQs for a specific category"""
    try:
        db = get_db_connection()
        if not db:
            print(f"⚠️ Database connection failed in get_faq_by_category for {category}")
            return []

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT question, answer, keywords, priority
            FROM chatbot_faq
            WHERE category = %s AND status = 1
            ORDER BY priority ASC, id ASC
        """, (category,))
        faqs = cursor.fetchall()
        cursor.close()
        db.close()

        print(f"✅ Found {len(faqs)} FAQs for category '{category}'")
        return faqs

    except Exception as e:
        print(f"❌ Error fetching FAQs for {category}: {e}")
        return []


def search_faq_by_keywords(user_query):
    """Search FAQ database by keywords"""
    try:
        db = get_db_connection()
        if not db:
            print(f"⚠️ Database connection failed in search_faq_by_keywords")
            return None

        cursor = db.cursor(dictionary=True)
        search_term = f"%{user_query}%"
        cursor.execute("""
            SELECT category, question, answer, priority
            FROM chatbot_faq
            WHERE status = 1
            AND (question LIKE %s OR answer LIKE %s OR keywords LIKE %s)
            ORDER BY priority ASC
            LIMIT 5
        """, (search_term, search_term, search_term))

        results = cursor.fetchall()
        cursor.close()
        db.close()

        print(f"✅ Search for '{user_query}' found {len(results) if results else 0} results")
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


# =============================================================================
# PORTFOLIO LOADING FROM SQL
# =============================================================================

# Module-level cache so we only hit the DB once per process restart
_portfolio_cache = None
_field_info_cache = None
_website_content_cache = None


def load_portfolio_from_db():
    """
    Load portfolio from the ACTUAL portfolio table.
    Matches exact schema: id, title, type, subtype, category, coverimage, description, etc.
    """
    global _portfolio_cache
    if _portfolio_cache is not None:
        return _portfolio_cache

    db = cursor = None
    try:
        db = get_db_connection()
        if not db:
            print("⚠️ Database connection not available")
            return {}

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, title, type, subtype, category, coverimage,
                   description, clientname, publishdate, isactive
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
                "img": f"https://api.fosterx.co{item['coverimage']}" if item.get('coverimage')
                       else "https://via.placeholder.com/300x200/667eea/ffffff?text=Portfolio",
                "url": f"https://keryar.com/workfolio/portfolio-details/{item.get('id', '')}"
            })

        print(f"✅ Loaded {len(portfolios)} portfolio items from database")
        print(f"📁 Portfolio organised into {len(portfolio_dict)} subtypes")
        _portfolio_cache = portfolio_dict
        return portfolio_dict

    except mysql.connector.Error as e:
        print(f"⚠️ Database error loading portfolio: {e}")
        return {}
    except Exception as e:
        print(f"⚠️ Error loading portfolio: {e}")
        return {}
    finally:
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


# =============================================================================
# FIELD INFO (Service Descriptions)
# =============================================================================

def load_field_info_from_sql():
    """Load field information from database"""
    global _field_info_cache
    if _field_info_cache is not None:
        return _field_info_cache

    db = cursor = None
    try:
        db = get_db_connection()
        if not db:
            print("⚠️ Database connection not available for field info")
            return get_default_field_info()

        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT field_key, description
            FROM field_info
            WHERE status = 1
            ORDER BY field_key
        """)
        field_items = cursor.fetchall()

        if not field_items:
            return get_default_field_info()

        field_dict = {item['field_key']: item['description'] for item in field_items}
        print(f"✅ Loaded {len(field_items)} field info entries")
        _field_info_cache = field_dict
        return field_dict

    except Exception as e:
        print(f"⚠️ Error loading field info: {e}")
        return get_default_field_info()
    finally:
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


def get_default_field_info():
    """Fallback field info if database is unavailable"""
    return {
        'development':          'We build robust, scalable, and innovative digital solutions tailored to your business needs.',
        'web_application':      'Custom web applications built with modern technologies for optimal performance.',
        'ecommerce':            'Complete e-commerce platforms with secure payment gateways and inventory management.',
        'website_development':  'Professional, responsive websites designed to captivate your audience.',
        'mobile_application':   'Native and cross-platform mobile applications for iOS and Android.',
        'uiux':                 'Intuitive and beautiful user interfaces that create memorable digital experiences.',
        'digital_marketing':    'Comprehensive digital marketing services to boost your online presence.',
        'seo':                  'Search engine optimization strategies that improve your website visibility.',
        'social_media':         'Complete social media management including content creation and advertising.'
    }


# =============================================================================
# LOAD WEBSITE CONTENT
# =============================================================================

def load_website_content():
    """Load content from Keryar website (cached in memory)"""
    global _website_content_cache
    if _website_content_cache is not None:
        return _website_content_cache

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

    _website_content_cache = website_text[:12000]
    return _website_content_cache


# =============================================================================
# AI RESPONSE FUNCTIONS
# =============================================================================

def get_ai_response(query, context=""):
    try:
        prompt = f"""
        You are a helpful assistant for Keryar, a digital solutions company.

        Context: {context}
        User query: {query}

        Provide a helpful, concise response (max 100 words).
        """
        response = model.generate_content(prompt)
        return response.text if response else "I'm here to help! How can I assist you?"
    except:
        return "Let me connect you with our team."


def get_company_answer_from_website(query):
    try:
        website_content = load_website_content()
        prompt = f"""
        Based on this website content:
        {website_content}

        Answer this question: {query}

        Be concise (max 80 words).
        """
        response = model.generate_content(prompt)
        return response.text if response else "Please visit keryar.com for more information."
    except:
        return "Visit https://keryar.com to learn more!"


# =============================================================================
# HELPER / VALIDATION FUNCTIONS
# =============================================================================

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
    keywords = ["back", "go back", "wrong", "no", "not this", "change", "mistake"]
    return any(keyword in text.lower() for keyword in keywords)


def is_company_related_query(text):
    keywords = ["keryar", "about you", "who are you", "your company", "location", "address", "contact"]
    return any(keyword in text.lower() for keyword in keywords)


# =============================================================================
# DATABASE SAVE FUNCTIONS
# =============================================================================

def save_initial_user_info(name, email, user_type, session_id):
    """Save initial user info (name, email, user_type) to database"""
    db = cursor = None
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
                (name, user_type, datetime.now(), session_id, 'new', email)
            )
        else:
            cursor.execute(
                """INSERT INTO chat_leads
                   (name, email, phone, user_type, message, Date, session_id, status)
                   VALUES (%s, %s, NULL, %s, '[]', %s, %s, %s)""",
                (name, email, user_type, datetime.now(), session_id, 'new')
            )

        db.commit()
        print(f"✅ Initial info saved: {name}, {email}, {user_type}")
        return True

    except Exception as e:
        print(f"❌ Error saving initial info: {e}")
        if db: db.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


def update_user_journey(email, service_interest):
    """Update user's service interest in the database"""
    db = cursor = None
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
                """UPDATE chat_leads
                   SET service_interest = %s, Date = %s
                   WHERE email = %s""",
                (new_interest, datetime.now(), email)
            )
            db.commit()
            return True

        return False

    except Exception as e:
        print(f"❌ Error updating journey: {e}")
        if db: db.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


def save_lead(name, email, phone, user_type, chat_history, session_id, business_type="", service_interest=""):
    """Save complete lead to database (with phone number)"""
    db = cursor = None
    try:
        db = get_db_connection()
        if not db:
            return False

        cursor = db.cursor()
        cursor.execute("SELECT id FROM chat_leads WHERE phone = %s OR email = %s", (phone, email))
        existing = cursor.fetchone()

        chat_json = json.dumps([{
            "role": chat["role"],
            "content": chat["content"],
            "timestamp": datetime.fromtimestamp(chat["timestamp"]).strftime('%Y-%m-%d %H:%M:%S'),
            "has_portfolio": 1 if chat.get("portfolio") else 0
        } for chat in chat_history], ensure_ascii=False)

        if existing:
            cursor.execute(
                """UPDATE chat_leads
                   SET name = %s, user_type = %s, phone = %s, business_type = %s,
                       service_interest = %s, message = %s, Date = %s, session_id = %s, status = %s
                   WHERE phone = %s OR email = %s""",
                (name, user_type, phone, business_type, service_interest, chat_json,
                 datetime.now(), session_id, 'contacted', phone, email)
            )
        else:
            cursor.execute(
                """INSERT INTO chat_leads
                   (name, email, phone, user_type, business_type, service_interest, message, Date, session_id, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, email, phone, user_type, business_type, service_interest, chat_json,
                 datetime.now(), session_id, 'contacted')
            )

        db.commit()
        return True

    except Exception as e:
        print(f"❌ Error saving lead: {e}")
        if db: db.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


# =============================================================================
# LOAD ALL DATA ON MODULE IMPORT
# =============================================================================

PORTFOLIO_DATA = load_portfolio_from_db()
FIELD_INFO     = load_field_info_from_sql()

print(f"📊 Total portfolio subtypes loaded: {len(PORTFOLIO_DATA)}")
for subtype, items in PORTFOLIO_DATA.items():
    print(f"   • {subtype}: {len(items)} items")