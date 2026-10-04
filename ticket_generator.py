import os
import re
import qrcode
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_font(size, bold=False):
    paths = [
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
    return ImageFont.load_default()

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
    address="Sundarpada, Bhubaneswar",
    date_selected="18/10/2026 (Sunday)",
    amount=299,
    base_url="",
    event_title="FAMILY DANDIA NIGHT 2026 - MELODY NIGHT SHOW",
    venue="Trilochan Resorts, Sundarpada, Bhubaneswar",
    quantity=1,
    payment_mode="Online (Razorpay)"
):
    """
    Generates standard A4 printable ticket (1240 x 1754 px at 150 DPI)
    with:
    - Dual QR codes (Venue Navigation QR + Gate Entry QR)
    - Show Timings strictly: 7:00 PM TO 10:00 PM
    - Organizer Phone numbers: 7992993433 / 7008955582
    - Organizer Email: mrunmayaassoxiates2023@gmail.com
    - Perforated Tear-off Gate Admission Token / Counterfoil at the bottom
    """
    sl_clean = format_serial_number(pass_id)
    clean_name = str(customer_name).strip() if customer_name else "Valued Guest"
    clean_mob = str(phone).strip() if phone else "7992993433"
    clean_addr = str(address).strip() if address else "Sundarpada, Bhubaneswar"
    clean_date = str(date_selected).strip() if date_selected else "18/10/2026 (Sunday)"
    clean_title = str(event_title).strip() if event_title else "FAMILY DANDIA NIGHT 2026 - MELODY NIGHT SHOW"
    clean_venue = str(venue).strip() if venue else "Trilochan Resorts, Sundarpada, Bhubaneswar"
    
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
    f_title = get_font(30, bold=True)
    f_subtitle = get_font(16, bold=True)
    f_h2 = get_font(18, bold=True)
    f_pass_id = get_font(30, bold=True)
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
    header_h = 92
    draw.rectangle([margin + 5, margin + 5, WIDTH - margin - 5, margin + header_h], fill=BG_SECTION)
    draw.line([margin + 5, margin + header_h, WIDTH - margin - 5, margin + header_h], fill=BORDER, width=2)

    # Brand Title & Organizer Contact
    draw.text((margin + 25, margin + 14), "MRUNMAYA ASSOCIATES", fill=NAVY, font=f_brand)
    draw.text((margin + 25, margin + 48), "Citizen Services, Event Tickets & Digital Solutions Desk", fill=TEXT_MUTED, font=f_sub)
    draw.text((margin + 25, margin + 68), f"Helpline: +91 {org_phones} | Email: {org_email}", fill=GOLD, font=f_sub)

    # Right Badge: Official Entry Pass
    badge_w, badge_h = 320, 68
    badge_x = WIDTH - margin - badge_w - 20
    badge_y = margin + 12
    draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=GOLD_LIGHT, outline=GOLD_BORDER, width=1)
    draw.text((badge_x + 16, badge_y + 10), "OFFICIAL ENTRY PASS", fill=GOLD, font=f_h2)
    draw.text((badge_x + 16, badge_y + 36), "STANDARD A4 PRINTABLE VOUCHER", fill=NAVY_LIGHT, font=get_font(12, bold=False))

    # =========================================================================
    # 2. EVENT TITLE BANNER (WITH MELODY NIGHT SHOW & STRICT 7:00 PM - 10:00 PM)
    # =========================================================================
    banner_y = margin + header_h + 12
    banner_h = 110
    draw.rectangle([margin + 16, banner_y, WIDTH - margin - 16, banner_y + banner_h], fill=(255, 251, 235), outline=GOLD_BORDER, width=1)
    
    draw.text((margin + 28, banner_y + 12), clean_title.upper(), fill=NAVY, font=f_title)
    draw.text((margin + 28, banner_y + 50), "In Grand Collaboration with Trilochan Resorts, Sundarpada, Bhubaneswar", fill=GOLD, font=f_subtitle)
    draw.text((margin + 28, banner_y + 76), f"Venue: {clean_venue}   |   Show Timing: 7:00 PM TO 10:00 PM", fill=NAVY_LIGHT, font=get_font(14, bold=True))

    # =========================================================================
    # 3. PASS SERIAL NUMBER & STATUS BAR
    # =========================================================================
    bar_y = banner_y + banner_h + 12
    bar_h = 56
    draw.rectangle([margin + 16, bar_y, WIDTH - margin - 16, bar_y + bar_h], fill=NAVY)

    draw.text((margin + 30, bar_y + 12), "PASS SERIAL NO:", fill=(203, 213, 225), font=get_font(13, bold=False))
    draw.text((margin + 165, bar_y + 9), sl_clean, fill=(254, 240, 138), font=f_pass_id)

    # Status Pill (Confirmed & Paid)
    stat_w, stat_h = 230, 36
    stat_x = WIDTH - margin - stat_w - 30
    stat_y = bar_y + 10
    draw.rectangle([stat_x, stat_y, stat_x + stat_w, stat_y + stat_h], fill=GREEN_BG, outline=GREEN_BORDER, width=1)
    draw.text((stat_x + 16, stat_y + 8), "STATUS: CONFIRMED", fill=GREEN, font=get_font(15, bold=True))

    # =========================================================================
    # 4. DUAL QR CODE BLOCKS (GPS MAPS NAVIGATION + GATE ENTRY DETAILS)
    # =========================================================================
    qr_y = bar_y + bar_h + 12
    box_w = (WIDTH - 2 * margin - 48) // 2
    box_h = 280

    # BOX 1: VENUE LOCATION QR (GOOGLE MAPS)
    b1_x = margin + 16
    draw.rectangle([b1_x, qr_y, b1_x + box_w, qr_y + box_h], fill=(255, 255, 255), outline=BORDER, width=1)
    draw.rectangle([b1_x, qr_y, b1_x + box_w, qr_y + 36], fill=(241, 245, 249))
    draw.text((b1_x + 16, qr_y + 9), "1. VENUE LOCATION QR CODE (MAPS)", fill=NAVY, font=f_qr_title)

    venue_map_url = "https://maps.google.com/?q=Trilochan+Resorts+Sundarpada+Bhubaneswar"
    qr1 = qrcode.QRCode(version=1, box_size=5, border=1)
    qr1.add_data(venue_map_url)
    qr1.make(fit=True)
    qr1_img = qr1.make_image(fill_color="black", back_color="white").convert("RGB")
    qr1_img = qr1_img.resize((150, 150), Image.Resampling.LANCZOS)
    im.paste(qr1_img, (b1_x + 18, qr_y + 48))

    b1_t_x = b1_x + 185
    draw.text((b1_t_x, qr_y + 48), "SCAN FOR GPS NAVIGATION", fill=GOLD, font=get_font(13, bold=True))
    draw.text((b1_t_x, qr_y + 70), "Venue Name:", fill=TEXT_MUTED, font=f_label)
    draw.text((b1_t_x, qr_y + 88), "Trilochan Resorts", fill=NAVY, font=get_font(15, bold=True))
    draw.text((b1_t_x, qr_y + 110), "Address Details:", fill=TEXT_MUTED, font=f_label)
    draw.text((b1_t_x, qr_y + 128), "Plot No.629, Ebaranga, Jatni Rd,", fill=NAVY_LIGHT, font=f_sub)
    draw.text((b1_t_x, qr_y + 146), "Sundarpada, Bhubaneswar - 751002", fill=NAVY_LIGHT, font=f_sub)
    draw.text((b1_t_x, qr_y + 168), "Landmark: Near Champaty Petrol Pump", fill=TEXT_MUTED, font=get_font(12, bold=False))
    
    draw.text((b1_x + 18, qr_y + 220), "Scan with Google Lens or Camera for instant turn-by-turn navigation.", fill=TEXT_MUTED, font=get_font(11, bold=False))
    draw.text((b1_x + 18, qr_y + 244), "Direct Link: maps.google.com/?q=Trilochan+Resorts", fill=GOLD, font=get_font(11, bold=False))

    # BOX 2: GATE TICKET DETAILS & ENTRY QR
    b2_x = b1_x + box_w + 16
    draw.rectangle([b2_x, qr_y, b2_x + box_w, qr_y + box_h], fill=(255, 255, 255), outline=BORDER, width=1)
    draw.rectangle([b2_x, qr_y, b2_x + box_w, qr_y + 36], fill=(241, 245, 249))
    draw.text((b2_x + 16, qr_y + 9), "2. GATE ENTRY & DETAILS QR CODE", fill=NAVY, font=f_qr_title)

    verify_url = f"https://mrunmayaleads.onrender.com/api/tickets/verify-pass/{sl_clean}"
    qr2_text = (
        f"MRUNMAYA ASSOCIATES - OFFICIAL PASS\n"
        f"Event: {clean_title}\n"
        f"Pass ID: {sl_clean}\n"
        f"Attendee: {clean_name}\n"
        f"Mobile: {clean_mob}\n"
        f"Date: {clean_date}\n"
        f"Timing: 7:00 PM TO 10:00 PM\n"
        f"Persons: {qty_int}\n"
        f"Amount: Rs. {rate_str}/- (PAID)\n"
        f"Helpline: {org_phones}\n"
        f"Gate URL: {verify_url}"
    )
    qr2 = qrcode.QRCode(version=1, box_size=5, border=1)
    qr2.add_data(qr2_text)
    qr2.make(fit=True)
    qr2_img = qr2.make_image(fill_color="black", back_color="white").convert("RGB")
    qr2_img = qr2_img.resize((150, 150), Image.Resampling.LANCZOS)
    im.paste(qr2_img, (b2_x + 18, qr_y + 48))

    b2_t_x = b2_x + 185
    draw.text((b2_t_x, qr_y + 48), "SCAN AT GATE ADMISSION", fill=GREEN, font=get_font(13, bold=True))
    draw.text((b2_t_x, qr_y + 70), "Pass ID / Ref:", fill=TEXT_MUTED, font=f_label)
    draw.text((b2_t_x, qr_y + 88), sl_clean, fill=NAVY, font=get_font(15, bold=True))
    draw.text((b2_t_x, qr_y + 110), "Primary Attendee:", fill=TEXT_MUTED, font=f_label)
    draw.text((b2_t_x, qr_y + 128), f"{clean_name[:22]}", fill=NAVY_LIGHT, font=get_font(14, bold=True))
    draw.text((b2_t_x, qr_y + 148), f"Persons Allowed: {qty_int} Guest(s)", fill=NAVY_LIGHT, font=f_sub)
    draw.text((b2_t_x, qr_y + 168), f"Amount Paid: Rs.{rate_str}/- (PAID)", fill=GREEN, font=get_font(13, bold=True))

    draw.text((b2_x + 18, qr_y + 220), "Show this QR at the gate counter. Security scanner validates pass instantly.", fill=TEXT_MUTED, font=get_font(11, bold=False))
    draw.text((b2_x + 18, qr_y + 244), f"Gate Verification Desk: mrunmayaleads.onrender.com", fill=GOLD, font=get_font(11, bold=False))

    # =========================================================================
    # 5. ATTENDEE & BOOKING INFORMATION TABLE
    # =========================================================================
    tbl_y = qr_y + box_h + 12
    draw.rectangle([margin + 16, tbl_y, WIDTH - margin - 16, tbl_y + 36], fill=NAVY)
    draw.text((margin + 28, tbl_y + 8), "ATTENDEE & RESERVATION DETAILS", fill=(255, 255, 255), font=f_h2)

    tbl_b_y = tbl_y + 36
    tbl_h = 168
    draw.rectangle([margin + 16, tbl_b_y, WIDTH - margin - 16, tbl_b_y + tbl_h], fill=(255, 255, 255), outline=BORDER, width=1)

    col_w = (WIDTH - 2 * margin - 32) // 2
    row_h = 56
    details = [
        ("Attendee Name", clean_name, "Registered Mobile", f"+91 {clean_mob}"),
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
        draw.text((margin + 28, r_y + 8), lbl1, fill=TEXT_MUTED, font=f_label)
        draw.text((margin + 28, r_y + 27), v1, fill=NAVY, font=f_val)

        # Col 2
        c2_x = margin + 16 + col_w
        draw.line([c2_x, r_y, c2_x, r_y + row_h], fill=BORDER, width=1)
        draw.text((c2_x + 18, r_y + 8), lbl2, fill=TEXT_MUTED, font=f_label)
        v2_color = GREEN if "PAID" in v2 else NAVY
        draw.text((c2_x + 18, r_y + 27), v2, fill=v2_color, font=f_val)

    # =========================================================================
    # 6. INCLUSIONS & FESTIVE HIGHLIGHTS STRIP
    # =========================================================================
    inc_y = tbl_b_y + tbl_h + 10
    draw.rectangle([margin + 16, inc_y, WIDTH - margin - 16, inc_y + 54], fill=GOLD_LIGHT, outline=GOLD_BORDER, width=1)
    draw.text((margin + 28, inc_y + 8), "PASS INCLUSIONS & FESTIVE HIGHLIGHTS:", fill=GOLD, font=get_font(13, bold=True))
    draw.text((margin + 28, inc_y + 29), "[+] Live DJ Dandia Arena   |   [+] Free Dandia Sticks at Gate   |   [+] Mega Lucky Draw Coupon   |   [+] Kids & Family Zone", fill=NAVY_LIGHT, font=get_font(12, bold=False))

    # =========================================================================
    # 7. IMPORTANT INSTRUCTIONS FOR ENTRY
    # =========================================================================
    t_y = inc_y + 64
    t_h = 138
    draw.rectangle([margin + 16, t_y, WIDTH - margin - 16, t_y + t_h], fill=BG_SECTION, outline=BORDER, width=1)
    draw.text((margin + 28, t_y + 8), "IMPORTANT INSTRUCTIONS FOR ENTRY (PLEASE READ):", fill=NAVY, font=f_terms_h)
    
    rules = [
        "1. Please carry this printed A4 ticket (or digital voucher) along with a valid Govt ID proof at the entrance gate.",
        "2. Each pass has a unique QR code. Once scanned at admission desk, it cannot be reused by another guest.",
        "3. Entry gates open strictly at 06:30 PM. Show timings are 7:00 PM TO 10:00 PM.",
        "4. Traditional Dandia / Ethnic attire warmly encouraged. Dandia sticks will be issued at the gate admission counters.",
        f"5. Organizers Helpline: +91 {org_phones} | Email: {org_email}"
    ]
    for r_idx, rule in enumerate(rules):
        draw.text((margin + 28, t_y + 32 + r_idx * 20), rule, fill=NAVY_LIGHT, font=f_terms)

    # =========================================================================
    # 8. ORGANIZER DESK & AUTHORIZED STAMP
    # =========================================================================
    foot_y = t_y + t_h + 10
    draw.line([margin + 16, foot_y, WIDTH - margin - 16, foot_y], fill=BORDER, width=1)

    # Left: Organizer contact desk
    draw.text((margin + 20, foot_y + 6), "MRUNMAYA ASSOCIATES | OFFICIAL ORGANIZER DESK", fill=NAVY, font=get_font(13, bold=True))
    draw.text((margin + 20, foot_y + 24), "Plot No.629, Ebaranga, Jatni Rd, Sundarpada, Bhubaneswar, Odisha 751002", fill=TEXT_MUTED, font=f_foot)
    draw.text((margin + 20, foot_y + 40), f"Helpline: +91 {org_phones} | Email: {org_email}", fill=GOLD, font=f_foot)

    # Right: Stamp Seal Box
    stamp_w, stamp_h = 240, 54
    stamp_x = WIDTH - margin - stamp_w - 16
    stamp_y = foot_y + 4
    draw.rectangle([stamp_x, stamp_y, stamp_x + stamp_w, stamp_y + stamp_h], outline=GOLD_BORDER, width=1)
    draw.text((stamp_x + 14, stamp_y + 6), "AUTHORIZED ENTRY PASS", fill=GOLD, font=get_font(12, bold=True))
    draw.text((stamp_x + 14, stamp_y + 22), "MRUNMAYA ASSOCIATES", fill=NAVY, font=get_font(13, bold=True))
    draw.text((stamp_x + 14, stamp_y + 38), "[OK] Digitally Signed & Verified", fill=GREEN, font=get_font(11, bold=False))

    # =========================================================================
    # 9. PERFORATED SCISSOR CUT LINE (TEAR-OFF DIVIDER)
    # =========================================================================
    cut_y = foot_y + 64
    badge_txt = "✂   TEAR HERE AT ENTRY GATE (ORGANIZER GATE TOKEN / COUNTERFOIL)   ✂"
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
    draw.text(((WIDTH - s_w) // 2, cut_y + 14), sub_help, fill=TEXT_MUTED, font=f_sub_h)

    # =========================================================================
    # 10. BOTTOM TEAR-OFF TOKEN (ORGANIZER GATE COUNTERFOIL)
    # =========================================================================
    token_y = cut_y + 36
    token_h = HEIGHT - margin - token_y - 8
    token_w = WIDTH - 2 * margin - 32
    token_x = margin + 16

    # Token Background & Perforated/Dashed Border
    draw.rectangle([token_x, token_y, token_x + token_w, token_y + token_h], fill=TOKEN_BG, outline=GOLD_BORDER, width=2)
    # Inner subtle dashed border for voucher aesthetic
    draw_dashed_line(draw, (token_x + 4, token_y + 4), (token_x + token_w - 4, token_y + 4), fill=BORDER_DASH, width=1)
    draw_dashed_line(draw, (token_x + 4, token_y + token_h - 4), (token_x + token_w - 4, token_y + token_h - 4), fill=BORDER_DASH, width=1)
    draw_dashed_line(draw, (token_x + 4, token_y + 4), (token_x + 4, token_y + token_h - 4), fill=BORDER_DASH, width=1)
    draw_dashed_line(draw, (token_x + token_w - 4, token_y + 4), (token_x + token_w - 4, token_y + token_h - 4), fill=BORDER_DASH, width=1)

    # Token Header Strip
    th_h = 42
    draw.rectangle([token_x, token_y, token_x + token_w, token_y + th_h], fill=NAVY)
    draw.text((token_x + 18, token_y + 10), "ORGANIZER GATE ENTRY TOKEN / COUNTERFOIL", fill=(254, 240, 138), font=f_token_h)
    draw.text((token_x + 550, token_y + 13), "SECURITY ADMISSION COPY (TEAR & RETAIN AT GATE)", fill=(203, 213, 225), font=get_font(12, bold=True))

    # Token 3-Column Layout:
    # Col A: Attendee & Pass Details (w: 440)
    # Col B: Mini Gate QR Scanner (w: 260)
    # Col C: Gate Marshal Verification Box (w: 390)

    colA_x = token_x + 16
    colA_y = token_y + th_h + 10
    
    # Token Pass ID Highlight Box
    draw.rectangle([colA_x, colA_y, colA_x + 430, colA_y + 42], fill=GOLD_LIGHT, outline=GOLD_BORDER, width=1)
    draw.text((colA_x + 12, colA_y + 10), "TOKEN PASS NO:", fill=GOLD, font=get_font(12, bold=True))
    draw.text((colA_x + 135, colA_y + 8), sl_clean, fill=NAVY, font=get_font(20, bold=True))

    # Token Key Fields
    token_fields = [
        ("Event Name:", clean_title[:45]),
        ("Attendee Name:", clean_name[:26]),
        ("Mobile Number:", f"+91 {clean_mob}"),
        ("Date & Timing:", f"{clean_date}  |  7 PM - 10 PM"),
        ("Persons Allowed:", f"{qty_int} Guest(s)"),
        ("Payment Status:", f"Rs. {rate_str}/- PAID ({payment_mode})"),
        ("Venue Location:", "Trilochan Resorts, Sundarpada, BBSR"),
        ("Organizer Support:", f"+91 {org_phones}")
    ]

    for f_idx, (f_lbl, f_val_text) in enumerate(token_fields):
        line_y = colA_y + 50 + f_idx * 21
        draw.text((colA_x, line_y), f_lbl, fill=TEXT_MUTED, font=get_font(12, bold=False))
        v_col = GREEN if "PAID" in f_val_text else NAVY
        draw.text((colA_x + 125, line_y), f_val_text, fill=v_col, font=get_font(12, bold=True))

    # Vertical divider 1
    div1_x = colA_x + 445
    draw.line([div1_x, token_y + th_h, div1_x, token_y + token_h - 26], fill=BORDER, width=1)

    # Col B: Quick Gate Token QR Code
    colB_x = div1_x + 16
    colB_y = token_y + th_h + 12
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
    qr3_img = qr3_img.resize((145, 145), Image.Resampling.LANCZOS)
    im.paste(qr3_img, (colB_x + 10, colB_y + 24))

    draw.text((colB_x + 15, colB_y + 175), "GATE SCANNER QR", fill=GREEN, font=get_font(12, bold=True))
    draw.text((colB_x + 10, colB_y + 194), "Scan & Detach Token", fill=TEXT_MUTED, font=get_font(11, bold=False))

    # Vertical divider 2
    div2_x = colB_x + 185
    draw.line([div2_x, token_y + th_h, div2_x, token_y + token_h - 26], fill=BORDER, width=1)

    # Col C: Gate Marshal Verification & Signature Desk
    colC_x = div2_x + 16
    colC_y = token_y + th_h + 12
    draw.text((colC_x, colC_y), "GATE MARSHAL ADMISSION DESK", fill=NAVY, font=get_font(13, bold=True))

    box_m_y = colC_y + 20
    box_m_w = token_w - (colC_x - token_x) - 16
    box_m_h = 195
    draw.rectangle([colC_x, box_m_y, colC_x + box_m_w, box_m_y + box_m_h], fill=(255, 255, 255), outline=BORDER, width=1)

    draw.text((colC_x + 12, box_m_y + 8), "[ ✓ ] TICKET VERIFIED & ALLOWED", fill=GREEN, font=get_font(12, bold=True))
    draw.text((colC_x + 12, box_m_y + 28), "Admitted Guests: ______ Person(s)", fill=NAVY_LIGHT, font=get_font(12, bold=False))
    draw.text((colC_x + 12, box_m_y + 48), "Dandia Sticks Issued: [ YES / NO ]", fill=NAVY_LIGHT, font=get_font(12, bold=False))
    draw.text((colC_x + 12, box_m_y + 68), "Admission Time: ______ : ______ PM", fill=NAVY_LIGHT, font=get_font(12, bold=False))
    draw.text((colC_x + 12, box_m_y + 90), "Security Officer Sign / Gate Stamp:", fill=TEXT_MUTED, font=get_font(11, bold=False))
    
    # Stamp / Sign box area
    stamp_inner_y = box_m_y + 114
    stamp_inner_h = 70
    draw.rectangle([colC_x + 12, stamp_inner_y, colC_x + box_m_w - 12, stamp_inner_y + stamp_inner_h], fill=(248, 250, 252), outline=BORDER, width=1)
    draw.text((colC_x + 24, stamp_inner_y + 26), "[ OFFICIAL GATE STAMP & SIGNATURE ]", fill=TEXT_MUTED, font=get_font(12, bold=False))

    # Token Bottom Instruction Strip
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
