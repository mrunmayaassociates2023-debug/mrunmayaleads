/**
 * MRUNMAY DIGITAL SERVICE - Client Application Logic
 * Automated Lead Capture & WhatsApp Integration
 */

// Global State
let appSettings = {
    owner_phone: "919876543210",
    business_name: "MRUNMAY DIGITAL SERVICE",
    tagline: "Your Trusted Partner for Digital, Citizen & Financial Services",
    address: "At/Po- Main Road, Near Bus Stand, Odisha - PIN 751001",
    email: "mrunmay.service@gmail.com",
    working_hours: "08:00 AM - 09:00 PM (All 7 Days)"
};

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
    loadSettings();
    initHeroForm();
    initModalForm();
    initSolarCalculator();
    initLoanCalculator();
    initQuickFilter();
    setupMobileMenu();
});

// 1. Fetch Dynamic Business Settings
async function loadSettings() {
    try {
        const res = await fetch("/api/settings");
        if (res.ok) {
            const data = await res.json();
            if (data.success && data.settings) {
                appSettings = { ...appSettings, ...data.settings };
                updateUIWithSettings();
            }
        }
    } catch (e) {
        console.log("Running in offline/standalone mode, using default/local settings.");
        const localSettings = localStorage.getItem("mrunmay_settings");
        if (localSettings) {
            try {
                appSettings = { ...appSettings, ...JSON.parse(localSettings) };
                updateUIWithSettings();
            } catch (err) {}
        }
    }
}

function updateUIWithSettings() {
    // Update displayed phone and links
    document.querySelectorAll(".business-name-text").forEach(el => el.textContent = appSettings.business_name);
    document.querySelectorAll(".business-address-text").forEach(el => el.textContent = appSettings.address);
    document.querySelectorAll(".business-phone-text").forEach(el => el.textContent = formatPhone(appSettings.owner_phone));
    
    // Update direct call buttons
    document.querySelectorAll(".direct-call-link").forEach(el => {
        el.href = `tel:+${cleanPhoneNumber(appSettings.owner_phone)}`;
    });

    // Update floating WhatsApp button
    const floatWa = document.getElementById("floatingWhatsAppBtn");
    if (floatWa) {
        floatWa.href = `https://wa.me/${cleanPhoneNumber(appSettings.owner_phone)}?text=${encodeURIComponent('🙏 Namaskar ' + appSettings.business_name + '! I want to inquire about your services.')}`;
    }
}

function cleanPhoneNumber(phone) {
    let cleaned = (phone || "").toString().replace(/\D/g, "");
    if (cleaned.length === 10) {
        cleaned = "91" + cleaned;
    }
    return cleaned;
}

function formatPhone(phone) {
    let clean = cleanPhoneNumber(phone);
    if (clean.startsWith("91") && clean.length === 12) {
        return `+91 ${clean.slice(2, 7)} ${clean.slice(7)}`;
    }
    return `+${clean}`;
}

// 2. Open / Close Enquiry Modal
function openEnquiryModal(service = "General Service", specificService = "") {
    const modal = document.getElementById("enquiryModal");
    const serviceSelect = document.getElementById("modalServiceSelect");
    const specificInput = document.getElementById("modalSpecificService");
    
    if (serviceSelect) {
        // Set value if exists, else add option
        let found = false;
        for (let i = 0; i < serviceSelect.options.length; i++) {
            if (serviceSelect.options[i].value.toLowerCase().includes(service.toLowerCase())) {
                serviceSelect.selectedIndex = i;
                found = true;
                break;
            }
        }
        if (!found) {
            serviceSelect.value = service;
        }
    }
    
    if (specificInput) {
        specificInput.value = specificService || "";
    }

    const modalTitle = document.getElementById("modalTitle");
    if (modalTitle) {
        modalTitle.innerHTML = `Enquiry for <span class="text-blue-600">${service}</span>`;
    }

    if (modal) {
        modal.style.display = "flex";
        modal.classList.remove("hidden");
        modal.classList.add("flex");
        document.body.classList.add("overflow-hidden");
        
        // Focus first field
        setTimeout(() => {
            const nameField = document.getElementById("modalCustomerName");
            if (nameField) nameField.focus();
        }, 100);
    }
}

function closeEnquiryModal() {
    const modal = document.getElementById("enquiryModal");
    if (modal) {
        modal.style.display = "none";
        modal.classList.add("hidden");
        modal.classList.remove("flex");
        document.body.classList.remove("overflow-hidden");
    }
}

// 3. Lead Submission & Automatic WhatsApp Connection
async function processLeadSubmission(payload, submitBtn) {
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg> Saving Number & Connecting WhatsApp...
    `;

    let leadId = "MDS-" + Math.floor(1000 + Math.random() * 9000);
    let whatsappUrl = "";
    const cleanCustomerPhone = payload.phone.replace(/\D/g, "");

    try {
        // First try server API
        const response = await fetch("/api/enquiry", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const result = await response.json();
            leadId = "#MDS-" + result.lead_id;
            whatsappUrl = result.whatsapp_url;
        } else {
            throw new Error("Server response error");
        }
    } catch (err) {
        // Submit to Netlify Forms so Netlify captures and saves the lead in dashboard
        try {
            const netlifyData = new URLSearchParams({
                "form-name": "enquiries",
                "name": payload.name,
                "phone": cleanCustomerPhone,
                "service": payload.service,
                "specific_service": payload.specific_service || "",
                "location": payload.location || "",
                "message": payload.message || ""
            });
            await fetch("/", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: netlifyData.toString()
            });
        } catch (netErr) {
            console.log("Netlify form post skipped offline", netErr);
        }

        // Fallback to client-side localStorage so data is NEVER lost!
        const existingLeads = JSON.parse(localStorage.getItem("mrunmay_leads") || "[]");
        const newRecord = {
            id: existingLeads.length + 1,
            name: payload.name,
            phone: cleanCustomerPhone,
            service: payload.service,
            specific_service: payload.specific_service || "",
            location: payload.location || "",
            message: payload.message || "",
            status: "New",
            created_at: new Date().toISOString().replace("T", " ").substring(0, 19)
        };
        existingLeads.unshift(newRecord);
        localStorage.setItem("mrunmay_leads", JSON.stringify(existingLeads));
        leadId = "#MDS-LOC" + newRecord.id;

        // Build WhatsApp URL locally
        const targetOwner = cleanPhoneNumber(appSettings.owner_phone);
        const msgLines = [
            `🙏 *Namaskar ${appSettings.business_name}!*`,
            `I have an enquiry regarding *${payload.service}*.`,
            ``,
            `👤 *Customer Name:* ${payload.name}`,
            `📱 *Mobile:* ${cleanCustomerPhone}`,
            payload.specific_service ? `📋 *Service Required:* ${payload.specific_service}` : "",
            payload.location ? `📍 *Location:* ${payload.location}` : "",
            payload.message ? `💬 *Notes:* ${payload.message}` : "",
            ``,
            `_Reference ID: ${leadId}_`,
            `Please share the details and charges. Thank you!`
        ].filter(Boolean);

        whatsappUrl = `https://wa.me/${targetOwner}?text=${encodeURIComponent(msgLines.join("\n"))}`;
    }

    // Show Success Modal with instant countdown & WhatsApp launch
    showSuccessPopup(leadId, payload.name, cleanCustomerPhone, payload.service, whatsappUrl);

    // Reset button
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalBtnText;
}

function showSuccessPopup(leadId, name, phone, service, whatsappUrl) {
    closeEnquiryModal();

    const popup = document.getElementById("successModal");
    if (!popup) {
        // If modal doesn't exist, open directly
        window.open(whatsappUrl, "_blank");
        return;
    }

    document.getElementById("successLeadId").textContent = leadId;
    document.getElementById("successCustomerInfo").textContent = `${name} (${phone})`;
    document.getElementById("successService").textContent = service;
    
    const waBtn = document.getElementById("successWhatsAppBtn");
    if (waBtn) {
        waBtn.href = whatsappUrl;
    }

    popup.style.display = "flex";
    popup.classList.remove("hidden");
    popup.classList.add("flex");

    // Automatically trigger WhatsApp in 1.5 seconds so user sees their saved ID first!
    let secondsLeft = 2;
    const countdownEl = document.getElementById("waCountdown");
    if (countdownEl) countdownEl.textContent = secondsLeft;

    const timer = setInterval(() => {
        secondsLeft--;
        if (countdownEl) countdownEl.textContent = secondsLeft;
        if (secondsLeft <= 0) {
            clearInterval(timer);
            // Open WhatsApp
            window.open(whatsappUrl, "_blank");
        }
    }, 1000);
}

function closeSuccessModal() {
    const popup = document.getElementById("successModal");
    if (popup) {
        popup.style.display = "none";
        popup.classList.add("hidden");
        popup.classList.remove("flex");
    }
}

// 4. Form Handlers
function initHeroForm() {
    const form = document.getElementById("heroEnquiryForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector("button[type='submit']");
        
        const payload = {
            name: form.querySelector("#heroName").value.trim(),
            phone: form.querySelector("#heroPhone").value.trim(),
            service: form.querySelector("#heroService").value,
            specific_service: form.querySelector("#heroSpecific") ? form.querySelector("#heroSpecific").value.trim() : "",
            location: form.querySelector("#heroLocation") ? form.querySelector("#heroLocation").value.trim() : "",
            message: "Enquiry submitted via Homepage Quick Form."
        };

        if (payload.phone.replace(/\D/g, "").length < 10) {
            alert("Please enter a valid 10-digit mobile number so we can reach you!");
            return;
        }

        await processLeadSubmission(payload, submitBtn);
        form.reset();
    });
}

function initModalForm() {
    const form = document.getElementById("modalEnquiryForm");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector("button[type='submit']");
        
        const payload = {
            name: form.querySelector("#modalCustomerName").value.trim(),
            phone: form.querySelector("#modalCustomerPhone").value.trim(),
            service: form.querySelector("#modalServiceSelect").value,
            specific_service: form.querySelector("#modalSpecificService").value.trim(),
            location: form.querySelector("#modalCustomerLocation").value.trim(),
            message: form.querySelector("#modalCustomerMessage").value.trim()
        };

        if (payload.phone.replace(/\D/g, "").length < 10) {
            alert("Please enter a valid 10-digit mobile number!");
            return;
        }

        await processLeadSubmission(payload, submitBtn);
        form.reset();
    });
}

// 5. Interactive Solar Subsidy & Savings Calculator
function initSolarCalculator() {
    const billSlider = document.getElementById("solarBillSlider");
    const billDisplay = document.getElementById("solarBillDisplay");
    const kwDisplay = document.getElementById("solarKwDisplay");
    const subsidyDisplay = document.getElementById("solarSubsidyDisplay");
    const monthlySavingsDisplay = document.getElementById("solarMonthlySavings");
    const annualSavingsDisplay = document.getElementById("solarAnnualSavings");
    const applySolarBtn = document.getElementById("applySolarCalcBtn");

    if (!billSlider) return;

    function updateSolar() {
        const bill = parseInt(billSlider.value);
        if (billDisplay) billDisplay.textContent = `₹${bill.toLocaleString("en-IN")}`;

        // Recommendation logic (PM Surya Ghar Muft Bijli Yojana)
        let kw = 1;
        let subsidy = 30000;
        let savingsMonthly = 0;

        if (bill <= 1200) {
            kw = 1;
            subsidy = 30000;
            savingsMonthly = Math.min(bill, 1100);
        } else if (bill <= 2500) {
            kw = 2;
            subsidy = 60000;
            savingsMonthly = Math.min(bill, 2200);
        } else {
            kw = Math.min(10, Math.ceil(bill / 1200));
            subsidy = 78000; // Max ceiling for PM Surya Ghar
            savingsMonthly = Math.min(bill, kw * 1100);
        }

        if (kwDisplay) kwDisplay.textContent = `${kw} kW Rooftop System`;
        if (subsidyDisplay) subsidyDisplay.textContent = `₹${subsidy.toLocaleString("en-IN")}`;
        if (monthlySavingsDisplay) monthlySavingsDisplay.textContent = `₹${savingsMonthly.toLocaleString("en-IN")}/mo`;
        if (annualSavingsDisplay) annualSavingsDisplay.textContent = `₹${(savingsMonthly * 12).toLocaleString("en-IN")}/yr`;

        if (applySolarBtn) {
            applySolarBtn.onclick = () => {
                openEnquiryModal("Solar Service", `PM Surya Ghar Yojana - ${kw}kW System (Current Bill: ₹${bill}/mo, Subsidy: ₹${subsidy})`);
            };
        }
    }

    billSlider.addEventListener("input", updateSolar);
    updateSolar();
}

// 6. Interactive Loan EMI Calculator
function initLoanCalculator() {
    const amountSlider = document.getElementById("loanAmountSlider");
    const rateSlider = document.getElementById("loanRateSlider");
    const tenureSlider = document.getElementById("loanTenureSlider");

    const amountDisplay = document.getElementById("loanAmountDisplay");
    const rateDisplay = document.getElementById("loanRateDisplay");
    const tenureDisplay = document.getElementById("loanTenureDisplay");

    const emiDisplay = document.getElementById("loanEmiDisplay");
    const totalInterestDisplay = document.getElementById("loanTotalInterestDisplay");
    const totalPayableDisplay = document.getElementById("loanTotalPayableDisplay");
    const applyLoanBtn = document.getElementById("applyLoanCalcBtn");

    if (!amountSlider) return;

    function updateLoan() {
        const principal = parseFloat(amountSlider.value);
        const annualRate = parseFloat(rateSlider.value);
        const months = parseInt(tenureSlider.value);

        if (amountDisplay) amountDisplay.textContent = `₹${principal.toLocaleString("en-IN")}`;
        if (rateDisplay) rateDisplay.textContent = `${annualRate.toFixed(1)}% p.a.`;
        if (tenureDisplay) tenureDisplay.textContent = `${months} Months (${(months / 12).toFixed(1)} Yrs)`;

        const monthlyRate = annualRate / 12 / 100;
        let emi = 0;
        if (monthlyRate > 0) {
            emi = (principal * monthlyRate * Math.pow(1 + monthlyRate, months)) / (Math.pow(1 + monthlyRate, months) - 1);
        } else {
            emi = principal / months;
        }

        const totalPayable = emi * months;
        const totalInterest = totalPayable - principal;

        if (emiDisplay) emiDisplay.textContent = `₹${Math.round(emi).toLocaleString("en-IN")}`;
        if (totalInterestDisplay) totalInterestDisplay.textContent = `₹${Math.round(totalInterest).toLocaleString("en-IN")}`;
        if (totalPayableDisplay) totalPayableDisplay.textContent = `₹${Math.round(totalPayable).toLocaleString("en-IN")}`;

        if (applyLoanBtn) {
            applyLoanBtn.onclick = () => {
                openEnquiryModal("Loan Service", `Loan ₹${principal.toLocaleString("en-IN")} for ${months} months @ ${annualRate}% (Est. EMI: ₹${Math.round(emi)}/mo)`);
            };
        }
    }

    amountSlider.addEventListener("input", updateLoan);
    rateSlider.addEventListener("input", updateLoan);
    tenureSlider.addEventListener("input", updateLoan);
    updateLoan();
}

// 7. Quick Filter for Service Tabs (All / Printing / CSC / Loan / Solar)
function initQuickFilter() {
    const tabButtons = document.querySelectorAll(".service-filter-tab");
    const serviceCards = document.querySelectorAll(".service-item-card");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => {
                b.classList.remove("bg-blue-600", "text-white", "shadow-md");
                b.classList.add("bg-white", "text-slate-700", "border-slate-200");
            });

            btn.classList.remove("bg-white", "text-slate-700", "border-slate-200");
            btn.classList.add("bg-blue-600", "text-white", "shadow-md");

            const filterCategory = btn.getAttribute("data-filter");

            serviceCards.forEach(card => {
                const cardCategory = card.getAttribute("data-category");
                if (filterCategory === "all" || cardCategory === filterCategory) {
                    card.classList.remove("hidden");
                } else {
                    card.classList.add("hidden");
                }
            });
        });
    });
}

// 8. Mobile Menu
function setupMobileMenu() {
    const menuBtn = document.getElementById("mobileMenuBtn");
    const mobileMenu = document.getElementById("mobileMenu");
    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener("click", () => {
            mobileMenu.classList.toggle("hidden");
        });
        
        // Close menu when clicking link
        mobileMenu.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                mobileMenu.classList.add("hidden");
            });
        });
    }
}
