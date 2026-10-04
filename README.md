# MRUNMAYA ASSOCIATES - Family Dandia Night 2026 & Digital Services Portal

Official Web Portal, Event Ticket Booking Platform & Organizer Dashboard for **MRUNMAYA ASSOCIATES & TRILOCHAN RESORTS**.

---

## 🌟 Key Features

1. **Instant Online Ticket Booking**:
   - Single Ticket: **₹299/-** (Family Dandia Night 2026 - Melody Night Show)
   - Dates: 17/10/2026 (Saturday) & 18/10/2026 (Sunday)
   - Timings: 7:00 PM TO 10:00 PM
   - Venue: Trilochan Resorts, Sundarpada, Bhubaneswar (Near Champaty Petrol Pump)
   - Inclusions: Unlimited Food | Unlimited Mocktails | Live Music & Singing | Lucky Draw (LED TV, Micro Oven, Induction)

2. **Official Razorpay Live Payment Gateway**:
   - Direct bank integration with live Razorpay credentials.
   - Customers can pay via **Google Pay, PhonePe, Paytm, BHIM UPI, Debit/Credit Cards & NetBanking**.
   - Zero-loading delay architecture with fail-safe fallback.

3. **Automated Ticket & Sequential Gate Pass Issuance**:
   - Sequential ticket numbering starting from **`Dandia/2026/301`**.
   - Generates official entry pass with dynamic gate validation QR code.
   - 1-click Download Ticket PNG and WhatsApp delivery.

4. **Organizer Admin Dashboard**:
   - Access via Admin PIN: `1234`
   - Real-time Ticket Booking Register, Financial Ledger, and Export to CSV.
   - Event Manager: Add, Edit, and Delete events with custom poster uploads.
   - Razorpay API credentials manager and GST tax configuration.

---

## 🚀 How to Run Locally

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Start Server
```bash
python main.py
```
Or double-click `start.bat`.

Open your browser at: `http://localhost:8000`

---

## 🌐 How to Upload to GitHub & Host on Render

### Step 1: Upload to GitHub
1. Create a new repository on GitHub (e.g. `mrunmaya-associates-website`).
2. Open terminal inside this folder and run:
```bash
git init
git add .
git commit -m "Official release with Live Razorpay & Dandia Night 2026"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

### Step 2: Deploy on Render (Free / Web Service)
1. Log in to [Render.com](https://render.com).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository.
4. Settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click **Deploy Web Service**!
   Your site will be live instantly with the pre-configured live Razorpay keys and Dandia 2026 poster.

---

## 🔑 Pre-Configured Credentials

- **Razorpay Key ID**: `rzp_live_TjiX5CotSd0Lrk`
- **Razorpay Key Secret**: `Z67kRRLfcjLXoHcAA1ndrs37`
- **Admin PIN**: `1234`
- **Helpline Contact**: `7008955582, 9938866544`
