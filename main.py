import os
import io
import csv
import urllib.parse
from fastapi import FastAPI, HTTPException, Depends, Query, Response, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from database import (
    init_db,
    save_lead,
    get_all_leads,
    update_lead_status,
    delete_lead,
    get_settings,
    update_settings,
    get_statistics,
    get_all_events,
    save_event,
    delete_event,
    save_ticket,
    get_all_tickets,
    update_ticket_status,
    get_ticket_by_pass_id,
    get_next_sequential_pass_info,
    save_payment,
    get_all_payments,
    get_all_sponsors,
    save_sponsor,
    delete_sponsor,
    toggle_sponsor_status,
    purge_expired_cancelled_tickets
)
from razorpay_client import RazorpayClient

# Initialize database
init_db()

app = FastAPI(
    title="MRUNMAYA ASSOCIATES Portal",
    description="Event Ticket Booking, Citizen Services & Digital Solutions",
    version="2.0.0"
)

# Enable CORS for local testing and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Models
class EnquiryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., min_length=10, max_length=15)
    service: str = Field(..., min_length=2)
    specific_service: Optional[str] = ""
    location: Optional[str] = ""
    message: Optional[str] = ""

class StatusUpdateRequest(BaseModel):
    status: str
    pin: str

class SettingsUpdateRequest(BaseModel):
    pin: str
    settings: Dict[str, Any]

class AdminAuthRequest(BaseModel):
    pin: str

class TicketBookingRequest(BaseModel):
    pass_id: Optional[str] = ""
    event_id: Optional[int] = 1
    event_title: str
    customer_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = ""
    city: Optional[str] = ""
    date_selected: Optional[str] = ""
    quantity: int = Field(1, ge=1, le=100)
    rate_per_ticket: int = 299
    total_amount: int = 299
    utr_reference: Optional[str] = ""
    payment_status: Optional[str] = "Paid"
    gst_amount: Optional[float] = 0.0
    gst_percent: Optional[float] = 0.0

class GeneralPaymentRequest(BaseModel):
    service_type: str = Field(..., min_length=2)
    customer_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10, max_length=15)
    amount: float = Field(..., ge=1)
    payment_mode: Optional[str] = "Shop UPI QR Scanner"
    sub_method: Optional[str] = "UPI"
    transaction_ref: Optional[str] = ""
    status: Optional[str] = "Success"
    pass_id: Optional[str] = ""
    details: Optional[Dict[str, Any]] = None

class RazorpayOrderCreateRequest(BaseModel):
    amount: float = Field(..., ge=1)
    event_id: Optional[int] = None
    event_title: Optional[str] = "Digital Service Payment"
    service_type: Optional[str] = "Service Payment"
    customer_name: str
    phone: str
    date_selected: Optional[str] = ""
    quantity: Optional[int] = 1

class RazorpayVerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    event_id: Optional[int] = None
    event_title: Optional[str] = ""
    service_type: Optional[str] = "Service Payment"
    customer_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=10, max_length=15)
    email: Optional[str] = ""
    city: Optional[str] = ""
    date_selected: Optional[str] = ""
    quantity: Optional[int] = 1
    rate_per_ticket: Optional[int] = 299
    total_amount: float = Field(..., ge=1)
    gst_amount: Optional[float] = 0.0
    gst_percent: Optional[float] = 0.0

class TicketStatusUpdateRequest(BaseModel):
    status: str
    pin: str

class EventRequest(BaseModel):
    title: str = Field(..., min_length=2)
    rate: int = Field(299, ge=0)
    dates: str
    timings: str
    venue: str
    highlights: Optional[str] = ""
    contacts: Optional[str] = ""
    poster_image: Optional[str] = ""
    enabled: Optional[int] = 1
    event_id: Optional[int] = None
    pin: str

class SponsorRequest(BaseModel):
    name: str = Field(..., min_length=2)
    category: Optional[str] = "Event Partner"
    logo_url: Optional[str] = ""
    website_url: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    display_order: Optional[int] = 0
    enabled: Optional[int] = 1
    sponsor_id: Optional[int] = None
    pin: str

def verify_admin_pin(pin: str):
    settings = get_settings()
    correct_pin = settings.get("admin_pin", "1234")
    if pin != correct_pin:
        raise HTTPException(status_code=401, detail="Invalid Admin PIN")
    return True

@app.post("/api/enquiry")
def submit_enquiry(req: EnquiryRequest):
    clean_phone = "".join(filter(str.isdigit, req.phone))
    if len(clean_phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number. Please enter a valid 10-digit number.")
    
    lead_id, created_at = save_lead(
        name=req.name,
        phone=clean_phone,
        service=req.service,
        specific_service=req.specific_service or "",
        location=req.location or "",
        message=req.message or ""
    )
    
    settings = get_settings()
    owner_phone = settings.get("owner_phone", "917992993433")
    clean_owner = "".join(filter(str.isdigit, owner_phone))
    if len(clean_owner) == 10:
        clean_owner = "91" + clean_owner
        
    business_name = settings.get("business_name", "MRUNMAYA ASSOCIATES")
    
    msg_lines = [
        f"Hello {business_name}!",
        f"I would like to enquire about: *{req.service}*.",
        "",
        f"Name: {req.name.strip()}",
        f"Mobile: {clean_phone}",
    ]
    
    if req.specific_service and req.specific_service.strip():
        msg_lines.append(f"Sub-Service: {req.specific_service.strip()}")
    if req.location and req.location.strip():
        msg_lines.append(f"Location: {req.location.strip()}")
    if req.message and req.message.strip():
        msg_lines.append(f"Notes: {req.message.strip()}")
        
    msg_lines.append("")
    msg_lines.append(f"_Ref ID: #MA-{lead_id}_")
    msg_lines.append("Please provide details and charges. Thank you!")
    
    full_message = "\n".join(msg_lines)
    encoded_msg = urllib.parse.quote(full_message)
    whatsapp_url = f"https://wa.me/{clean_owner}?text={encoded_msg}"
    
    return {
        "success": True,
        "lead_id": lead_id,
        "created_at": created_at,
        "whatsapp_url": whatsapp_url
    }

# ================= RAZORPAY PAYMENT GATEWAY APIS =================
@app.post("/api/razorpay/create-order")
def create_razorpay_order_endpoint(req: RazorpayOrderCreateRequest):
    clean_phone = "".join(filter(str.isdigit, req.phone))
    if len(clean_phone) < 10:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number.")
    
    settings = get_settings()
    key_id = (settings.get("razorpay_key_id") or "rzp_live_TjiX5CotSd0Lrk").strip()
    key_secret = (settings.get("razorpay_key_secret") or "Z67kRRLfcjLXoHcAA1ndrs37").strip()
    
    client = RazorpayClient(key_id=key_id, key_secret=key_secret)
    notes = {
        "customer_name": req.customer_name,
        "phone": clean_phone,
        "event_id": str(req.event_id) if req.event_id else "",
        "event_title": req.event_title or "",
        "service_type": req.service_type or req.event_title or "Service Payment",
        "date_selected": req.date_selected or "",
        "quantity": str(req.quantity or 1)
    }
    receipt = f"rcpt_{clean_phone[-4:]}_{int(req.amount)}"
    
    try:
        order = client.create_order(amount_in_rupees=req.amount, receipt=receipt, notes=notes)
        return {
            "success": True,
            "order_id": order.get("order_id"),
            "amount": order.get("amount"),
            "currency": order.get("currency", "INR"),
            "key_id": order.get("key_id"),
            "mock": order.get("mock", False),
            "simulated": order.get("mock", False),
            "message": order.get("message", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/razorpay/verify-payment")
def verify_razorpay_payment_endpoint(req: RazorpayVerifyPaymentRequest):
    clean_phone = "".join(filter(str.isdigit, req.phone))
    if len(clean_phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number.")
    
    settings = get_settings()
    key_id = (settings.get("razorpay_key_id") or "rzp_live_TjiX5CotSd0Lrk").strip()
    key_secret = (settings.get("razorpay_key_secret") or "Z67kRRLfcjLXoHcAA1ndrs37").strip()
    
    client = RazorpayClient(key_id=key_id, key_secret=key_secret)
    
    # Cryptographic Signature Verification
    is_valid = client.verify_payment_signature(
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=400, 
            detail="Payment signature verification failed! No ticket issued. If money was deducted, contact support."
        )
    
    owner_phone = settings.get("owner_phone", "917992993433")
    clean_owner = "".join(filter(str.isdigit, owner_phone))
    if len(clean_owner) == 10:
        clean_owner = "91" + clean_owner

    is_ticket = (req.event_id is not None and req.event_id > 0) or ("ticket" in (req.service_type or "").lower()) or ("dandia" in (req.event_title or "").lower())

    if is_ticket:
        # Signature is Verified Genuine -> Save Confirmed Ticket in Database (auto-logs to payments table)
        ticket_id, official_pass_id, created_at = save_ticket(
            pass_id=None,
            event_id=req.event_id or 1,
            event_title=req.event_title or "Family Dandia Night 2026 - Melody Show",
            customer_name=req.customer_name,
            phone=clean_phone,
            email=req.email or "",
            city=req.city or "Bhubaneswar",
            date_selected=req.date_selected or "17/10/2026 (Saturday)",
            quantity=req.quantity or 1,
            rate_per_ticket=req.rate_per_ticket or 299,
            total_amount=int(req.total_amount),
            utr_reference=f"RZP: {req.razorpay_payment_id}",
            payment_status="Paid",
            razorpay_order_id=req.razorpay_order_id,
            razorpay_payment_id=req.razorpay_payment_id,
            razorpay_signature=req.razorpay_signature,
            gst_amount=float(req.gst_amount or 0.0),
            gst_percent=float(req.gst_percent or 0.0)
        )

        msg_lines = [
            f"🎫 *ENTRY TICKET CONFIRMATION - MRUNMAYA ASSOCIATES*",
            f"Event: *{req.event_title or 'Family Dandia Night 2026'}*",
            f"Ticket Sl.No: *{official_pass_id}*",
            f"Name: *{req.customer_name}*",
            f"Phone: {clean_phone}",
            f"Tickets: *{req.quantity or 1} Person(s)*",
            f"Date: {req.date_selected or '17/10/2026 (Saturday)'}",
            f"Amount Paid: ₹{req.total_amount}",
            f"Payment ID: {req.razorpay_payment_id}",
            "",
            "✅ Verified Online Payment. Please present your digital ticket or printout at the entrance gate. Enjoy the show!"
        ]
        encoded_msg = urllib.parse.quote("\n".join(msg_lines))
        whatsapp_url = f"https://wa.me/{clean_owner}?text={encoded_msg}"

        ticket_obj = {
            "id": ticket_id,
            "pass_id": official_pass_id,
            "event_id": req.event_id or 1,
            "event_title": req.event_title or "Family Dandia Night 2026",
            "customer_name": req.customer_name,
            "phone": clean_phone,
            "city": req.city or "Bhubaneswar",
            "date_selected": req.date_selected or "17/10/2026 (Saturday)",
            "quantity": req.quantity or 1,
            "rate_per_ticket": req.rate_per_ticket or 299,
            "total_amount": req.total_amount,
            "utr_reference": f"RZP: {req.razorpay_payment_id}",
            "payment_status": "Paid",
            "booking_status": "Confirmed",
            "created_at": created_at
        }

        return {
            "success": True,
            "ticket_id": ticket_id,
            "pass_id": official_pass_id,
            "created_at": created_at,
            "whatsapp_url": whatsapp_url,
            "ticket": ticket_obj
        }
    else:
        # General service payment verified via Razorpay
        row_id, payment_id, created_at = save_payment(
            service_type=req.service_type or "General Service Payment",
            customer_name=req.customer_name,
            phone=clean_phone,
            amount=req.total_amount,
            payment_mode="Razorpay",
            sub_method="Online Gateway",
            transaction_ref=req.razorpay_payment_id,
            status="Success",
            payment_id=req.razorpay_payment_id,
            order_id=req.razorpay_order_id,
            details={"email": req.email, "city": req.city}
        )

        msg_lines = [
            f"💳 *ONLINE PAYMENT CONFIRMATION - MRUNMAYA ASSOCIATES*",
            f"Payment ID: *{req.razorpay_payment_id}*",
            f"Service: *{req.service_type or 'General Service'}*",
            f"Name: *{req.customer_name}*",
            f"Phone: {clean_phone}",
            f"Amount Paid: ₹{req.total_amount}",
            "",
            "✅ Verified Online Gateway Payment. Thank you for choosing MRUNMAYA ASSOCIATES!"
        ]
        encoded_msg = urllib.parse.quote("\n".join(msg_lines))
        whatsapp_url = f"https://wa.me/{clean_owner}?text={encoded_msg}"

        return {
            "success": True,
            "payment_id": payment_id,
            "created_at": created_at,
            "whatsapp_url": whatsapp_url,
            "payment": {
                "id": row_id,
                "payment_id": payment_id,
                "service_type": req.service_type,
                "customer_name": req.customer_name,
                "amount": req.total_amount,
                "status": "Success",
                "created_at": created_at
            }
        }

# ================= GENERAL PAYMENTS RECORDING API =================
@app.post("/api/payments")
def record_general_payment(req: GeneralPaymentRequest):
    clean_phone = "".join(filter(str.isdigit, req.phone))
    if len(clean_phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number.")

    row_id, payment_id, created_at = save_payment(
        service_type=req.service_type,
        customer_name=req.customer_name,
        phone=clean_phone,
        amount=req.amount,
        payment_mode=req.payment_mode or "Shop UPI QR Scanner",
        sub_method=req.sub_method or "UPI",
        transaction_ref=req.transaction_ref or "Verified",
        status=req.status or "Success",
        pass_id=req.pass_id or "",
        details=req.details
    )

    settings = get_settings()
    owner_phone = settings.get("owner_phone", "917992993433")
    clean_owner = "".join(filter(str.isdigit, owner_phone))
    if len(clean_owner) == 10:
        clean_owner = "91" + clean_owner

    msg_lines = [
        f"💳 *PAYMENT CONFIRMATION - MRUNMAYA ASSOCIATES*",
        f"Receipt ID: *{payment_id}*",
        f"Service: *{req.service_type}*",
        f"Name: *{req.customer_name}*",
        f"Phone: {clean_phone}",
        f"Amount: *₹{req.amount}*",
        f"Method: {req.payment_mode or 'Shop UPI QR'}",
        f"Ref / UTR: {req.transaction_ref or 'Direct Payment'}",
        "",
        "✅ Payment successfully recorded. Thank you!"
    ]
    encoded_msg = urllib.parse.quote("\n".join(msg_lines))
    whatsapp_url = f"https://wa.me/{clean_owner}?text={encoded_msg}"

    return {
        "success": True,
        "payment_id": payment_id,
        "created_at": created_at,
        "whatsapp_url": whatsapp_url
    }

# ================= TICKET BOOKING APIS =================
@app.post("/api/tickets")
def create_ticket(req: TicketBookingRequest, pin: Optional[str] = Query(None)):
    clean_phone = "".join(filter(str.isdigit, req.phone))
    if len(clean_phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid mobile number.")

    settings = get_settings()
    rzp_enabled = settings.get("razorpay_enabled", "1") == "1"
    correct_pin = settings.get("admin_pin", "1234")

    # If razorpay is enabled and user is not an authenticated admin, disallow manual creation
    if rzp_enabled and (not pin or pin != correct_pin):
        raise HTTPException(
            status_code=403, 
            detail="Direct manual booking is disabled. Entry tickets can only be generated through verified Razorpay online payment."
        )

    ticket_id, official_pass_id, created_at = save_ticket(
        pass_id=req.pass_id,
        event_id=req.event_id,
        event_title=req.event_title,
        customer_name=req.customer_name,
        phone=clean_phone,
        email=req.email or "",
        city=req.city or "",
        date_selected=req.date_selected or "",
        quantity=req.quantity,
        rate_per_ticket=req.rate_per_ticket,
        total_amount=req.total_amount,
        utr_reference=req.utr_reference or "Manual Admin Issue",
        payment_status=req.payment_status or "Paid",
        gst_amount=float(req.gst_amount or 0.0),
        gst_percent=float(req.gst_percent or 0.0)
    )

    owner_phone = settings.get("owner_phone", "917992993433")
    clean_owner = "".join(filter(str.isdigit, owner_phone))
    if len(clean_owner) == 10:
        clean_owner = "91" + clean_owner

    msg_lines = [
        f"🎫 *ENTRY TICKET CONFIRMATION - MRUNMAYA ASSOCIATES*",
        f"Event: *{req.event_title}*",
        f"Ticket Sl.No: *{official_pass_id}*",
        f"Name: *{req.customer_name}*",
        f"Phone: {clean_phone}",
        f"Tickets: *{req.quantity} Person(s)*",
        f"Date: {req.date_selected or '18-19 Oct 2026'}",
        f"Amount Paid: ₹{req.total_amount}",
        f"UTR Ref: {req.utr_reference or 'Online UPI'}",
        "",
        "Please present your digital ticket or printout at the entrance gate. Enjoy the show!"
    ]
    encoded_msg = urllib.parse.quote("\n".join(msg_lines))
    whatsapp_url = f"https://wa.me/{clean_owner}?text={encoded_msg}"

    return {
        "success": True,
        "ticket_id": ticket_id,
        "pass_id": official_pass_id,
        "created_at": created_at,
        "whatsapp_url": whatsapp_url
    }

@app.get("/api/tickets/next-pass")
def get_next_pass():
    next_seq, next_pass_id, total_tickets = get_next_sequential_pass_info()
    return {
        "success": True,
        "next_seq": next_seq,
        "next_pass_id": next_pass_id,
        "total_tickets": total_tickets
    }

@app.get("/api/payment/qr")
def generate_payment_qr(
    amount: Optional[int] = Query(None),
    upi_id: Optional[str] = Query("PPQR01.DOENZS@iob"),
    payee: Optional[str] = Query("MRUNMAYA ASSOCIATES"),
    note: Optional[str] = Query("Family Dandia Night Ticket")
):
    import qrcode
    clean_upi = upi_id.strip() if upi_id else "PPQR01.DOENZS@iob"
    clean_payee = payee.strip() if payee else "MRUNMAYA ASSOCIATES"
    clean_note = note.strip() if note else "Family Dandia Night Ticket"
    
    if amount and amount > 0:
        upi_uri = f"upi://pay?pa={clean_upi}&pn={urllib.parse.quote(clean_payee)}&am={amount}&cu=INR&tn={urllib.parse.quote(clean_note)}"
    else:
        upi_uri = f"upi://pay?pa={clean_upi}&pn={urllib.parse.quote(clean_payee)}&cu=INR"
        
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(upi_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="image/png")

@app.get("/api/tickets")
def list_tickets(pin: str = Query(...), search: Optional[str] = Query(None)):
    verify_admin_pin(pin)
    tickets = get_all_tickets(search=search)
    return {"success": True, "tickets": tickets}

@app.patch("/api/tickets/{ticket_id}/status")
def patch_ticket_status(ticket_id: int, req: TicketStatusUpdateRequest):
    verify_admin_pin(req.pin)
    update_ticket_status(ticket_id, req.status)
    return {"success": True, "message": f"Ticket status updated to {req.status}"}

@app.delete("/api/admin/tickets/purge-cancelled")
def purge_cancelled_tickets_endpoint(pin: str = Query(...)):
    verify_admin_pin(pin)
    count = purge_expired_cancelled_tickets()
    return {"success": True, "purged_count": count, "message": f"Purged {count} expired cancelled tickets."}

@app.get("/api/tickets/verify-pass/{pass_id:path}")
def verify_pass_endpoint(pass_id: str):
    ticket = get_ticket_by_pass_id(pass_id)
    if not ticket:
        return {"success": False, "valid": False, "message": f"Invalid Pass ID '{pass_id}'. No ticket found in register."}
    masked_phone = ticket["phone"][:3] + "XXXX" + ticket["phone"][-3:] if len(ticket.get("phone", "")) >= 10 else ticket.get("phone", "")
    return {
        "success": True,
        "valid": True,
        "ticket": {
            "id": ticket.get("id"),
            "pass_id": ticket.get("pass_id"),
            "event_title": ticket.get("event_title"),
            "customer_name": ticket.get("customer_name"),
            "phone_masked": masked_phone,
            "city": ticket.get("city"),
            "date_selected": ticket.get("date_selected"),
            "quantity": ticket.get("quantity"),
            "total_amount": ticket.get("total_amount"),
            "booking_status": ticket.get("booking_status", "Confirmed"),
            "payment_status": ticket.get("payment_status", "Paid"),
            "created_at": ticket.get("created_at")
        }
    }

@app.post("/api/tickets/{ticket_id}/checkin")
def checkin_ticket_endpoint(ticket_id: int, pin: str = Query(...)):
    verify_admin_pin(pin)
    update_ticket_status(ticket_id, "Admitted")
    return {"success": True, "message": "Attendee Admitted. Status updated to 'Admitted'."}

@app.get("/api/tickets/export-csv")
def export_tickets_csv(pin: str = Query(...)):
    verify_admin_pin(pin)
    tickets = get_all_tickets()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ticket ID", "Pass ID", "Event Title", "Customer Name", "Phone", "Email", "City", "Date Selected", "Qty", "Total Amount", "UTR Ref", "Booking Status", "Date Booked"])
    for t in tickets:
        writer.writerow([
            t.get("id"),
            t.get("pass_id"),
            t.get("event_title"),
            t.get("customer_name"),
            t.get("phone"),
            t.get("email"),
            t.get("city"),
            t.get("date_selected"),
            t.get("quantity"),
            t.get("total_amount"),
            t.get("utr_reference"),
            t.get("booking_status"),
            t.get("created_at")
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mrunmaya_event_tickets.csv"}
    )

@app.get("/api/tickets/{ticket_id:path}/image")
def get_ticket_image(ticket_id: str, download: bool = False):
    from ticket_generator import generate_ticket_image
    ticket = None
    all_tickets = get_all_tickets()
    for t in all_tickets:
        if str(t.get("id")) == str(ticket_id) or str(t.get("pass_id", "")).lower() == str(ticket_id).lower():
            ticket = t
            break
            
    if not ticket:
        ticket = {
            "pass_id": ticket_id if "Dandia" in ticket_id else f"Dandia/2026/{str(ticket_id).zfill(3)}",
            "customer_name": "Valued Guest",
            "phone": "7992993433",
            "city": "Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002",
            "date_selected": "17/10/2026 (Saturday)",
            "total_amount": 299
        }
        
    im = generate_ticket_image(
        pass_id=ticket.get("pass_id", "Dandia/2026/301"),
        customer_name=ticket.get("customer_name", "Attendee"),
        phone=ticket.get("phone", "7992993433"),
        address=ticket.get("city", "Trilochan Resorts, Trilochan Vihar, Sundarpada, Ebaranga, Jatni Road, Bhubaneswar - 751002"),
        date_selected=ticket.get("date_selected", "18/10/2026 (Sunday)"),
        amount=ticket.get("total_amount", 299),
        event_title=ticket.get("event_title", "FAMILY DANDIA NIGHT 2026 - MELODY NIGHT SHOW"),
        quantity=ticket.get("quantity", 1)
    )
    
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    buf.seek(0)
    
    clean_pass = str(ticket.get("pass_id", "301")).replace("/", "_")
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    if download:
        headers["Content-Disposition"] = f'attachment; filename="Family_Dandia_Night_A4_Ticket_{clean_pass}.png"'
        
    return Response(content=buf.getvalue(), media_type="image/png", headers=headers)

# ================= EVENT MANAGEMENT APIS =================
@app.get("/api/events")
def list_events():
    events = get_all_events()
    return {"success": True, "events": events}

@app.post("/api/events/upload-poster")
async def upload_event_poster_endpoint(file: UploadFile = File(...), pin: str = Query(...)):
    verify_admin_pin(pin)
    import time
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext = ".jpg"
    safe_name = f"event_poster_{int(time.time())}{ext}"
    dest_path = os.path.join(STATIC_DIR, safe_name)
    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)
    # Also save a copy to BASE_DIR
    base_dest = os.path.join(BASE_DIR, safe_name)
    with open(base_dest, "wb") as f:
        f.write(content)
    return {"success": True, "poster_url": f"/static/{safe_name}"}

@app.post("/api/events")
def create_or_update_event(req: EventRequest):
    verify_admin_pin(req.pin)
    event_id = save_event(
        title=req.title,
        rate=req.rate,
        dates=req.dates,
        timings=req.timings,
        venue=req.venue,
        highlights=req.highlights or "",
        contacts=req.contacts or "",
        poster_image=req.poster_image or "",
        enabled=req.enabled if req.enabled is not None else 1,
        event_id=req.event_id
    )
    return {"success": True, "event_id": event_id, "message": "Event saved successfully"}

@app.delete("/api/events/{event_id}")
def remove_event(event_id: int, pin: str = Query(...)):
    verify_admin_pin(pin)
    delete_event(event_id)
    return {"success": True, "message": "Event deleted successfully"}

# ================= SPONSORSHIP MANAGEMENT APIS =================
@app.get("/api/sponsors")
def list_public_sponsors():
    sponsors = get_all_sponsors(enabled_only=True)
    return {"success": True, "sponsors": sponsors}

@app.get("/api/admin/sponsors")
def list_admin_sponsors(pin: str = Query(...)):
    verify_admin_pin(pin)
    sponsors = get_all_sponsors(enabled_only=False)
    return {"success": True, "sponsors": sponsors}

@app.post("/api/admin/sponsors")
def create_or_update_sponsor(req: SponsorRequest):
    verify_admin_pin(req.pin)
    sponsor_id = save_sponsor(
        name=req.name,
        category=req.category or "Event Partner",
        logo_url=req.logo_url or "",
        website_url=req.website_url or "",
        phone=req.phone or "",
        email=req.email or "",
        display_order=req.display_order or 0,
        enabled=req.enabled if req.enabled is not None else 1,
        sponsor_id=req.sponsor_id
    )
    return {"success": True, "sponsor_id": sponsor_id, "message": "Sponsor saved successfully"}

@app.delete("/api/admin/sponsors/{sponsor_id}")
def remove_sponsor(sponsor_id: int, pin: str = Query(...)):
    verify_admin_pin(pin)
    delete_sponsor(sponsor_id)
    return {"success": True, "message": "Sponsor removed successfully"}

@app.patch("/api/admin/sponsors/{sponsor_id}/toggle")
def toggle_sponsor(sponsor_id: int, pin: str = Query(...)):
    verify_admin_pin(pin)
    toggle_sponsor_status(sponsor_id)
    return {"success": True, "message": "Sponsor status toggled"}

@app.post("/api/sponsors/upload-logo")
async def upload_sponsor_logo_endpoint(file: UploadFile = File(...), pin: str = Query(...)):
    verify_admin_pin(pin)
    try:
        import time
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
            ext = ".png"
        safe_name = f"sponsor_logo_{int(time.time())}{ext}"
        dest_path = os.path.join(STATIC_DIR, safe_name)
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)
        base_dest = os.path.join(BASE_DIR, safe_name)
        with open(base_dest, "wb") as f:
            f.write(content)
        return JSONResponse(status_code=200, content={"success": True, "logo_url": f"/static/{safe_name}"})
    except Exception as e:
        logger.error(f"Sponsor logo upload error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "detail": str(e)})

# ================= ADMIN LEADS & SETTINGS =================
@app.post("/api/admin/verify")
def admin_verify(req: AdminAuthRequest):
    verify_admin_pin(req.pin)
    return {"success": True, "message": "PIN verified successfully"}

@app.get("/api/leads")
def list_leads(
    pin: str = Query(...),
    service: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    verify_admin_pin(pin)
    leads = get_all_leads(service_filter=service, status_filter=status, search=search)
    return {"success": True, "leads": leads}

@app.patch("/api/leads/{lead_id}/status")
def update_status(lead_id: int, req: StatusUpdateRequest):
    verify_admin_pin(req.pin)
    valid_statuses = ["New", "Contacted", "In Progress", "Completed", "Cancelled"]
    if req.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")
    update_lead_status(lead_id, req.status)
    return {"success": True, "message": f"Status updated to {req.status}"}

@app.delete("/api/leads/{lead_id}")
def remove_lead(lead_id: int, pin: str = Query(...)):
    verify_admin_pin(pin)
    delete_lead(lead_id)
    return {"success": True, "message": "Lead deleted successfully"}

@app.get("/api/stats")
def stats(pin: str = Query(...)):
    verify_admin_pin(pin)
    data = get_statistics()
    return {"success": True, "stats": data}

@app.get("/api/settings")
def public_settings():
    settings = get_settings()
    # Exclude sensitive secrets from public endpoint
    public_dict = {k: v for k, v in settings.items() if k not in ["admin_pin", "razorpay_key_secret"]}
    return {"success": True, "settings": public_dict}

@app.get("/api/admin/settings")
def admin_settings(pin: str = Query(...)):
    verify_admin_pin(pin)
    settings = get_settings()
    return {"success": True, "settings": settings}

@app.get("/api/admin/payments")
def list_admin_payments(
    pin: str = Query(...),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    mode: Optional[str] = Query(None)
):
    verify_admin_pin(pin)
    payments = get_all_payments(search=search, status=status, mode=mode)
    return {"success": True, "payments": payments}

@app.get("/api/admin/payments/export-csv")
def export_payments_csv(pin: str = Query(...)):
    verify_admin_pin(pin)
    payments = get_all_payments()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Payment ID", "Date & Time", "Customer Name", "Phone", "Service / Purpose", "Amount (INR)", "Payment Mode", "Sub-Method", "UTR / RZP Ref", "Status", "Pass ID", "Extra Details"])
    for p in payments:
        writer.writerow([
            p.get("id"),
            p.get("payment_id"),
            p.get("created_at"),
            p.get("customer_name"),
            p.get("phone"),
            p.get("service_type"),
            p.get("amount"),
            p.get("payment_mode"),
            p.get("sub_method"),
            p.get("transaction_ref"),
            p.get("status"),
            p.get("pass_id") or "",
            p.get("details") or ""
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mrunmaya_payments_ledger.csv"}
    )

@app.post("/api/settings")
def save_settings(req: SettingsUpdateRequest):
    verify_admin_pin(req.pin)
    safe_keys = [
        "owner_phone", "business_name", "tagline", "address", "email", 
        "working_hours", "site_config", "upi_id", "payee_name", "qr_image",
        "razorpay_key_id", "razorpay_key_secret", "razorpay_enabled", "payment_enabled",
        "gst_enabled", "gst_percent", "gstin", "gst_type"
    ]
    updates = {k: v for k, v in req.settings.items() if k in safe_keys}
    if "admin_pin" in req.settings and req.settings["admin_pin"].strip():
        updates["admin_pin"] = req.settings["admin_pin"].strip()
    update_settings(updates)
    return {"success": True, "message": "Settings updated successfully"}

@app.get("/api/leads/export-csv")
def export_csv(pin: str = Query(...)):
    verify_admin_pin(pin)
    leads = get_all_leads()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date & Time", "Customer Name", "Phone Number", "Service", "Specific Sub-Service", "Location", "Message", "Status"])
    for l in leads:
        writer.writerow([
            l.get("id"),
            l.get("created_at"),
            l.get("name"),
            l.get("phone"),
            l.get("service"),
            l.get("specific_service"),
            l.get("location"),
            l.get("message"),
            l.get("status")
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=mrunmaya_customer_leads.csv"}
    )

# Static files mount
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    css_dir = os.path.join(STATIC_DIR, "css")
    js_dir = os.path.join(STATIC_DIR, "js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")

def get_index_file():
    for d in [BASE_DIR, STATIC_DIR]:
        fpath = os.path.join(d, "index.html")
        if os.path.isfile(fpath):
            return fpath
    return None

@app.get("/")
def read_root():
    index_path = get_index_file()
    if index_path:
        return FileResponse(index_path)
    return {"message": "MRUNMAYA ASSOCIATES API is Running."}

@app.get("/admin")
def read_admin():
    index_path = get_index_file()
    if index_path:
        return FileResponse(index_path)
    return {"message": "Admin portal loading..."}

@app.get("/download-zip")
def download_project_zip():
    zip_path = os.path.join(BASE_DIR, "mrunmay_website_ready_to_host.zip")
    if os.path.exists(zip_path):
        return FileResponse(
            zip_path, 
            filename="mrunmay_website_ready_to_host.zip", 
            media_type="application/zip"
        )
    raise HTTPException(status_code=404, detail="ZIP file not found")

@app.get("/{filename}")
def read_root_file(filename: str):
    for d in [BASE_DIR, STATIC_DIR]:
        fpath = os.path.join(d, filename)
        if os.path.isfile(fpath):
            return FileResponse(fpath)
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    print("Starting MRUNMAYA ASSOCIATES Server on http://0.0.0.0:8000 ...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
