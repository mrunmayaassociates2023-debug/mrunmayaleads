import os
import re
import qrcode
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_OFFICIAL = os.path.join(BASE_DIR, "dandia_ticket_template_official_2026.jpg")
TEMPLATE_SUN = os.path.join(BASE_DIR, "dandia_ticket_template_sun_299.png")
TEMPLATE_DEFAULT = os.path.join(BASE_DIR, "dandia_ticket_template_299.png")

def get_font(font_name, size):
    paths = [
        os.path.join(r"C:\Windows\Fonts", font_name),
        os.path.join(r"C:\Windows\Fonts", "arialbd.ttf"),
        os.path.join(r"C:\Windows\Fonts", "arial.ttf")
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

def generate_ticket_image(
    pass_id="Dandia/2026/301", 
    customer_name="Attendee", 
    phone="7992993433", 
    address="Sundarpada, Bhubaneswar", 
    date_selected="18/10/2026 (Sunday)", 
    amount=299,
    base_url="",
    event_title="FAMILY DANDIA NIGHT 2026",
    venue="Trilochan Resorts, Sundarpada"
):
    template_file = TEMPLATE_OFFICIAL if os.path.exists(TEMPLATE_OFFICIAL) else (
        TEMPLATE_SUN if os.path.exists(TEMPLATE_SUN) else TEMPLATE_DEFAULT
    )
    if not os.path.exists(template_file):
        raise FileNotFoundError(f"Template not found at {template_file}")
        
    im = Image.open(template_file).convert("RGB")
    draw = ImageDraw.Draw(im)
    
    font_sl_stub = get_font("arialbd.ttf", 11)
    font_sl_tr = get_font("arialbd.ttf", 9)
    font_val = get_font("arialbd.ttf", 11)
    font_rs = get_font("arialbd.ttf", 16)
    
    # 1. Format clean serial number as Dandia/2026/301
    sl_clean = format_serial_number(pass_id)
    
    # Clean fields
    clean_name = str(customer_name).strip()[:24] if customer_name else "Valued Guest"
    clean_addr = str(address).strip()[:24] if address else "Sundarpada, BBSR"
    clean_mob = str(phone).strip()[:15] if phone else "7992993433"
    clean_venue = str(venue).strip()[:35] if venue else "Trilochan Resorts, Sundarpada"
    clean_title = str(event_title).strip()[:35] if event_title else "FAMILY DANDIA NIGHT 2026"
    
    try:
        amt_float = float(amount)
        rate_str = f"{amt_float:.2f}"
    except Exception:
        rate_str = str(amount)

    # 2. Stub Sl.No (top-left) - sits right on underline
    draw.text((105, 23), sl_clean, fill=(200, 0, 0), font=font_sl_stub)
    
    # 3. Main Ticket Sl.No (top-right) - sits right on underline
    draw.text((948, 33), sl_clean, fill=(200, 0, 0), font=font_sl_tr)
    
    # 4. Customer Details on Left Stub
    # Name - line 1 dots
    draw.text((72, 187), clean_name, fill=(10, 20, 100), font=font_val)
    # Address - line 3 dots
    draw.text((80, 241), clean_addr, fill=(10, 20, 100), font=font_val)
    # Mob - line 5 dots
    draw.text((62, 280), clean_mob, fill=(10, 20, 100), font=font_val)
    
    # 5. Rs Box: Rate / Total Amount
    draw.text((80, 313), f"{rate_str}/-", fill=(200, 0, 0), font=font_rs)

    # 6. RIGHT SIDE RED BOX (X: 877-1013, Y: 230-337) -> Stamped QR Code with Customer Details
    # Covers the red rectangle cleanly with white card and 102x102 QR
    draw.rectangle([877, 230, 1013, 337], fill=(255, 255, 255), outline=(0, 0, 0), width=1)
    
    verify_url = f"https://mrunmayaleads.onrender.com/api/tickets/verify-pass/{sl_clean}"
    qr_data = (
        f"MRUNMAYA ASSOCIATES | {clean_title.upper()}\n"
        f"TICKET NO: {sl_clean}\n"
        f"NAME: {clean_name}\n"
        f"MOB: {clean_mob}\n"
        f"ADDRESS: {clean_addr}\n"
        f"DATE: {date_selected}\n"
        f"VENUE: {clean_venue}\n"
        f"AMOUNT: Rs.{rate_str}\n"
        f"STATUS: VERIFIED & CONFIRMED\n"
        f"GATE VERIFY: {verify_url}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=3,
        border=1
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    # Fit into the red box
    qr_resized = qr_img.resize((102, 102), Image.Resampling.LANCZOS)
    
    # Position centered inside [877, 230, 1013, 337]
    im.paste(qr_resized, (894, 232))
    
    return im

if __name__ == "__main__":
    t = generate_ticket_image(
        pass_id="Dandia/2026/015",
        customer_name="Priyanka Mohapatra",
        phone="9861234567",
        address="Sundarpada, BBSR",
        date_selected="18/10/2026 (Sunday)",
        amount=299
    )
    t.save("test_official_ticket_final.png")
    print("Generated test_official_ticket_final.png successfully!")
