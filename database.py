import sqlite3
import os
import json
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mrunmay_leads.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create leads table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        service TEXT NOT NULL,
        specific_service TEXT,
        location TEXT,
        message TEXT,
        status TEXT DEFAULT 'New',
        created_at TEXT NOT NULL
    )
    """)
    
    # Create settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Create events table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        poster_image TEXT,
        rate INTEGER DEFAULT 400,
        dates TEXT,
        timings TEXT,
        venue TEXT,
        highlights TEXT,
        contacts TEXT,
        enabled INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # Create tickets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pass_id TEXT UNIQUE NOT NULL,
        event_id INTEGER,
        event_title TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        city TEXT,
        date_selected TEXT,
        quantity INTEGER DEFAULT 1,
        rate_per_ticket INTEGER DEFAULT 399,
        total_amount INTEGER DEFAULT 399,
        payment_status TEXT DEFAULT 'Paid',
        utr_reference TEXT,
        booking_status TEXT DEFAULT 'Confirmed',
        razorpay_order_id TEXT,
        razorpay_payment_id TEXT,
        razorpay_signature TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Create payments table for full transaction ledger
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT UNIQUE NOT NULL,
        order_id TEXT,
        service_type TEXT NOT NULL,
        customer_name TEXT NOT NULL,
        phone TEXT NOT NULL,
        amount REAL NOT NULL,
        payment_mode TEXT NOT NULL,
        sub_method TEXT DEFAULT 'UPI',
        transaction_ref TEXT,
        status TEXT DEFAULT 'Success',
        pass_id TEXT,
        details TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # Ensure razorpay columns exist for existing tables
    cursor.execute("PRAGMA table_info(tickets)")
    ticket_cols = [col["name"] for col in cursor.fetchall()]
    if "razorpay_order_id" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN razorpay_order_id TEXT")
    if "razorpay_payment_id" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN razorpay_payment_id TEXT")
    if "razorpay_signature" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN razorpay_signature TEXT")
    if "gst_amount" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN gst_amount REAL DEFAULT 0")
    if "gst_percent" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN gst_percent REAL DEFAULT 0")
    
    # Insert default settings if not exists
    default_settings = {
        "owner_phone": "919938866544",
        "business_name": "MRUNMAYA ASSOCIATES",
        "tagline": "Citizen Services, Event Tickets & Digital Solutions",
        "address": "Plot No.629, Ebaranga, Jatni Rd, Sundarpada, Bhubaneswar, Odisha 751002",
        "email": "mrunmay.service@gmail.com",
        "admin_pin": "1234",
        "working_hours": "08:00 AM - 09:00 PM (All 7 Days)",
        "upi_id": "PPQR01.DOENZS@iob",
        "payee_name": "MRUNMAYA ASSOCIATES",
        "payment_enabled": "1",
        "razorpay_key_id": "rzp_live_TjiX5CotSd0Lrk",
        "razorpay_key_secret": "Z67kRRLfcjLXoHcAA1ndrs37",
        "razorpay_enabled": "1",
        "gst_enabled": "0",
        "gst_percent": "18",
        "gst_type": "exclusive",
        "gstin": ""
    }
    
    for key, value in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    # Update business name and default Razorpay credentials in settings table
    cursor.execute("UPDATE settings SET value = 'MRUNMAYA ASSOCIATES' WHERE key = 'business_name'")
    cursor.execute("UPDATE settings SET value = 'rzp_live_TjiX5CotSd0Lrk' WHERE key = 'razorpay_key_id'")
    cursor.execute("UPDATE settings SET value = 'Z67kRRLfcjLXoHcAA1ndrs37' WHERE key = 'razorpay_key_secret'")
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'razorpay_enabled'")

    # Seed default Family Dandia Night 2026 event if not exists or update poster
    cursor.execute("SELECT COUNT(*) as cnt FROM events WHERE title LIKE '%Dandia%'")
    if cursor.fetchone()["cnt"] == 0:
        cursor.execute("""
        INSERT INTO events (title, poster_image, rate, dates, timings, venue, highlights, contacts, enabled, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            "Family Dandia Night 2026 - Melody Night Show",
            "dandia_night_2026.jpg",
            299,
            "17/10/2026 (Saturday) & 18/10/2026 (Sunday)",
            "7:00 PM TO 10:00 PM",
            "Trilochan Resorts, Sundarpada, Bhubaneswar (Near Champaty Petrol Pump)",
            "Unlimited Food | Unlimited Mocktails | Live Music & Singing | Lucky Draw (LED TV, Micro Oven, Induction)",
            "7008955582, 9938866544",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    else:
        cursor.execute("""
        UPDATE events SET 
            rate = 299,
            poster_image = 'dandia_night_2026.jpg',
            dates = '17/10/2026 (Saturday) & 18/10/2026 (Sunday)',
            timings = '7:00 PM TO 10:00 PM',
            venue = 'Trilochan Resorts, Sundarpada, Bhubaneswar (Near Champaty Petrol Pump)',
            highlights = 'Unlimited Food | Unlimited Mocktails | Live Music & Singing | Lucky Draw (LED TV, Micro Oven, Induction)',
            contacts = '7008955582, 9938866544'
        WHERE title LIKE '%Dandia%'
        """)

    # Migrate any existing tickets into payments table so admin ledger has complete history
    try:
        cursor.execute("SELECT * FROM tickets")
        existing_tickets = cursor.fetchall()
        for t in existing_tickets:
            p_id = t["razorpay_payment_id"] if t["razorpay_payment_id"] else f"TIC-{t['pass_id']}"
            cursor.execute("SELECT COUNT(*) as c FROM payments WHERE payment_id = ? OR pass_id = ?", (p_id, t["pass_id"]))
            if cursor.fetchone()["c"] == 0:
                mode = "Razorpay" if t["razorpay_payment_id"] else "Shop UPI QR Scanner"
                sub_m = "Online Gateway" if t["razorpay_payment_id"] else "UPI Barcode"
                cursor.execute("""
                INSERT OR IGNORE INTO payments (payment_id, order_id, service_type, customer_name, phone, amount, payment_mode, sub_method, transaction_ref, status, pass_id, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    p_id,
                    t["razorpay_order_id"] or "",
                    f"Event Ticket: {t['event_title']}",
                    t["customer_name"],
                    t["phone"],
                    t["total_amount"],
                    mode,
                    sub_m,
                    t["utr_reference"] or t["razorpay_payment_id"] or "Verified",
                    "Success",
                    t["pass_id"],
                    json.dumps({"quantity": t["quantity"], "date": t["date_selected"], "city": t["city"]}),
                    t["created_at"]
                ))
    except Exception as e:
        print(f"Ticket migration to payments notice: {e}")
        
    conn.commit()
    conn.close()

def save_lead(name: str, phone: str, service: str, specific_service: str = "", location: str = "", message: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO leads (name, phone, service, specific_service, location, message, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 'New', ?)
    """, (name.strip(), phone.strip(), service.strip(), specific_service.strip(), location.strip(), message.strip(), created_at))
    lead_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return lead_id, created_at

def get_all_leads(service_filter: str = None, status_filter: str = None, search: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM leads WHERE 1=1"
    params = []
    if service_filter and service_filter != "All":
        query += " AND service = ?"
        params.append(service_filter)
    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    if search:
        query += " AND (name LIKE ? OR phone LIKE ? OR location LIKE ? OR message LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    leads = [dict(row) for row in rows]
    conn.close()
    return leads

def update_lead_status(lead_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    conn.close()
    return True

def delete_lead(lead_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    return True

# Event Management
def get_all_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY id DESC")
    rows = cursor.fetchall()
    events = [dict(row) for row in rows]
    conn.close()
    return events

def save_event(title: str, rate: int, dates: str, timings: str, venue: str, highlights: str = "", contacts: str = "", poster_image: str = "", enabled: int = 1, event_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_poster = poster_image.strip() if (poster_image and poster_image.strip()) else "/static/dandia_night_2026.jpg"
    if event_id:
        cursor.execute("""
        UPDATE events SET title=?, rate=?, dates=?, timings=?, venue=?, highlights=?, contacts=?, poster_image=?, enabled=?
        WHERE id=?
        """, (title.strip(), rate, dates.strip(), timings.strip(), venue.strip(), highlights.strip(), contacts.strip(), clean_poster, enabled, event_id))
    else:
        cursor.execute("""
        INSERT INTO events (title, rate, dates, timings, venue, highlights, contacts, poster_image, enabled, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title.strip(), rate, dates.strip(), timings.strip(), venue.strip(), highlights.strip(), contacts.strip(), clean_poster, enabled, created_at))
        event_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return event_id

def delete_event(event_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    return True

# Ticket Management
def get_next_sequential_pass_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, pass_id FROM tickets")
    rows = cursor.fetchall()
    highest_num = 300  # Start pass sequence at 301
    existing_pass_ids = set()
    for row in rows:
        pid = row["pass_id"]
        if pid:
            existing_pass_ids.add(pid.strip().upper())
            m = re.search(r"/(\d+)$", pid.strip())
            if m:
                try:
                    num = int(m.group(1))
                    if num > highest_num:
                        highest_num = num
                except:
                    pass
            else:
                nums = re.findall(r"\d+", pid)
                if nums:
                    try:
                        num = int(nums[-1])
                        if num != 2026 and num > highest_num:
                            highest_num = num
                    except:
                        pass
    conn.close()

    if highest_num < 300:
        highest_num = 300

    next_seq = highest_num + 1
    official_pass_id = f"Dandia/2026/{next_seq:03d}"
    while official_pass_id.upper() in existing_pass_ids:
        next_seq += 1
        official_pass_id = f"Dandia/2026/{next_seq:03d}"

    return next_seq, official_pass_id, len(rows)

def save_ticket(pass_id: str = None, event_id: int = 1, event_title: str = "", customer_name: str = "", phone: str = "", quantity: int = 1, total_amount: int = 299, date_selected: str = "", email: str = "", city: str = "", rate_per_ticket: int = 299, utr_reference: str = "", payment_status: str = "Paid", razorpay_order_id: str = "", razorpay_payment_id: str = "", razorpay_signature: str = "", gst_amount: float = 0.0, gst_percent: float = 0.0):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Strictly Unique Sequential Pass ID - starting from Dandia/2026/301
    cursor.execute("SELECT id, pass_id FROM tickets")
    rows = cursor.fetchall()
    highest_num = 300  # Start sequence at 301
    existing_pass_ids = set()
    for row in rows:
        pid = row["pass_id"]
        if pid:
            existing_pass_ids.add(pid.strip().upper())
            m = re.search(r"/(\d+)$", pid.strip())
            if m:
                try:
                    num = int(m.group(1))
                    if num > highest_num:
                        highest_num = num
                except:
                    pass
            else:
                nums = re.findall(r"\d+", pid)
                if nums:
                    try:
                        num = int(nums[-1])
                        if num != 2026 and num > highest_num:
                            highest_num = num
                    except:
                        pass

    if highest_num < 300:
        highest_num = 300

    next_seq = highest_num + 1
    official_pass_id = f"Dandia/2026/{next_seq:03d}"
    while official_pass_id.upper() in existing_pass_ids:
        next_seq += 1
        official_pass_id = f"Dandia/2026/{next_seq:03d}"

    cursor.execute("""
    INSERT INTO tickets (pass_id, event_id, event_title, customer_name, phone, email, city, date_selected, quantity, rate_per_ticket, total_amount, payment_status, utr_reference, booking_status, razorpay_order_id, razorpay_payment_id, razorpay_signature, created_at, gst_amount, gst_percent)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?, ?, ?, ?, ?, ?)
    """, (official_pass_id, event_id, event_title.strip(), customer_name.strip(), phone.strip(), email.strip(), city.strip(), date_selected.strip(), quantity, rate_per_ticket, total_amount, payment_status, utr_reference.strip(), razorpay_order_id.strip(), razorpay_payment_id.strip(), razorpay_signature.strip(), created_at, gst_amount, gst_percent))
    ticket_id = cursor.lastrowid

    # Auto-record in payments transaction ledger
    try:
        p_mode = "Razorpay" if razorpay_payment_id else "Shop UPI QR Scanner"
        sub_m = "Online Gateway" if razorpay_payment_id else "UPI QR / Direct"
        pay_ref = razorpay_payment_id or utr_reference or f"PASS-{official_pass_id}"
        p_id = razorpay_payment_id if razorpay_payment_id else f"PAY-{official_pass_id.replace('/', '-')}"
        detail_dict = {
            "quantity": quantity,
            "date_selected": date_selected,
            "rate_per_ticket": rate_per_ticket,
            "city": city,
            "email": email
        }
        cursor.execute("""
        INSERT OR REPLACE INTO payments (payment_id, order_id, service_type, customer_name, phone, amount, payment_mode, sub_method, transaction_ref, status, pass_id, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Success', ?, ?, ?)
        """, (
            p_id,
            razorpay_order_id or "",
            f"Event Ticket: {event_title.strip()}",
            customer_name.strip(),
            phone.strip(),
            total_amount,
            p_mode,
            sub_m,
            pay_ref,
            official_pass_id,
            json.dumps(detail_dict),
            created_at
        ))
    except Exception as e:
        print(f"Error auto-recording ticket to payments: {e}")

    conn.commit()
    conn.close()
    return ticket_id, official_pass_id, created_at

def save_payment(service_type: str, customer_name: str, phone: str, amount: float, payment_mode: str = "Razorpay", sub_method: str = "UPI", transaction_ref: str = "", status: str = "Success", pass_id: str = "", details: dict = None, payment_id: str = None, order_id: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not payment_id:
        cursor.execute("SELECT id FROM payments ORDER BY id DESC LIMIT 1")
        last_row = cursor.fetchone()
        next_id = (last_row["id"] + 1) if last_row else 1
        payment_id = f"PAY-2026-{next_id:04d}"

    details_str = json.dumps(details) if isinstance(details, dict) else (str(details) if details else "")

    cursor.execute("""
    INSERT INTO payments (payment_id, order_id, service_type, customer_name, phone, amount, payment_mode, sub_method, transaction_ref, status, pass_id, details, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        payment_id,
        order_id or "",
        service_type.strip(),
        customer_name.strip(),
        phone.strip(),
        float(amount),
        payment_mode.strip(),
        sub_method.strip(),
        transaction_ref.strip(),
        status.strip(),
        pass_id.strip() if pass_id else None,
        details_str,
        created_at
    ))
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id, payment_id, created_at

def get_all_payments(search: str = None, status: str = None, mode: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM payments WHERE 1=1"
    params = []
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)
    if mode and mode != "All":
        query += " AND payment_mode LIKE ?"
        params.append(f"%{mode}%")
    if search:
        query += " AND (payment_id LIKE ? OR customer_name LIKE ? OR phone LIKE ? OR service_type LIKE ? OR transaction_ref LIKE ? OR pass_id LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term, term, term])
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    payments = [dict(row) for row in rows]
    conn.close()
    return payments

def get_all_tickets(search: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    if search:
        query += " AND (pass_id LIKE ? OR customer_name LIKE ? OR phone LIKE ? OR event_title LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    tickets = [dict(row) for row in rows]
    conn.close()
    return tickets

def update_ticket_status(ticket_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET booking_status = ? WHERE id = ?", (status, ticket_id))
    conn.commit()
    conn.close()
    return True

def get_ticket_by_pass_id(pass_id: str):
    clean = str(pass_id or "").strip()
    if not clean:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    # Match exact or case-insensitive or formatted Dandia/2026/XXX
    clean_formatted = f"Dandia/2026/{int(clean):03d}" if clean.isdigit() else clean
    cursor.execute("""
        SELECT * FROM tickets 
        WHERE LOWER(pass_id) = LOWER(?) 
           OR LOWER(pass_id) = LOWER(?)
           OR pass_id LIKE ? 
           OR id = ?
        ORDER BY id DESC LIMIT 1
    """, (clean, clean_formatted, f"%{clean}%", clean if clean.isdigit() else -1))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    settings = {row["key"]: row["value"] for row in rows}
    conn.close()
    return settings

def update_settings(updates: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    for key, value in updates.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()
    return True

def get_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM leads")
    total = cursor.fetchone()["total"]
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) as today FROM leads WHERE created_at LIKE ?", (f"{today_str}%",))
    today = cursor.fetchone()["today"]
    
    cursor.execute("SELECT service, COUNT(*) as count FROM leads GROUP BY service")
    by_service = {row["service"]: row["count"] for row in cursor.fetchall()}
    
    cursor.execute("SELECT status, COUNT(*) as count FROM leads GROUP BY status")
    by_status = {row["status"]: row["count"] for row in cursor.fetchall()}

    # Ticket statistics
    cursor.execute("SELECT COUNT(*) as total_tickets FROM tickets")
    total_tickets = cursor.fetchone()["total_tickets"]

    cursor.execute("SELECT SUM(quantity) as total_guests FROM tickets")
    total_guests = cursor.fetchone()["total_guests"] or 0

    cursor.execute("SELECT SUM(total_amount) as total_revenue FROM tickets")
    total_revenue = cursor.fetchone()["total_revenue"] or 0

    # Payments ledger statistics
    cursor.execute("SELECT COUNT(*) as total_payments FROM payments")
    total_payments = cursor.fetchone()["total_payments"]

    cursor.execute("SELECT SUM(amount) as payments_revenue FROM payments")
    payments_revenue = cursor.fetchone()["payments_revenue"] or 0

    cursor.execute("SELECT COUNT(*) as today_payments FROM payments WHERE created_at LIKE ?", (f"{today_str}%",))
    today_payments = cursor.fetchone()["today_payments"]

    cursor.execute("SELECT COUNT(*) as total_admitted FROM tickets WHERE LOWER(booking_status) = 'admitted'")
    total_admitted = cursor.fetchone()["total_admitted"]

    cursor.execute("SELECT payment_mode, COUNT(*) as cnt, SUM(amount) as total FROM payments GROUP BY payment_mode")
    by_payment_mode = {row["payment_mode"]: {"count": row["cnt"], "total": row["total"]} for row in cursor.fetchall()}
    
    conn.close()
    return {
        "total": total,
        "today": today,
        "by_service": by_service,
        "by_status": by_status,
        "total_tickets": total_tickets,
        "total_guests": total_guests,
        "total_revenue": total_revenue,
        "total_admitted": total_admitted,
        "total_payments": total_payments,
        "payments_revenue": payments_revenue,
        "today_payments": today_payments,
        "by_payment_mode": by_payment_mode
    }
