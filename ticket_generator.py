import os
import re
import functools
import qrcode
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@functools.lru_cache(maxsize=128)
def get_font(size, bold=False):
    bundled_font = os.path.join(BASE_DIR, "arialbd.ttf" if bold else "arial.ttf")
    paths = [
        bundled_font,
        # Linux standard truetype font paths (for Render / Docker / Debian / Ubuntu)
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # Windows standard fonts
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()

_CACHED_VENUE_QR_IMG = None
def get_cached_venue_qr():
    global _CACHED_VENUE_QR_IMG
    if _CACHED_VENUE_QR_IMG is None:
        venue_map_url = "https://maps.google.com/?q=Trilochan+Resorts+Trilochan+Vihar+Sundarpada+Ebaranga+Jatni+Road+Bhubaneswar+751002"
        qr1 = qrcode.QRCode(version=1, box_size=5, border=1)
        qr1.add_data(venue_map_url)
        qr1.make(fit=True)
        img = qr1.make_image(fill_color="black", back_color="white").convert("RGB")
        _CACHED_VENUE_QR_IMG = img.resize((140, 140), Image.Resampling.LANCZOS)
    return _CACHED_VENUE_QR_IMG.copy()

def format_serial_number(pass_id):
    """
    Format serial number as 'Dandia/2026/301'
    """
    s = str(pass_id or "").strip()
    if s.startswith("Dandia/2026/"):
        return s
    nums = re.findall(r"\d+", s)
    if nums:
        try:
            seq = int(nums[-1])
            return f"Dandia/2026/{seq:03d}"
        except Exception:
            pass
    return "Dandia/2026/301"

def draw_dashed_line(draw, start_pos, end_pos, fill, width=1, dash_len=8, gap_len=6):
    x1, y1 = start_pos
    x2, y2 = end_pos
    if y1 == y2:  # Horizontal
        curr_x = x1
        while curr_x < x2:
            next_x = min(curr_x + dash_len, x2)
            draw.line([(curr_x, y1), (next_x, y1)], fill=fill, width=width)
            curr_x += dash_len + gap_len
    elif x1 == x2:  # Vertical
        curr_y = y1
        while curr_y < y2:
            next_y = min(curr_y + dash_len, y2)
            draw.line([(x1, curr_y), (x1, next_y)], fill=fill, width=width)
            curr_y += dash_len + gap_len

def generate_ticket_image(
    pass_id="Dandia/2026/301",
    customer_name="Attendee",
    phone="7992993433",
    address="Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002",
    date_selected="18/10/2026 (Sunday)",
    amount=299,
    base_url="",
    event_title="FAMILY DANDIA NIGHT 2026 - MELODY NIGHT SHOW",
    venue="Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002",
    quantity=1,
    payment_mode="Online (Razorpay)",
    utr_ref=""
):
    """
    Generates standard A4 printable ticket (1240 x 1754 px at 150 DPI)
    with:
    - High-contrast prominent ATTENDEE NAME header banner
    - Dual QR codes (Venue Navigation QR + Gate Entry QR)
    - Show Timings strictly: 7:00 PM TO 10:00 PM
    - Organizer Phone numbers: 7992993433 / 7008955582
    - Organizer Email: mrunmayaassoxiates2023@gmail.com
    - Perforated Tear-off Gate Admission Token / Counterfoil at the bottom
    """
    sl_clean = format_serial_number(pass_id)
    raw_name = str(customer_name or "").strip()
    clean_name = raw_name if raw_name and raw_name.lower() not in ("none", "null", "undefined") else "Valued Guest"
    clean_mob = str(phone).strip() if phone else "7992993433"
    clean_addr = str(address).strip() if address else "Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002"
    clean_date = str(date_selected).strip() if date_selected else "18/10/2026 (Sunday)"
    clean_title = str(event_title).strip() if event_title else "FAMILY DANDIA NIGHT 2026 - MELODY NIGHT SHOW"
    clean_venue = str(venue).strip() if venue else "Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002"
    
    org_phones = "7992993433 / 7008955582"
    org_email = "mrunmayaassoxiates2023@gmail.com"

    try:
        amt_float = float(amount)
        rate_str = f"{int(amt_float)}" if amt_float.is_integer() else f"{amt_float:.2f}"
    except Exception:
        rate_str = str(amount)

    try:
        qty_int = int(quantity)
    except Exception:
        qty_int = 1

    # VIP Pass Detection
    is_vip = False
    pm_upper = str(payment_mode or "").upper()
    pass_upper = str(pass_id or "").upper()
    utr_upper = str(utr_ref or "").upper()
    if "VIP" in pm_upper or "VIP" in pass_upper or "VIP" in utr_upper or "COMPLIMENTARY" in pm_upper:
        is_vip = True
    try:
        if float(amount or 0) == 0 and ("VIP" in pm_upper or "COMPLIMENTARY" in pm_upper or "VIP" in utr_upper):
            is_vip = True
    except Exception:
        pass

    # Standard A4 at 150 DPI: 1240 x 1754 px
    WIDTH, HEIGHT = 1240, 1754
    im = Image.new("RGB", (WIDTH, HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)

    # Color Palette - Professional Print Theme
    NAVY = (15, 23, 42)           # #0f172a Deep Slate Navy
    NAVY_LIGHT = (30, 41, 59)     # Slate 800
    GOLD = (180, 83, 9)           # #b45309 Amber 700
    GOLD_LIGHT = (254, 243, 199)  # #fef3c7 Amber 100
    GOLD_BORDER = (245, 158, 11)  # #f59e0b Amber 500
    BORDER = (203, 213, 225)      # Slate 300
    BORDER_DASH = (148, 163, 184) # Slate 400
    BG_SECTION = (248, 250, 252)  # Slate 50
    TEXT_MUTED = (100, 116, 139)  # Slate 500
    GREEN = (22, 101, 52)         # Emerald 800
    GREEN_BG = (220, 252, 231)    # Emerald 100
    GREEN_BORDER = (34, 197, 94)  # Emerald 500
    RED_ACCENT = (185, 28, 28)    # Red 700
    TOKEN_BG = (255, 253, 245)    # Light cream security background

    # Fonts
    f_brand = get_font(28, bold=True)
    f_sub = get_font(14, bold=False)
    f_title = get_font(28, bold=True)
    f_subtitle = get_font(15, bold=True)
    f_h2 = get_font(18, bold=True)
    f_pass_id = get_font(38, bold=True)
    f_label = get_font(13, bold=False)
    f_val = get_font(16, bold=True)
    f_qr_title = get_font(15, bold=True)
    f_terms_h = get_font(15, bold=True)
    f_terms = get_font(12, bold=False)
    f_foot = get_font(12, bold=False)
    f_token_h = get_font(17, bold=True)

    margin = 40
    # Outer double border for main pass
    draw.rectangle([margin, margin, WIDTH - margin, HEIGHT - margin], outline=NAVY, width=2)
    draw.rectangle([margin + 4, margin + 4, WIDTH - margin - 4, HEIGHT - margin - 4], outline=BORDER, width=1)

    # =========================================================================
    # 1. TOP HEADER BRANDING
    # =========================================================================
    header_h = 90
    draw.rectangle([margin + 5, margin + 5, WIDTH - margin - 5, margin + header_h], fill=BG_SECTION)
    draw.line([margin + 5, margin + header_h, WIDTH - margin - 5, margin + header_h], fill=BORDER, width=2)

    # Brand Title & Organizer Contact
    draw.text((margin + 25, margin + 14), "MRUNMAYA ASSOCIATES", fill=NAVY, font=f_brand)
    draw.text((margin + 25, margin + 48), "Citizen Services, Event Tickets & Digital Solutions Desk", fill=TEXT_MUTED, font=f_sub)
    draw.text((margin + 25, margin + 68), f"Helpline: +91 {org_phones} | Email: {org_email}", fill=GOLD, font=f_sub)

    # Right Badge: Official Entry Pass / VIP Pass
    badge_w, badge_h = 340, 68
    badge_x = WIDTH - margin - badge_w - 20
    badge_y = margin + 11
    if is_vip:
        draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=(254, 240, 138), outline=(217, 119, 6), width=2)
        draw.text((badge_x + 16, badge_y + 10), "VIP ENTRY PASS", fill=(180, 83, 9), font=f_h2)
        draw.text((badge_x + 16, badge_y + 36), "COMPLIMENTARY VIP GUEST ACCESS", fill=(113, 63, 18), font=get_font(12, bold=True))
    else:
        draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=GOLD_LIGHT, outline=GOLD_BORDER, width=1)
        draw.text((badge_x + 16, badge_y + 10), "OFFICIAL ENTRY PASS", fill=GOLD, font=f_h2)
        draw.text((badge_x + 16, badge_y + 36), "STANDARD A4 PRINTABLE VOUCHER", fill=NAVY_LIGHT, font=get_font(12, bold=False))

    # =========================================================================
    # 2. EVENT TITLE BANNER (MELODY NIGHT SHOW & STRICT 7:00 PM - 10:00 PM)
    # =========================================================================
    banner_y = margin + header_h + 10
    banner_h = 100
    draw.rectangle([margin + 16, banner_y, WIDTH - margin - 16, banner_y + banner_h], fill=(255, 251, 235), outline=GOLD_BORDER, width=1)
    
    draw.text((margin + 28, banner_y + 10), clean_title.upper(), fill=NAVY, font=f_title)
    draw.text((margin + 28, banner_y + 46), "Venue: Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, BBSR - 751002", fill=GOLD, font=f_subtitle)
    draw.text((margin + 28, banner_y + 70), "Show Timing: 7:00 PM TO 10:00 PM   |   Official Dandia Night Voucher", fill=NAVY_LIGHT, font=get_font(14, bold=True))

    # =========================================================================
    # 3. PASS SERIAL NUMBER & STATUS BAR (HUGE, BOLD, HIGH-CONTRAST BADGE)
    # =========================================================================
    bar_y = banner_y + banner_h + 10
    bar_h = 66
    draw.rectangle([margin + 16, bar_y, WIDTH - margin - 16, bar_y + bar_h], fill=NAVY)

    draw.text((margin + 28, bar_y + 22), "PASS SERIAL NO:", fill=(203, 213, 225), font=get_font(14, bold=True))

    # Bright Gold / Amber Highlight Container for Pass ID
    pass_badge_x = margin + 175
    pass_badge_w = 460
    draw.rectangle([pass_badge_x, bar_y + 7, pass_badge_x + pass_badge_w, bar_y + bar_h - 7], fill=(254, 243, 199), outline=GOLD_BORDER, width=2)
    draw.text((pass_badge_x + 18, bar_y + 8), sl_clean, fill=NAVY, font=get_font(36, bold=True))

    # Status Pill
    if is_vip:
        stat_w, stat_h = 280, 42
        stat_x = WIDTH - margin - stat_w - 24
        stat_y = bar_y + 12
        draw.rectangle([stat_x, stat_y, stat_x + stat_w, stat_y + stat_h], fill=(254, 240, 138), outline=(217, 119, 6), width=2)
        draw.text((stat_x + 14, stat_y + 10), "STATUS: VIP GUEST", fill=(180, 83, 9), font=get_font(16, bold=True))
    else:
        stat_w, stat_h = 240, 42
        stat_x = WIDTH - margin - stat_w - 24
        stat_y = bar_y + 12
        draw.rectangle([stat_x, stat_y, stat_x + stat_w, stat_y + stat_h], fill=GREEN_BG, outline=GREEN_BORDER, width=2)
        draw.text((stat_x + 18, stat_y + 10), "STATUS: CONFIRMED", fill=GREEN, font=get_font(16, bold=True))

    # =========================================================================
    # 4. PROMINENT ATTENDEE NAME & CREDENTIALS BANNER (HIGH-CONTRAST & BOLD)
    # =========================================================================
    name_bar_y = bar_y + bar_h + 10
    name_bar_h = 76
    draw.rectangle([margin + 16, name_bar_y, WIDTH - margin - 16, name_bar_y + name_bar_h], fill=(241, 245, 249), outline=NAVY, width=2)

    # Left: Gold/Navy Attendee Accent Box
    n_tag_w = 280
    draw.rectangle([margin + 16, name_bar_y, margin + 16 + n_tag_w, name_bar_y + name_bar_h], fill=NAVY)
    draw.text((margin + 28, name_bar_y + 14), "ATTENDEE NAME", fill=(254, 240, 138), font=get_font(18, bold=True))
    draw.text((margin + 28, name_bar_y + 42), "PRIMARY TICKET HOLDER", fill=(203, 213, 225), font=get_font(11, bold=True))

    # Center: HUGE BOLD ATTENDEE FULL NAME
    name_x = margin + 16 + n_tag_w + 20
    name_display = clean_name.upper()
    f_att_size = 32 if len(name_display) <= 24 else (26 if len(name_display) <= 32 else 22)
    draw.text((name_x, name_bar_y + 18), name_display, fill=NAVY, font=get_font(f_att_size, bold=True))
    
    info_sub = f"Registered Phone: +91 {clean_mob}   |   Admit: {qty_int} Person(s)   |   Event Date: {clean_date}"
    draw.text((name_x, name_bar_y + 50), info_sub, fill=GOLD, font=get_font(12, bold=True))

    # Right Badge inside Name Bar: Verified Guest Seal
    v_badge_w, v_badge_h = 160, 48
    v_badge_x = WIDTH - margin - 16 - v_badge_w - 12
    v_badge_y = name_bar_y + 14
    draw.rectangle([v_badge_x, v_badge_y, v_badge_x + v_badge_w, v_badge_y + v_badge_h], fill=(255, 255, 255), outline=GREEN_BORDER, width=1)
    draw.text((v_badge_x + 14, v_badge_y + 8), "[OK] VERIFIED", fill=GREEN, font=get_font(12, bold=True))
    draw.text((v_badge_x + 14, v_badge_y + 26), "LUCKY DRAW PASS", fill=GOLD, font=get_font(10, bold=True))

    # =========================================================================
    # 5. DUAL QR CODE BLOCKS (GPS MAPS NAVIGATION + GATE ENTRY DETAILS)
    # =========================================================================
    qr_y = name_bar_y + name_bar_h + 10
    box_w = (WIDTH - 2 * margin - 48) // 2
    box_h = 264

    # BOX 1: VENUE LOCATION QR (GOOGLE MAPS)
    b1_x = margin + 16
    draw.rectangle([b1_x, qr_y, b1_x + box_w, qr_y + box_h], fill=(255, 255, 255), outline=BORDER, width=1)
    draw.rectangle([b1_x, qr_y, b1_x + box_w, qr_y + 34], fill=(241, 245, 249))
    draw.text((b1_x + 16, qr_y + 8), "1. VENUE LOCATION QR CODE (MAPS)", fill=NAVY, font=f_qr_title)

    qr1_img = get_cached_venue_qr()
    im.paste(qr1_img, (b1_x + 16, qr_y + 44))

    b1_t_x = b1_x + 172
    draw.text((b1_t_x, qr_y + 44), "SCAN FOR GPS NAVIGATION", fill=GOLD, font=get_font(13, bold=True))
    draw.text((b1_t_x, qr_y + 64), "Venue Name:", fill=TEXT_MUTED, font=f_label)
    draw.text((b1_t_x, qr_y + 80), "Trilochan Resorts", fill=NAVY, font=get_font(15, bold=True))
    draw.text((b1_t_x, qr_y + 102), "Address Details:", fill=TEXT_MUTED, font=f_label)
    draw.text((b1_t_x, qr_y + 118), "Trilochan Vihar, Sundarpada,", fill=NAVY_LIGHT, font=f_sub)
    draw.text((b1_t_x, qr_y + 134), "Ebaranga, Jatni Road,", fill=NAVY_LIGHT, font=f_sub)
    draw.text((b1_t_x, qr_y + 150), "Bhubaneswar - 751002", fill=NAVY_LIGHT, font=f_sub)
    draw.text((b1_t_x, qr_y + 170), "Landmark: Trilochan Vihar Gate", fill=TEXT_MUTED, font=get_font(11, bold=False))
    
    draw.text((b1_x + 16, qr_y + 204), "Scan with Google Lens or Camera for instant turn-by-turn navigation.", fill=TEXT_MUTED, font=get_font(11, bold=False))
    draw.text((b1_x + 16, qr_y + 228), "Direct Link: maps.google.com/?q=Trilochan+Resorts", fill=GOLD, font=get_font(11, bold=False))

    # BOX 2: GATE TICKET DETAILS & ENTRY QR
    b2_x = b1_x + box_w + 16
    draw.rectangle([b2_x, qr_y, b2_x + box_w, qr_y + box_h], fill=(255, 255, 255), outline=BORDER, width=1)
    draw.rectangle([b2_x, qr_y, b2_x + box_w, qr_y + 34], fill=(241, 245, 249))
    draw.text((b2_x + 16, qr_y + 8), "2. GATE ENTRY & DETAILS QR CODE", fill=NAVY, font=f_qr_title)

    verify_url = f"https://mrunmayaleads.onrender.com/api/tickets/verify-pass/{sl_clean}"
    qr2_text = (
        f"MRUNMAYA ASSOCIATES - OFFICIAL PASS\n"
        f"Event: {clean_title}\n"
        f"Pass ID: {sl_clean}\n"
        f"Attendee Name: {clean_name}\n"
        f"Mobile: {clean_mob}\n"
        f"Date: {clean_date}\n"
        f"Timing: 7:00 PM TO 10:00 PM\n"
        f"Persons: {qty_int}\n"
        f"Amount: Rs. {rate_str}/- (PAID)\n"
        f"Venue: Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002\n"
        f"Helpline: {org_phones}\n"
        f"Gate URL: {verify_url}"
    )
    qr2 = qrcode.QRCode(version=1, box_size=5, border=1)
    qr2.add_data(qr2_text)
    qr2.make(fit=True)
    qr2_img = qr2.make_image(fill_color="black", back_color="white").convert("RGB")
    qr2_img = qr2_img.resize((140, 140), Image.Resampling.LANCZOS)
    im.paste(qr2_img, (b2_x + 16, qr_y + 44))

    b2_t_x = b2_x + 172
    draw.text((b2_t_x, qr_y + 44), "SCAN AT GATE ADMISSION", fill=GREEN, font=get_font(13, bold=True))
    draw.text((b2_t_x, qr_y + 64), "Pass ID / Ref:", fill=TEXT_MUTED, font=f_label)
    draw.text((b2_t_x, qr_y + 78), sl_clean, fill=NAVY, font=get_font(20, bold=True))
    draw.text((b2_t_x, qr_y + 102), "Attendee Name:", fill=GOLD, font=get_font(12, bold=True))
    draw.text((b2_t_x, qr_y + 118), f"{clean_name.upper()[:24]}", fill=NAVY, font=get_font(17, bold=True))
    draw.text((b2_t_x, qr_y + 142), f"Persons: {qty_int} Guest(s)   |   Date: {clean_date[:10]}", fill=NAVY_LIGHT, font=get_font(12, bold=False))
    draw.text((b2_t_x, qr_y + 162), f"Amount Paid: Rs.{rate_str}/- (PAID)", fill=GREEN, font=get_font(13, bold=True))

    draw.text((b2_x + 16, qr_y + 204), "Show this QR at the gate counter. Security scanner validates pass instantly.", fill=TEXT_MUTED, font=get_font(11, bold=False))
    draw.text((b2_x + 16, qr_y + 228), f"Gate Verification Desk: mrunmayaleads.onrender.com", fill=GOLD, font=get_font(11, bold=False))

    # =========================================================================
    # 6. ATTENDEE & BOOKING INFORMATION TABLE
    # =========================================================================
    tbl_y = qr_y + box_h + 10
    draw.rectangle([margin + 16, tbl_y, WIDTH - margin - 16, tbl_y + 34], fill=NAVY)
    draw.text((margin + 28, tbl_y + 7), "ATTENDEE & RESERVATION DETAILS", fill=(255, 255, 255), font=f_h2)

    tbl_b_y = tbl_y + 34
    tbl_h = 162
    draw.rectangle([margin + 16, tbl_b_y, WIDTH - margin - 16, tbl_b_y + tbl_h], fill=(255, 255, 255), outline=BORDER, width=1)

    col_w = (WIDTH - 2 * margin - 32) // 2
    row_h = 54
    details = [
        ("Attendee / Ticket Holder Name", clean_name.upper(), "Registered Mobile Number", f"+91 {clean_mob}"),
        ("Event Date Selected", clean_date, "Show Timings", "7:00 PM TO 10:00 PM"),
        ("Pass Type / Category", f"Family Dandia Entry ({qty_int} Person(s))", "Payment Status", f"Rs. {rate_str}/- PAID ({payment_mode})")
    ]

    for idx, (lbl1, v1, lbl2, v2) in enumerate(details):
        r_y = tbl_b_y + idx * row_h
        if idx % 2 == 1:
            draw.rectangle([margin + 17, r_y, WIDTH - margin - 17, r_y + row_h], fill=BG_SECTION)
        if idx > 0:
            draw.line([margin + 16, r_y, WIDTH - margin - 16, r_y], fill=BORDER, width=1)
        
        # Col 1
        draw.text((margin + 28, r_y + 7), lbl1, fill=TEXT_MUTED, font=f_label)
        if idx == 0:
            draw.text((margin + 28, r_y + 25), f"[OK] {v1}", fill=NAVY, font=get_font(21, bold=True))
        else:
            draw.text((margin + 28, r_y + 25), v1, fill=NAVY, font=f_val)

        # Col 2
        c2_x = margin + 16 + col_w
        draw.line([c2_x, r_y, c2_x, r_y + row_h], fill=BORDER, width=1)
        draw.text((c2_x + 18, r_y + 7), lbl2, fill=TEXT_MUTED, font=f_label)
        v2_color = GREEN if "PAID" in v2 else NAVY
        draw.text((c2_x + 18, r_y + 25), v2, fill=v2_color, font=f_val)

    # =========================================================================
    # 7. INCLUSIONS & FESTIVE HIGHLIGHTS STRIP
    # =========================================================================
    inc_y = tbl_b_y + tbl_h + 10
    draw.rectangle([margin + 16, inc_y, WIDTH - margin - 16, inc_y + 50], fill=GOLD_LIGHT, outline=GOLD_BORDER, width=1)
    draw.text((margin + 28, inc_y + 7), "PASS INCLUSIONS & FESTIVE HIGHLIGHTS:", fill=GOLD, font=get_font(13, bold=True))
    draw.text((margin + 28, inc_y + 27), "[+] Live DJ Dandia Arena   |   [+] Dandia Sticks Available (Paid)   |   [+] Mega Lucky Draw Coupon   |   [+] Kids & Family Zone", fill=NAVY_LIGHT, font=get_font(12, bold=False))

    # =========================================================================
    # 8. IMPORTANT INSTRUCTIONS FOR ENTRY
    # =========================================================================
    t_y = inc_y + 58
    t_h = 132
    draw.rectangle([margin + 16, t_y, WIDTH - margin - 16, t_y + t_h], fill=BG_SECTION, outline=BORDER, width=1)
    draw.text((margin + 28, t_y + 7), "IMPORTANT INSTRUCTIONS FOR ENTRY (PLEASE READ):", fill=NAVY, font=f_terms_h)
    
    rules = [
        "1. Please carry this printed A4 ticket (or digital voucher) along with a valid Govt ID proof at the entrance gate.",
        "2. Each pass has a unique QR code. Once scanned at admission desk, it cannot be reused by another guest.",
        "3. Entry gates open strictly at 06:30 PM. Show timings are 7:00 PM TO 10:00 PM.",
        "4. Traditional Dandia / Ethnic attire warmly encouraged. Dandia sticks are available for purchase at venue counters (Paid).",
        f"5. Organizers Helpline: +91 {org_phones} | Email: {org_email}"
    ]
    for r_idx, rule in enumerate(rules):
        draw.text((margin + 28, t_y + 30 + r_idx * 19), rule, fill=NAVY_LIGHT, font=f_terms)

    # =========================================================================
    # 9. ORGANIZER DESK & AUTHORIZED STAMP
    # =========================================================================
    foot_y = t_y + t_h + 10
    draw.line([margin + 16, foot_y, WIDTH - margin - 16, foot_y], fill=BORDER, width=1)

    draw.text((margin + 20, foot_y + 5), "MRUNMAYA ASSOCIATES | OFFICIAL ORGANIZER DESK", fill=NAVY, font=get_font(13, bold=True))
    draw.text((margin + 20, foot_y + 22), "Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002", fill=TEXT_MUTED, font=f_foot)
    draw.text((margin + 20, foot_y + 38), f"Helpline: +91 {org_phones} | Email: {org_email}", fill=GOLD, font=f_foot)

    stamp_w, stamp_h = 240, 50
    stamp_x = WIDTH - margin - stamp_w - 16
    stamp_y = foot_y + 3
    draw.rectangle([stamp_x, stamp_y, stamp_x + stamp_w, stamp_y + stamp_h], outline=GOLD_BORDER, width=1)
    draw.text((stamp_x + 14, stamp_y + 5), "AUTHORIZED ENTRY PASS", fill=GOLD, font=get_font(12, bold=True))
    draw.text((stamp_x + 14, stamp_y + 20), "MRUNMAYA ASSOCIATES", fill=NAVY, font=get_font(13, bold=True))
    draw.text((stamp_x + 14, stamp_y + 35), "[OK] Digitally Signed & Verified", fill=GREEN, font=get_font(11, bold=False))

    # =========================================================================
    # 10. PERFORATED SCISSOR CUT LINE (TEAR-OFF DIVIDER)
    # =========================================================================
    cut_y = foot_y + 58
    badge_txt = "- - - TEAR HERE AT ENTRY GATE (ORGANIZER GATE TOKEN / COUNTERFOIL) - - -"
    f_cut = get_font(12, bold=True)
    bbox = draw.textbbox((0, 0), badge_txt, font=f_cut)
    txt_w = bbox[2] - bbox[0]
    txt_x = (WIDTH - txt_w) // 2
    
    draw_dashed_line(draw, (margin + 16, cut_y), (txt_x - 12, cut_y), fill=BORDER_DASH, width=2, dash_len=8, gap_len=5)
    draw.rectangle([txt_x - 8, cut_y - 10, txt_x + txt_w + 8, cut_y + 10], fill=(255, 255, 255))
    draw.text((txt_x, cut_y - 8), badge_txt, fill=RED_ACCENT, font=f_cut)
    draw_dashed_line(draw, (txt_x + txt_w + 12, cut_y), (WIDTH - margin - 16, cut_y), fill=BORDER_DASH, width=2, dash_len=8, gap_len=5)

    sub_help = "[ ATTENDEE KEEPS UPPER PASS AS SOUVENIR   |   GATE SECURITY TEARS & RETAINS THIS BOTTOM TOKEN ]"
    f_sub_h = get_font(11, bold=False)
    s_bbox = draw.textbbox((0, 0), sub_help, font=f_sub_h)
    s_w = s_bbox[2] - s_bbox[0]
    draw.text(((WIDTH - s_w) // 2, cut_y + 13), sub_help, fill=TEXT_MUTED, font=f_sub_h)

    # =========================================================================
    # 11. BOTTOM TEAR-OFF TOKEN (ORGANIZER GATE COUNTERFOIL)
    # =========================================================================
    token_y = cut_y + 32
    token_h = HEIGHT - margin - token_y - 8
    token_w = WIDTH - 2 * margin - 32
    token_x = margin + 16

    draw.rectangle([token_x, token_y, token_x + token_w, token_y + token_h], fill=TOKEN_BG, outline=GOLD_BORDER, width=2)
    draw_dashed_line(draw, (token_x + 4, token_y + 4), (token_x + token_w - 4, token_y + 4), fill=BORDER_DASH, width=1)
    draw_dashed_line(draw, (token_x + 4, token_y + token_h - 4), (token_x + token_w - 4, token_y + token_h - 4), fill=BORDER_DASH, width=1)
    draw_dashed_line(draw, (token_x + 4, token_y + 4), (token_x + 4, token_y + token_h - 4), fill=BORDER_DASH, width=1)
    draw_dashed_line(draw, (token_x + token_w - 4, token_y + 4), (token_x + token_w - 4, token_y + token_h - 4), fill=BORDER_DASH, width=1)

    th_h = 40
    draw.rectangle([token_x, token_y, token_x + token_w, token_y + th_h], fill=NAVY)
    token_hdr_txt = "VIP GATE ADMISSION TOKEN / COUNTERFOIL" if is_vip else "ORGANIZER GATE ENTRY TOKEN / COUNTERFOIL"
    draw.text((token_x + 18, token_y + 9), token_hdr_txt, fill=(254, 240, 138), font=f_token_h)
    draw.text((token_x + 550, token_y + 12), "SECURITY ADMISSION COPY (TEAR & RETAIN AT GATE)", fill=(203, 213, 225), font=get_font(12, bold=True))

    colA_x = token_x + 16
    colA_y = token_y + th_h + 10
    
    # Token Pass ID Highlight Box
    draw.rectangle([colA_x, colA_y, colA_x + 440, colA_y + 48], fill=GOLD_LIGHT, outline=GOLD_BORDER, width=2)
    draw.text((colA_x + 14, colA_y + 14), "TOKEN NO:", fill=GOLD, font=get_font(13, bold=True))
    draw.text((colA_x + 115, colA_y + 5), sl_clean, fill=NAVY, font=get_font(32, bold=True))

    # Prominent Attendee Name on Token
    draw.rectangle([colA_x, colA_y + 54, colA_x + 440, colA_y + 92], fill=(241, 245, 249), outline=BORDER, width=1)
    draw.text((colA_x + 12, colA_y + 61), "ATTENDEE:", fill=GOLD, font=get_font(11, bold=True))
    draw.text((colA_x + 88, colA_y + 57), clean_name.upper()[:24], fill=NAVY, font=get_font(19, bold=True))

    token_pay_status = "VIP COMPLIMENTARY (FREE)" if is_vip else f"Rs. {rate_str}/- PAID ({payment_mode})"
    token_fields = [
        ("Event Name:", clean_title[:45]),
        ("Mobile Number:", f"+91 {clean_mob}"),
        ("Date & Timing:", f"{clean_date}  |  7 PM - 10 PM"),
        ("Persons Allowed:", f"{qty_int} Guest(s)"),
        ("Payment Status:", token_pay_status),
        ("Venue Location:", "Trilochan Resorts, Jatni Rd, BBSR"),
        ("Organizer Support:", f"+91 {org_phones}")
    ]

    for f_idx, (f_lbl, f_val_text) in enumerate(token_fields):
        line_y = colA_y + 100 + f_idx * 19
        draw.text((colA_x, line_y), f_lbl, fill=TEXT_MUTED, font=get_font(11, bold=False))
        v_col = GREEN if "PAID" in f_val_text else NAVY
        draw.text((colA_x + 125, line_y), f_val_text, fill=v_col, font=get_font(11, bold=True))

    # Vertical divider 1
    div1_x = colA_x + 445
    draw.line([div1_x, token_y + th_h, div1_x, token_y + token_h - 26], fill=BORDER, width=1)

    # Col B: Quick Gate Token QR Code
    colB_x = div1_x + 16
    colB_y = token_y + th_h + 10
    draw.text((colB_x + 12, colB_y), "GATE VERIFICATION QR", fill=NAVY, font=get_font(13, bold=True))

    qr3_text = (
        f"GATE TOKEN: {sl_clean}\n"
        f"NAME: {clean_name}\n"
        f"MOB: {clean_mob}\n"
        f"DATE: {clean_date}\n"
        f"TIMING: 7:00 PM TO 10:00 PM\n"
        f"GUESTS: {qty_int}\n"
        f"AMOUNT: Rs.{rate_str} PAID\n"
        f"STATUS: ADMITTED"
    )
    qr3 = qrcode.QRCode(version=1, box_size=4, border=1)
    qr3.add_data(qr3_text)
    qr3.make(fit=True)
    qr3_img = qr3.make_image(fill_color="black", back_color="white").convert("RGB")
    qr3_img = qr3_img.resize((140, 140), Image.Resampling.LANCZOS)
    im.paste(qr3_img, (colB_x + 10, colB_y + 22))

    draw.text((colB_x + 15, colB_y + 170), "GATE SCANNER QR", fill=GREEN, font=get_font(12, bold=True))
    draw.text((colB_x + 10, colB_y + 188), "Scan & Detach Token", fill=TEXT_MUTED, font=get_font(11, bold=False))

    # Vertical divider 2
    div2_x = colB_x + 185
    draw.line([div2_x, token_y + th_h, div2_x, token_y + token_h - 26], fill=BORDER, width=1)

    # Col C: Gate Marshal Verification & Signature Desk
    colC_x = div2_x + 16
    colC_y = token_y + th_h + 10
    draw.text((colC_x, colC_y), "GATE MARSHAL ADMISSION DESK", fill=NAVY, font=get_font(13, bold=True))

    box_m_y = colC_y + 20
    box_m_w = token_w - (colC_x - token_x) - 16
    box_m_h = 195
    draw.rectangle([colC_x, box_m_y, colC_x + box_m_w, box_m_y + box_m_h], fill=(255, 255, 255), outline=BORDER, width=1)

    draw.text((colC_x + 12, box_m_y + 8), "[ OK ] TICKET VERIFIED & ALLOWED", fill=GREEN, font=get_font(12, bold=True))
    draw.text((colC_x + 12, box_m_y + 28), "Admitted Guests: ______ Person(s)", fill=NAVY_LIGHT, font=get_font(12, bold=False))
    draw.text((colC_x + 12, box_m_y + 48), "Dandia Sticks (Paid Counter): [ ISSUED / N/A ]", fill=NAVY_LIGHT, font=get_font(12, bold=False))
    draw.text((colC_x + 12, box_m_y + 68), "Admission Time: ______ : ______ PM", fill=NAVY_LIGHT, font=get_font(12, bold=False))
    draw.text((colC_x + 12, box_m_y + 90), "Security Officer Sign / Gate Stamp:", fill=TEXT_MUTED, font=get_font(11, bold=False))
    
    stamp_inner_y = box_m_y + 114
    stamp_inner_h = 70
    draw.rectangle([colC_x + 12, stamp_inner_y, colC_x + box_m_w - 12, stamp_inner_y + stamp_inner_h], fill=(248, 250, 252), outline=BORDER, width=1)
    draw.text((colC_x + 24, stamp_inner_y + 26), "[ OFFICIAL GATE STAMP & SIGNATURE ]", fill=TEXT_MUTED, font=get_font(12, bold=False))

    t_foot_y = token_y + token_h - 24
    draw.line([token_x, t_foot_y, token_x + token_w, t_foot_y], fill=BORDER, width=1)
    draw.text((token_x + 18, t_foot_y + 5), "* MANDATORY FOR SECURITY CONTROL: Detach this token slip along the scissor line upon guest entry and drop into Gate Admission Box.", fill=RED_ACCENT, font=get_font(11, bold=True))

    return im

if __name__ == "__main__":
    t = generate_ticket_image(
        pass_id="Dandia/2026/301",
        customer_name="Priyanka Mohapatra",
        phone="7992993433",
        address="Sundarpada, Bhubaneswar",
        date_selected="18/10/2026 (Sunday)",
        amount=299
    )
    t.save("a4_ticket_preview.png", "PNG", dpi=(150, 150))
    print("Generated clean A4 ticket image with bottom tear-off token successfully!")
