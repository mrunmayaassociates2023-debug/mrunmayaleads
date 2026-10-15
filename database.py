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

    # Create sponsors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sponsors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'Event Partner',
        logo_url TEXT,
        website_url TEXT,
        display_order INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
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
    if "cancelled_at" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN cancelled_at TEXT")
    if "is_deleted" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN is_deleted INTEGER DEFAULT 0")
    if "deleted_at" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN deleted_at TEXT")
    if "is_vip" not in ticket_cols:
        cursor.execute("ALTER TABLE tickets ADD COLUMN is_vip INTEGER DEFAULT 0")

    # Ensure phone and email exist in sponsors table
    cursor.execute("PRAGMA table_info(sponsors)")
    sponsor_cols = [col["name"] for col in cursor.fetchall()]
    if "phone" not in sponsor_cols:
        cursor.execute("ALTER TABLE sponsors ADD COLUMN phone TEXT")
    if "email" not in sponsor_cols:
        cursor.execute("ALTER TABLE sponsors ADD COLUMN email TEXT")
    
    # Insert default settings if not exists
    default_settings = {
        "owner_phone": "919938866544",
        "business_name": "MRUNMAYA ASSOCIATES",
        "tagline": "Citizen Services, Event Tickets & Digital Solutions",
        "address": "Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002",
        "email": "mrunmay.service@gmail.com",
        "admin_pin": "9906",
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
        "gstin": "",
        "booking_status": "open",
        "booking_close_date": "2026-10-16T23:59",
        "booking_close_message": "Online ticket booking is officially closed for Family Dandia Night 2026. For VIP / gate passes, please contact organizer."
    }
    
    for key, value in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    # Update business name, contacts, email, address and default Razorpay credentials in settings table
    cursor.execute("UPDATE settings SET value = 'MRUNMAYA ASSOCIATES' WHERE key = 'business_name'")
    cursor.execute("UPDATE settings SET value = '917992993433' WHERE key = 'owner_phone'")
    cursor.execute("UPDATE settings SET value = 'mrunmayaassoxiates2023@gmail.com' WHERE key = 'email'")
    cursor.execute("UPDATE settings SET value = 'Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002' WHERE key = 'address'")
    cursor.execute("UPDATE settings SET value = 'rzp_live_TjiX5CotSd0Lrk' WHERE key = 'razorpay_key_id'")
    cursor.execute("UPDATE settings SET value = 'Z67kRRLfcjLXoHcAA1ndrs37' WHERE key = 'razorpay_key_secret'")
    cursor.execute("UPDATE settings SET value = '1' WHERE key = 'razorpay_enabled'")

    # Create persistent tombstone table for permanent deletions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deleted_items (
        item_type TEXT NOT NULL,
        item_id TEXT NOT NULL,
        deleted_at TEXT NOT NULL,
        PRIMARY KEY (item_type, item_id)
    )
    """)

    # Check if initial seeding has already been completed once
    cursor.execute("SELECT value FROM settings WHERE key = 'app_init_done'")
    init_done_row = cursor.fetchone()

    if not init_done_row:
        # Seed default Family Dandia Night 2026 event on initial fresh setup only
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
                "Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002",
                "Unlimited Food | Unlimited Mocktails | Live Music & Singing | Lucky Draw (LED TV, Micro Oven, Induction)",
                "7992993433, 7008955582",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        # Seed default sponsors on initial fresh setup only
        cursor.execute("SELECT COUNT(*) as cnt FROM sponsors")
        if cursor.fetchone()["cnt"] == 0:
            default_sponsors = [
                ("Trilochan Resorts", "Venue Partner", "/static/dandia_night_2026.jpg", "https://maps.google.com/?q=Trilochan+Resorts+Trilochan+Vihar+Sundarpada+Ebaranga+Jatni+Road+Bhubaneswar+751002", 1),
                ("Mrunmaya Associates", "Organizing & Ticketing Desk", "/static/logo.png", "https://mrunmayaleads.onrender.com/", 2),
                ("Odisha Live Beats", "Live Sound & Entertainment Partner", "", "", 3)
            ]
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for s_name, s_cat, s_logo, s_web, s_order in default_sponsors:
                cursor.execute("""
                INSERT INTO sponsors (name, category, logo_url, website_url, display_order, enabled, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """, (s_name, s_cat, s_logo, s_web, s_order, now_str))

        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('app_init_done', '1')")

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
    try:
        sync_supabase_pull_tickets_and_payments(force=True)
    except Exception:
        pass

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

def record_deleted_item(item_type: str, item_id: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deleted_items (
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            deleted_at TEXT NOT NULL,
            PRIMARY KEY (item_type, item_id)
        )
        """)
        cursor.execute("INSERT OR REPLACE INTO deleted_items (item_type, item_id, deleted_at) VALUES (?, ?, ?)", (item_type, str(item_id).strip(), now_str))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Notice recording deleted item: {e}")

def is_item_deleted(item_type: str, item_id: str) -> bool:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deleted_items (
            item_type TEXT NOT NULL,
            item_id TEXT NOT NULL,
            deleted_at TEXT NOT NULL,
            PRIMARY KEY (item_type, item_id)
        )
        """)
        clean = str(item_id).strip()
        cursor.execute("SELECT 1 FROM deleted_items WHERE item_type = ? AND (item_id = ? OR LOWER(item_id) = LOWER(?))", (item_type, clean, clean))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception:
        return False

def delete_event(event_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()
    record_deleted_item("event", str(event_id))
    sync_supabase_delete("events", "id", str(event_id))
    return True

_last_sponsors_sync = 0

def sync_supabase_pull_sponsors(force: bool = False):
    global _last_sponsors_sync
    import time
    import urllib.request
    import json
    
    now = time.time()
    if not force and (now - _last_sponsors_sync < 5):
        return
    _last_sponsors_sync = now

    sb_url = "https://ivhjhyjrbeodwsugpjxq.supabase.co"
    sb_key = "sb_publishable_AfBcq6xJZM0YI_6dHOsyqQ__J16HqDn"
    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}"
    }

    try:
        req = urllib.request.Request(f"{sb_url}/rest/v1/sponsors?select=*&order=id.asc", headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            cloud_sponsors = json.loads(resp.read().decode())
            
        if not isinstance(cloud_sponsors, list) or len(cloud_sponsors) == 0:
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(sponsors)")
        cols = [c["name"] for c in cursor.fetchall()]
        if "phone" not in cols:
            cursor.execute("ALTER TABLE sponsors ADD COLUMN phone TEXT")
        if "email" not in cols:
            cursor.execute("ALTER TABLE sponsors ADD COLUMN email TEXT")

        for s in cloud_sponsors:
            s_id = s.get("id")
            s_name = s.get("name")
            if not s_id or not s_name:
                continue

            # If sponsor was permanently deleted by admin, purge from Supabase and skip insertion!
            if is_item_deleted("sponsor", str(s_id)):
                sync_supabase_delete("sponsors", "id", str(s_id))
                continue

            s_cat = s.get("category") or "Event Partner"
            s_logo = s.get("logo_url") or ""
            s_web = s.get("website_url") or ""
            s_phone = s.get("phone") or ""
            s_email = s.get("email") or ""
            s_order = s.get("display_order", 1)
            s_enabled = s.get("enabled", 1)
            s_created = s.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("SELECT id FROM sponsors WHERE id = ?", (s_id,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE sponsors SET
                        name = ?, category = ?, logo_url = ?, website_url = ?,
                        phone = ?, email = ?, display_order = ?, enabled = ?
                    WHERE id = ?
                """, (s_name, s_cat, s_logo, s_web, s_phone, s_email, s_order, s_enabled, s_id))
            else:
                cursor.execute("""
                    INSERT INTO sponsors (id, name, category, logo_url, website_url, phone, email, display_order, enabled, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (s_id, s_name, s_cat, s_logo, s_web, s_phone, s_email, s_order, s_enabled, s_created))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Supabase sponsor pull note: {e}")

# Sponsorship Management
def get_all_sponsors(enabled_only=False):
    try:
        sync_supabase_pull_sponsors()
    except Exception:
        pass
    conn = get_db_connection()
    cursor = conn.cursor()
    if enabled_only:
        cursor.execute("SELECT * FROM sponsors WHERE enabled = 1 ORDER BY display_order ASC, id ASC")
    else:
        cursor.execute("SELECT * FROM sponsors ORDER BY display_order ASC, id ASC")
    rows = cursor.fetchall()
    sponsors = [dict(row) for row in rows]
    conn.close()
    return sponsors

def save_sponsor(name: str, category: str = "Event Partner", logo_url: str = "", website_url: str = "", phone: str = "", email: str = "", display_order: int = 1, enabled: int = 1, sponsor_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_logo = logo_url.strip() if logo_url else ""
    clean_web = website_url.strip() if website_url else ""
    clean_name = name.strip()
    clean_cat = category.strip() if category else "Event Partner"
    clean_phone = phone.strip() if phone else ""
    clean_email = email.strip() if email else ""
    
    if not sponsor_id:
        import time
        sponsor_id = int(time.time() * 1000)
    
    cursor.execute("SELECT id FROM sponsors WHERE id = ?", (sponsor_id,))
    if cursor.fetchone():
        cursor.execute("""
        UPDATE sponsors SET name=?, category=?, logo_url=?, website_url=?, phone=?, email=?, display_order=?, enabled=?
        WHERE id=?
        """, (clean_name, clean_cat, clean_logo, clean_web, clean_phone, clean_email, display_order, enabled, sponsor_id))
    else:
        cursor.execute("""
        INSERT INTO sponsors (id, name, category, logo_url, website_url, phone, email, display_order, enabled, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (sponsor_id, clean_name, clean_cat, clean_logo, clean_web, clean_phone, clean_email, display_order, enabled, created_at))
    conn.commit()
    conn.close()

    # Cloud Persistence: Sync to Supabase
    try:
        sync_supabase_upsert("sponsors", {
            "id": sponsor_id,
            "name": clean_name,
            "category": clean_cat,
            "logo_url": clean_logo,
            "website_url": clean_web,
            "phone": clean_phone,
            "email": clean_email,
            "display_order": display_order,
            "enabled": enabled,
            "created_at": created_at
        })
    except Exception as e_sb:
        print(f"Supabase sponsor upsert notice: {e_sb}")

    return sponsor_id

def sync_supabase_delete(table: str, column: str, value: str):
    import urllib.request
    import urllib.parse
    sb_url = "https://ivhjhyjrbeodwsugpjxq.supabase.co"
    sb_key = "sb_publishable_AfBcq6xJZM0YI_6dHOsyqQ__J16HqDn"
    clean_val = urllib.parse.quote(str(value).strip(), safe="")
    url = f"{sb_url}/rest/v1/{table}?{column}=eq.{clean_val}"
    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="DELETE")
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        pass

def sync_supabase_upsert(table: str, row_data: dict):
    import urllib.request
    import json
    sb_url = "https://ivhjhyjrbeodwsugpjxq.supabase.co"
    sb_key = "sb_publishable_AfBcq6xJZM0YI_6dHOsyqQ__J16HqDn"
    url = f"{sb_url}/rest/v1/{table}"
    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    try:
        body = json.dumps([row_data]).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        pass

_last_supabase_sync = 0

def sync_supabase_pull_tickets_and_payments(force: bool = False):
    global _last_supabase_sync
    import time
    import urllib.request
    import json
    
    now = time.time()
    if not force and (now - _last_supabase_sync < 10):
        return
    _last_supabase_sync = now

    sb_url = "https://ivhjhyjrbeodwsugpjxq.supabase.co"
    sb_key = "sb_publishable_AfBcq6xJZM0YI_6dHOsyqQ__J16HqDn"
    headers = {
        "apikey": sb_key,
        "Authorization": f"Bearer {sb_key}"
    }

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Pull tickets
        try:
            req = urllib.request.Request(f"{sb_url}/rest/v1/tickets?select=*&order=id.asc", headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                cloud_tickets = json.loads(resp.read().decode())
                for t in cloud_tickets:
                    pid = t.get("pass_id")
                    if not pid:
                        continue
                    
                    # If ticket was permanently deleted by admin, purge from Supabase and skip!
                    if is_item_deleted("ticket", pid) or is_item_deleted("ticket", str(t.get("id"))):
                        sync_supabase_delete("tickets", "pass_id", pid)
                        continue

                    p_status = str(t.get("payment_status") or "Paid")
                    u_ref = str(t.get("utr_reference") or "")
                    is_vip_val = 1 if ("vip" in p_status.lower() or "vip" in u_ref.lower() or "vip" in pid.lower() or t.get("is_vip") == 1) else 0

                    cursor.execute("SELECT id FROM tickets WHERE pass_id = ? OR LOWER(pass_id) = LOWER(?)", (pid, pid))
                    existing = cursor.fetchone()
                    if existing:
                        cursor.execute("""
                            UPDATE tickets SET
                                event_id = ?, event_title = ?, customer_name = ?, phone = ?, email = ?,
                                city = ?, date_selected = ?, quantity = ?, rate_per_ticket = ?, total_amount = ?,
                                payment_status = ?, utr_reference = ?, booking_status = ?,
                                razorpay_order_id = ?, razorpay_payment_id = ?, is_vip = ?, created_at = ?
                            WHERE id = ?
                        """, (
                            t.get("event_id", 1), t.get("event_title", ""), t.get("customer_name", ""), t.get("phone", ""), t.get("email", ""),
                            t.get("city", ""), t.get("date_selected", ""), t.get("quantity", 1), t.get("rate_per_ticket", 299), t.get("total_amount", 299),
                            p_status, u_ref, t.get("booking_status", "Confirmed"),
                            t.get("razorpay_order_id", ""), t.get("razorpay_payment_id", ""), is_vip_val, t.get("created_at", ""),
                            existing["id"]
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO tickets (
                                pass_id, event_id, event_title, customer_name, phone, email,
                                city, date_selected, quantity, rate_per_ticket, total_amount,
                                payment_status, utr_reference, booking_status,
                                razorpay_order_id, razorpay_payment_id, is_vip, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            pid, t.get("event_id", 1), t.get("event_title", ""), t.get("customer_name", ""), t.get("phone", ""), t.get("email", ""),
                            t.get("city", ""), t.get("date_selected", ""), t.get("quantity", 1), t.get("rate_per_ticket", 299), t.get("total_amount", 299),
                            p_status, u_ref, t.get("booking_status", "Confirmed"),
                            t.get("razorpay_order_id", ""), t.get("razorpay_payment_id", ""), is_vip_val, t.get("created_at", "")
                        ))
        except Exception as e_t:
            pass

        # 2. Pull payments
        try:
            req_p = urllib.request.Request(f"{sb_url}/rest/v1/payments?select=*&order=id.asc", headers=headers)
            with urllib.request.urlopen(req_p, timeout=5) as resp_p:
                cloud_payments = json.loads(resp_p.read().decode())
                for p in cloud_payments:
                    pay_id = p.get("payment_id")
                    if not pay_id:
                        continue
                    
                    p_pass = p.get("pass_id") or ""
                    # If payment or its linked ticket was deleted, purge from Supabase and skip!
                    if is_item_deleted("payment", pay_id) or (p_pass and is_item_deleted("ticket", p_pass)):
                        sync_supabase_delete("payments", "payment_id", pay_id)
                        continue

                    cursor.execute("SELECT id FROM payments WHERE payment_id = ?", (pay_id,))
                    existing_p = cursor.fetchone()
                    if existing_p:
                        cursor.execute("""
                            UPDATE payments SET
                                order_id = ?, service_type = ?, customer_name = ?, phone = ?,
                                amount = ?, payment_mode = ?, status = ?, pass_id = ?, created_at = ?
                            WHERE id = ?
                        """, (
                            p.get("order_id", ""), p.get("service_type", ""), p.get("customer_name", ""), p.get("phone", ""),
                            p.get("amount", 0.0), p.get("payment_mode", ""), p.get("status", "Success"), p.get("pass_id", ""),
                            p.get("created_at", ""), existing_p["id"]
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO payments (
                                payment_id, order_id, service_type, customer_name, phone,
                                amount, payment_mode, status, pass_id, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            pay_id, p.get("order_id", ""), p.get("service_type", ""), p.get("customer_name", ""), p.get("phone", ""),
                            p.get("amount", 0.0), p.get("payment_mode", ""), p.get("status", "Success"), p.get("pass_id", ""),
                            p.get("created_at", "")
                        ))
        except Exception as e_p:
            pass

        conn.commit()
        conn.close()
    except Exception as e_outer:
        pass

def delete_sponsor(sponsor_id: int):
    record_deleted_item("sponsor", str(sponsor_id))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sponsors WHERE id = ?", (sponsor_id,))
    conn.commit()
    conn.close()
    sync_supabase_delete("sponsors", "id", str(sponsor_id))
    return True

def toggle_sponsor_status(sponsor_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE sponsors SET enabled = CASE WHEN enabled = 1 THEN 0 ELSE 1 END WHERE id = ?", (sponsor_id,))
    cursor.execute("SELECT enabled FROM sponsors WHERE id = ?", (sponsor_id,))
    row = cursor.fetchone()
    new_state = row["enabled"] if row else 1
    conn.commit()
    conn.close()
    try:
        import urllib.request, json
        sb_url = "https://ivhjhyjrbeodwsugpjxq.supabase.co"
        sb_key = "sb_publishable_AfBcq6xJZM0YI_6dHOsyqQ__J16HqDn"
        url = f"{sb_url}/rest/v1/sponsors?id=eq.{sponsor_id}"
        headers = {
            "apikey": sb_key,
            "Authorization": f"Bearer {sb_key}",
            "Content-Type": "application/json"
        }
        body = json.dumps({"enabled": new_state}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass
    return True

# Ticket Management
def get_next_sequential_pass_info():
    try:
        sync_supabase_pull_tickets_and_payments(force=True)
    except Exception:
        pass

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
            for num_str in re.findall(r"\d+", pid):
                try:
                    num = int(num_str)
                    if num != 2026 and num > highest_num:
                        highest_num = num
                except:
                    pass

    # Also check payments table (handles multi-pass strings e.g. "Dandia/2026/310, Dandia/2026/311")
    cursor.execute("SELECT pass_id FROM payments WHERE pass_id IS NOT NULL AND pass_id != ''")
    for r in cursor.fetchall():
        raw_passes = r["pass_id"]
        if raw_passes:
            for p_part in str(raw_passes).split(","):
                clean_p = p_part.strip().upper()
                if clean_p:
                    existing_pass_ids.add(clean_p)
                    for num_str in re.findall(r"\d+", clean_p):
                        try:
                            num = int(num_str)
                            if num != 2026 and num > highest_num:
                                highest_num = num
                        except:
                            pass
                        
    # Check deleted_pass_ids tombstone table
    cursor.execute("CREATE TABLE IF NOT EXISTS deleted_pass_ids (pass_id TEXT PRIMARY KEY, deleted_at TEXT NOT NULL)")
    cursor.execute("SELECT pass_id FROM deleted_pass_ids")
    for r in cursor.fetchall():
        pid = r["pass_id"]
        if pid:
            existing_pass_ids.add(pid.strip().upper())
            for num_str in re.findall(r"\d+", pid):
                try:
                    num = int(num_str)
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
    try:
        sync_supabase_pull_tickets_and_payments(force=True)
    except Exception:
        pass

    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Strictly Unique Sequential Pass IDs - starting from Dandia/2026/301
    cursor.execute("SELECT pass_id FROM tickets")
    rows = cursor.fetchall()
    highest_num = 300  # Start sequence at 301
    existing_pass_ids = set()
    for row in rows:
        pid = row["pass_id"]
        if pid:
            existing_pass_ids.add(pid.strip().upper())
            for num_str in re.findall(r"\d+", pid):
                try:
                    num = int(num_str)
                    if num != 2026 and num > highest_num:
                        highest_num = num
                except:
                    pass

    cursor.execute("SELECT pass_id FROM payments WHERE pass_id IS NOT NULL AND pass_id != ''")
    for r in cursor.fetchall():
        raw_passes = r["pass_id"]
        if raw_passes:
            for p_part in str(raw_passes).split(","):
                clean_p = p_part.strip().upper()
                if clean_p:
                    existing_pass_ids.add(clean_p)
                    for num_str in re.findall(r"\d+", clean_p):
                        try:
                            num = int(num_str)
                            if num != 2026 and num > highest_num:
                                highest_num = num
                        except:
                            pass

    # Include deleted_pass_ids to never re-allocate an old deleted pass ID
    cursor.execute("CREATE TABLE IF NOT EXISTS deleted_pass_ids (pass_id TEXT PRIMARY KEY, deleted_at TEXT NOT NULL)")
    cursor.execute("SELECT pass_id FROM deleted_pass_ids")
    for r in cursor.fetchall():
        pid = r["pass_id"]
        if pid:
            existing_pass_ids.add(pid.strip().upper())
            for num_str in re.findall(r"\d+", pid):
                try:
                    num = int(num_str)
                    if num != 2026 and num > highest_num:
                        highest_num = num
                except:
                    pass

    if highest_num < 300:
        highest_num = 300

    qty = max(1, int(quantity or 1))
    allocated_pass_ids = []

    if pass_id and pass_id.strip() and pass_id.strip().upper() not in existing_pass_ids:
        allocated_pass_ids.append(pass_id.strip())
        existing_pass_ids.add(pass_id.strip().upper())
        curr_seq = highest_num + 1
        for _ in range(qty - 1):
            candidate = f"Dandia/2026/{curr_seq:03d}"
            while candidate.upper() in existing_pass_ids:
                curr_seq += 1
                candidate = f"Dandia/2026/{curr_seq:03d}"
            allocated_pass_ids.append(candidate)
            existing_pass_ids.add(candidate.upper())
            curr_seq += 1
    else:
        curr_seq = highest_num + 1
        for _ in range(qty):
            candidate = f"Dandia/2026/{curr_seq:03d}"
            while candidate.upper() in existing_pass_ids:
                curr_seq += 1
                candidate = f"Dandia/2026/{curr_seq:03d}"
            allocated_pass_ids.append(candidate)
            existing_pass_ids.add(candidate.upper())
            curr_seq += 1

    first_ticket_id = None
    all_ticket_ids = []

    # Calculate fair share per ticket
    per_ticket_amt = int(round(total_amount / qty)) if qty > 1 else total_amount
    per_ticket_gst = round(gst_amount / qty, 2) if (gst_amount and qty > 1) else gst_amount
    primary_pass = allocated_pass_ids[0]
    passes_display = ", ".join(allocated_pass_ids)

    # Check VIP classification
    is_vip = 1 if ("vip" in str(payment_status).lower() or "vip" in str(utr_reference).lower() or (pass_id and "vip" in str(pass_id).lower()) or (total_amount == 0 and "complimentary" in str(payment_status).lower())) else 0

    # Insert individual record for each pass so each guest gets an individual lucky draw ticket
    for idx, pid in enumerate(allocated_pass_ids):
        c_name = customer_name.strip()
        ref_text = utr_reference.strip()
        if qty > 1:
            ref_text = f"{ref_text} [Pass {idx+1}/{qty}]" if ref_text else f"Pass {idx+1}/{qty}"

        cursor.execute("""
        INSERT INTO tickets (pass_id, event_id, event_title, customer_name, phone, email, city, date_selected, quantity, rate_per_ticket, total_amount, payment_status, utr_reference, booking_status, razorpay_order_id, razorpay_payment_id, razorpay_signature, created_at, gst_amount, gst_percent, is_vip)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, 'Confirmed', ?, ?, ?, ?, ?, ?, ?)
        """, (pid, event_id, event_title.strip(), c_name, phone.strip(), email.strip(), city.strip(), date_selected.strip(), rate_per_ticket, per_ticket_amt, payment_status, ref_text, razorpay_order_id.strip(), razorpay_payment_id.strip(), razorpay_signature.strip(), created_at, per_ticket_gst, gst_percent, is_vip))
        
        row_id = cursor.lastrowid
        all_ticket_ids.append(row_id)
        if first_ticket_id is None:
            first_ticket_id = row_id

    # Auto-record in payments transaction ledger (1 ledger row for the transaction)
    p_id = ""
    try:
        p_mode = "VIP / Complimentary" if is_vip else ("Razorpay" if razorpay_payment_id else "Shop UPI QR Scanner")
        sub_m = "VIP Desk" if is_vip else ("Online Gateway" if razorpay_payment_id else "UPI QR / Direct")
        pay_ref = razorpay_payment_id or utr_reference or f"PASS-{primary_pass}"
        p_id = razorpay_payment_id if razorpay_payment_id else f"PAY-{primary_pass.replace('/', '-')}"
        detail_dict = {
            "quantity": qty,
            "pass_ids": allocated_pass_ids,
            "date_selected": date_selected,
            "rate_per_ticket": rate_per_ticket,
            "city": city,
            "email": email,
            "is_vip": is_vip
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
            passes_display if qty > 1 else primary_pass,
            json.dumps(detail_dict),
            created_at
        ))
    except Exception as e:
        print(f"Error auto-recording ticket to payments: {e}")

    conn.commit()
    conn.close()

    # Sync all generated individual passes to Supabase Cloud
    for pid in allocated_pass_ids:
        sync_supabase_upsert("tickets", {
            "pass_id": pid,
            "event_id": event_id,
            "event_title": event_title.strip(),
            "customer_name": customer_name.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
            "city": city.strip(),
            "date_selected": date_selected.strip(),
            "quantity": 1,
            "rate_per_ticket": rate_per_ticket,
            "total_amount": per_ticket_amt,
            "payment_status": payment_status,
            "utr_reference": f"Razorpay [{pid}]" if razorpay_payment_id else (utr_reference or "Paid"),
            "booking_status": "Confirmed",
            "razorpay_order_id": razorpay_order_id.strip(),
            "razorpay_payment_id": razorpay_payment_id.strip(),
            "is_vip": is_vip,
            "created_at": created_at
        })

    # Also sync payment transaction to Supabase Cloud
    if p_id:
        try:
            sync_supabase_upsert("payments", {
                "payment_id": p_id,
                "order_id": razorpay_order_id or "",
                "service_type": f"Event Ticket: {event_title.strip()}",
                "customer_name": customer_name.strip(),
                "phone": phone.strip(),
                "amount": total_amount,
                "payment_mode": "VIP / Complimentary" if is_vip else ("Razorpay" if razorpay_payment_id else "Cash / Counter"),
                "status": "Success",
                "pass_id": passes_display if qty > 1 else primary_pass,
                "created_at": created_at
            })
        except Exception:
            pass

    return first_ticket_id, primary_pass, created_at, allocated_pass_ids

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

def purge_expired_cancelled_tickets():
    """Delete tickets that were cancelled more than 24 hours ago (auto-cleanup)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        DELETE FROM tickets 
        WHERE booking_status = 'Cancelled' 
          AND cancelled_at IS NOT NULL 
          AND datetime(cancelled_at) <= datetime('now', '-24 hours')
        """)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"Purge cancelled tickets notice: {e}")
        return 0

def auto_backup_tickets():
    """Auto-backs up all tickets to tickets_backup_archive.json and jsonl"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets ORDER BY id ASC")
        rows = cursor.fetchall()
        all_data = [dict(r) for r in rows]
        conn.close()
        
        backup_path = os.path.join(os.path.dirname(__file__), "tickets_backup_archive.json")
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
            
        backup_jsonl = os.path.join(os.path.dirname(__file__), "tickets_backup_archive.jsonl")
        with open(backup_jsonl, "w", encoding="utf-8") as f:
            for item in all_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"Auto-backup tickets warning: {e}")
        return False

def get_all_tickets(search: str = None, include_deleted: bool = False):
    try:
        sync_supabase_pull_tickets_and_payments(force=False)
    except Exception:
        pass
    # Automatically purge tickets cancelled more than 24 hours ago
    purge_expired_cancelled_tickets()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Ensure tombstone table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deleted_pass_ids (
        pass_id TEXT PRIMARY KEY,
        deleted_at TEXT NOT NULL
    )
    """)
    
    conds = []
    params = []
    if not include_deleted:
        conds.append("(is_deleted = 0 OR is_deleted IS NULL)")
        conds.append("pass_id NOT IN (SELECT pass_id FROM deleted_pass_ids)")
        
    if search:
        conds.append("(pass_id LIKE ? OR customer_name LIKE ? OR phone LIKE ? OR event_title LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term, term])
        
    where_clause = ("WHERE " + " AND ".join(conds)) if conds else ""
    query = f"SELECT * FROM tickets {where_clause} ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    tickets = [dict(row) for row in rows]
    conn.close()
    return tickets

def get_recycle_bin_tickets():
    """Retrieve all tickets currently stored in the Recycle Bin"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE is_deleted = 1 ORDER BY deleted_at DESC, id DESC")
    rows = cursor.fetchall()
    tickets = [dict(row) for row in rows]
    conn.close()
    return tickets

def update_ticket_status(ticket_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status.lower() == "cancelled":
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE tickets SET booking_status = ?, cancelled_at = ? WHERE id = ?", (status, now_str, ticket_id))
    else:
        cursor.execute("UPDATE tickets SET booking_status = ?, cancelled_at = NULL WHERE id = ?", (status, ticket_id))
    conn.commit()
    conn.close()
    auto_backup_tickets()
    return True

def update_ticket_details(ticket_identifier, updates: dict):
    """
    Allow Admin to edit ticket details (date, name, phone, email, city, amount, qty, VIP, payment status, etc.)
    Syncs changes to SQLite and Supabase Cloud.
    """
    clean_id = str(ticket_identifier).strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM tickets 
        WHERE id = ? 
           OR pass_id = ? 
           OR LOWER(pass_id) = LOWER(?)
    """, (int(clean_id) if clean_id.isdigit() else -1, clean_id, clean_id))
    ticket = cursor.fetchone()
    if not ticket and ("dandia" in clean_id.lower() or "/" in clean_id):
        cursor.execute("SELECT * FROM tickets WHERE pass_id = ? OR LOWER(pass_id) = LOWER(?)", (clean_id, clean_id))
        ticket = cursor.fetchone()
        
    if not ticket:
        conn.close()
        return False, "Ticket not found"
        
    tid = ticket["id"]
    current_pass_id = ticket["pass_id"]
    
    allowed_fields = [
        "date_selected", "customer_name", "phone", "email", "city",
        "quantity", "rate_per_ticket", "total_amount", "payment_status",
        "utr_reference", "booking_status", "is_vip", "event_title",
        "razorpay_payment_id"
    ]
    
    set_clauses = []
    params = []
    
    for f in allowed_fields:
        if f in updates and updates[f] is not None:
            val = updates[f]
            if f in ("quantity", "rate_per_ticket", "total_amount"):
                try:
                    val = int(round(float(val)))
                except:
                    pass
            elif f == "is_vip":
                val = 1 if str(val).lower() in ("1", "true", "yes", "vip") else 0
            elif isinstance(val, str):
                val = val.strip()
            set_clauses.append(f"{f} = ?")
            params.append(val)
            
    if not set_clauses:
        conn.close()
        return False, "No valid fields provided to update"
        
    params.append(tid)
    cursor.execute(f"UPDATE tickets SET {', '.join(set_clauses)} WHERE id = ?", params)
    
    # Also update corresponding payment record if customer_name, phone, or amount changed
    update_pay_clauses = []
    pay_params = []
    if "customer_name" in updates:
        update_pay_clauses.append("customer_name = ?")
        pay_params.append(str(updates["customer_name"]).strip())
    if "phone" in updates:
        update_pay_clauses.append("phone = ?")
        pay_params.append(str(updates["phone"]).strip())
    if "total_amount" in updates:
        try:
            update_pay_clauses.append("amount = ?")
            pay_params.append(float(updates["total_amount"]))
        except:
            pass
    if update_pay_clauses:
        pay_params.append(current_pass_id)
        cursor.execute(f"UPDATE payments SET {', '.join(update_pay_clauses)} WHERE pass_id = ? OR pass_id LIKE ?", pay_params + [f"%{current_pass_id}%"])
        
    conn.commit()
    
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (tid,))
    updated_ticket = dict(cursor.fetchone())
    conn.close()
    
    # Sync update to Supabase Cloud
    try:
        sync_supabase_upsert("tickets", {
            "pass_id": updated_ticket.get("pass_id"),
            "event_id": updated_ticket.get("event_id", 1),
            "event_title": updated_ticket.get("event_title", ""),
            "customer_name": updated_ticket.get("customer_name", ""),
            "phone": updated_ticket.get("phone", ""),
            "email": updated_ticket.get("email", ""),
            "city": updated_ticket.get("city", ""),
            "date_selected": updated_ticket.get("date_selected", ""),
            "quantity": updated_ticket.get("quantity", 1),
            "rate_per_ticket": updated_ticket.get("rate_per_ticket", 299),
            "total_amount": updated_ticket.get("total_amount", 299),
            "payment_status": updated_ticket.get("payment_status", "Paid"),
            "utr_reference": updated_ticket.get("utr_reference", ""),
            "booking_status": updated_ticket.get("booking_status", "Confirmed"),
            "razorpay_order_id": updated_ticket.get("razorpay_order_id", ""),
            "razorpay_payment_id": updated_ticket.get("razorpay_payment_id", ""),
            "is_vip": updated_ticket.get("is_vip", 0),
            "created_at": updated_ticket.get("created_at", "")
        })
    except Exception as e_sb:
        print(f"Supabase update sync note: {e_sb}")
        
    auto_backup_tickets()
    return True, updated_ticket

def delete_ticket(ticket_identifier, permanent: bool = True):
    """
    If permanent=True: Completely purges ticket from DB, payments, deleted_items tombstone, and Supabase.
    If permanent=False: Moves ticket to Recycle Bin (Trash) with deleted_at timestamp.
    """
    clean_id = str(ticket_identifier).strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        SELECT id, pass_id FROM tickets 
        WHERE id = ? 
           OR pass_id = ? 
           OR LOWER(pass_id) = LOWER(?)
    """, (int(clean_id) if clean_id.isdigit() else -1, clean_id, clean_id))
    rows = cursor.fetchall()

    if not rows and ("dandia" in clean_id.lower() or "/" in clean_id):
        cursor.execute("SELECT id, pass_id FROM tickets WHERE pass_id = ? OR LOWER(pass_id) = LOWER(?)", (clean_id, clean_id))
        rows = cursor.fetchall()

    if not permanent:
        # Move to Recycle Bin (soft delete)
        for r in rows:
            cursor.execute("UPDATE tickets SET is_deleted = 1, deleted_at = ? WHERE id = ?", (now_str, r["id"]))
            if r["pass_id"]:
                record_deleted_item("ticket", r["pass_id"])
            record_deleted_item("ticket", str(r["id"]))
        conn.commit()
        conn.close()
        auto_backup_tickets()
        return True

    # Permanent delete
    deleted_passes = set()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deleted_pass_ids (
        pass_id TEXT PRIMARY KEY,
        deleted_at TEXT NOT NULL
    )
    """)
    for r in rows:
        pid = r["pass_id"]
        if pid:
            deleted_passes.add(pid)
            cursor.execute("INSERT OR REPLACE INTO deleted_pass_ids (pass_id, deleted_at) VALUES (?, ?)", (pid, now_str))
            record_deleted_item("ticket", pid)
            cursor.execute("DELETE FROM payments WHERE pass_id = ? OR payment_id LIKE ? OR details LIKE ?", (pid, f"%{pid}%", f"%{pid}%"))
        record_deleted_item("ticket", str(r["id"]))
        cursor.execute("DELETE FROM tickets WHERE id = ?", (r["id"],))

    conn.commit()
    conn.close()

    # Permanently delete from Supabase Cloud as well
    for pid in deleted_passes:
        sync_supabase_delete("tickets", "pass_id", pid)
        sync_supabase_delete("payments", "pass_id", pid)
    if clean_id.isdigit():
        sync_supabase_delete("tickets", "id", clean_id)
        record_deleted_item("ticket", clean_id)
        
    auto_backup_tickets()
    return True

def restore_ticket_from_recycle_bin(ticket_identifier):
    """Restore a deleted ticket from Recycle Bin back to active status"""
    clean_id = str(ticket_identifier).strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, pass_id, event_id, event_title, customer_name, phone, email, city, date_selected, quantity, rate_per_ticket, total_amount, payment_status, utr_reference, booking_status, razorpay_order_id, razorpay_payment_id, created_at 
        FROM tickets 
        WHERE id = ? 
           OR pass_id = ? 
           OR LOWER(pass_id) = LOWER(?)
    """, (int(clean_id) if clean_id.isdigit() else -1, clean_id, clean_id))
    rows = cursor.fetchall()
    
    restored_list = []
    for r in rows:
        cursor.execute("UPDATE tickets SET is_deleted = 0, deleted_at = NULL WHERE id = ?", (r["id"],))
        pid = r["pass_id"]
        if pid:
            cursor.execute("DELETE FROM deleted_pass_ids WHERE pass_id = ? OR LOWER(pass_id) = LOWER(?)", (pid, pid))
            cursor.execute("DELETE FROM deleted_items WHERE item_type = 'ticket' AND (item_id = ? OR LOWER(item_id) = LOWER(?))", (pid, pid))
            restored_list.append(dict(r))
        cursor.execute("DELETE FROM deleted_items WHERE item_type = 'ticket' AND item_id = ?", (str(r["id"]),))
            
    conn.commit()
    conn.close()
    
    # Re-sync to Supabase Cloud
    for t in restored_list:
        sync_supabase_upsert("tickets", {
            "pass_id": t["pass_id"],
            "event_id": t["event_id"],
            "event_title": t["event_title"],
            "customer_name": t["customer_name"],
            "phone": t["phone"],
            "email": t["email"],
            "city": t["city"],
            "date_selected": t["date_selected"],
            "quantity": t["quantity"],
            "rate_per_ticket": t["rate_per_ticket"],
            "total_amount": t["total_amount"],
            "payment_status": t["payment_status"],
            "utr_reference": t["utr_reference"],
            "booking_status": "Confirmed",
            "razorpay_order_id": t.get("razorpay_order_id") or "",
            "razorpay_payment_id": t.get("razorpay_payment_id") or "",
            "created_at": t.get("created_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
    auto_backup_tickets()
    return True

def restore_all_recycle_bin_tickets():
    """Restore all tickets in Recycle Bin back to active status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET is_deleted = 0, deleted_at = NULL WHERE is_deleted = 1")
    cursor.execute("DELETE FROM deleted_pass_ids")
    conn.commit()
    conn.close()
    auto_backup_tickets()
    return True

def empty_recycle_bin():
    """Permanently delete all tickets currently in Recycle Bin"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, pass_id FROM tickets WHERE is_deleted = 1")
    rows = cursor.fetchall()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deleted_passes = []
    for r in rows:
        pid = r["pass_id"]
        if pid:
            deleted_passes.append(pid)
            cursor.execute("INSERT OR REPLACE INTO deleted_pass_ids (pass_id, deleted_at) VALUES (?, ?)", (pid, now_str))
        cursor.execute("DELETE FROM tickets WHERE id = ?", (r["id"],))
    conn.commit()
    conn.close()
    
    for pid in deleted_passes:
        sync_supabase_delete("tickets", "pass_id", pid)
        sync_supabase_delete("payments", "pass_id", pid)
        
    auto_backup_tickets()
    return True

def get_ticket_by_pass_id(pass_id: str):
    import urllib.parse
    raw = str(pass_id or "").strip()
    if not raw:
        return None
    decoded = urllib.parse.unquote(raw).strip()
    normalized = decoded.replace("_", "/").strip()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    clean_formatted = f"Dandia/2026/{int(decoded):03d}" if decoded.isdigit() else normalized
    
    cursor.execute("""
        SELECT * FROM tickets 
        WHERE LOWER(pass_id) = LOWER(?) 
           OR LOWER(pass_id) = LOWER(?)
           OR LOWER(pass_id) = LOWER(?)
           OR LOWER(pass_id) = LOWER(?)
           OR pass_id LIKE ? 
           OR pass_id LIKE ?
           OR id = ?
        ORDER BY (CASE WHEN pass_id NOT LIKE '%_OLD%' THEN 0 ELSE 1 END), id DESC LIMIT 1
    """, (raw, decoded, normalized, clean_formatted, f"%{decoded}%", f"%{normalized}%", int(decoded) if decoded.isdigit() else -1))
    row = cursor.fetchone()
    
    # If still not found, search by trailing sequential number (e.g. 302)
    if not row:
        nums = re.findall(r"\d+", decoded)
        if nums:
            seq = int(nums[-1])
            target_pass = f"Dandia/2026/{seq:03d}"
            cursor.execute("""
                SELECT * FROM tickets
                WHERE pass_id = ? OR pass_id LIKE ?
                ORDER BY (CASE WHEN pass_id NOT LIKE '%_OLD%' THEN 0 ELSE 1 END), id DESC
                LIMIT 1
            """, (target_pass, f"%{target_pass}%"))
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
