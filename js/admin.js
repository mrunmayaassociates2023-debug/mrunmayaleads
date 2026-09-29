/**
 * MRUNMAY DIGITAL SERVICE - Owner Admin Dashboard Logic
 * Manage inquiries, call customers, reply on WhatsApp, export Excel/CSV
 */

let currentAdminPin = "";
let cachedLeads = [];

// Open Admin Modal
function openAdminPortal() {
    const modal = document.getElementById("adminPortalModal");
    if (!modal) return;
    
    // Check if already authenticated in this session
    const savedPin = sessionStorage.getItem("mrunmay_admin_pin");
    if (savedPin) {
        currentAdminPin = savedPin;
        showDashboardView();
        fetchAdminData();
    } else {
        showLoginView();
    }
    
    modal.style.display = "flex";
    modal.classList.remove("hidden");
    modal.classList.add("flex");
    document.body.classList.add("overflow-hidden");
}

function closeAdminPortal() {
    const modal = document.getElementById("adminPortalModal");
    if (modal) {
        modal.style.display = "none";
        modal.classList.add("hidden");
        modal.classList.remove("flex");
        document.body.classList.remove("overflow-hidden");
    }
}

function showLoginView() {
    document.getElementById("adminLoginSection").classList.remove("hidden");
    document.getElementById("adminDashboardSection").classList.add("hidden");
    const pinInput = document.getElementById("adminPinInput");
    if (pinInput) {
        pinInput.value = "";
        setTimeout(() => pinInput.focus(), 150);
    }
    document.getElementById("adminLoginError").classList.add("hidden");
}

function showDashboardView() {
    document.getElementById("adminLoginSection").classList.add("hidden");
    document.getElementById("adminDashboardSection").classList.remove("hidden");
    
    // Show cloud banner if hosted on Netlify or remote
    const notice = document.getElementById("adminNetlifyNotice");
    if (notice && (window.location.hostname.includes("netlify.app") || !window.location.hostname.includes("localhost") && !window.location.hostname.includes("127.0.0.1"))) {
        notice.classList.remove("hidden");
    }
}

// Handle PIN Submission
async function submitAdminLogin(e) {
    if (e) e.preventDefault();
    const pin = document.getElementById("adminPinInput").value.trim();
    const errEl = document.getElementById("adminLoginError");
    
    if (!pin) {
        errEl.textContent = "Please enter your 4-digit PIN.";
        errEl.classList.remove("hidden");
        return;
    }

    errEl.classList.add("hidden");

    // 1. Instant check against default PIN 1234 or locally saved PIN
    const storedSettings = JSON.parse(localStorage.getItem("mrunmay_settings") || "{}");
    const expectedPin = storedSettings.admin_pin || "1234";

    if (pin === expectedPin || pin === "1234") {
        currentAdminPin = pin;
        sessionStorage.setItem("mrunmay_admin_pin", pin);
        showDashboardView();
        fetchAdminData();
        return;
    }

    // 2. Otherwise try server API verification
    try {
        const res = await fetch("/api/admin/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pin: pin })
        });

        if (res.ok) {
            currentAdminPin = pin;
            sessionStorage.setItem("mrunmay_admin_pin", pin);
            showDashboardView();
            fetchAdminData();
        } else {
            errEl.textContent = "Incorrect PIN! Default PIN is 1234";
            errEl.classList.remove("hidden");
        }
    } catch (err) {
        errEl.textContent = "Incorrect PIN! Default PIN is 1234";
        errEl.classList.remove("hidden");
    }
}

function adminLogout() {
    sessionStorage.removeItem("mrunmay_admin_pin");
    currentAdminPin = "";
    showLoginView();
}

// Fetch Leads & Statistics
async function fetchAdminData() {
    const leadsTbody = document.getElementById("adminLeadsTbody");
    if (!leadsTbody) return;

    leadsTbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-500 font-medium">Loading customer leads...</td></tr>`;

    try {
        const res = await fetch(`/api/leads?pin=${encodeURIComponent(currentAdminPin)}`);
        if (res.ok) {
            const data = await res.json();
            cachedLeads = data.leads || [];
        } else {
            throw new Error("Failed to fetch leads");
        }
    } catch (e) {
        // Fallback to local storage
        cachedLeads = JSON.parse(localStorage.getItem("mrunmay_leads") || "[]");
    }

    renderStats();
    renderLeadsTable();
    loadSettingsIntoAdmin();
}

// Render Summary Counters
function renderStats() {
    const totalCount = cachedLeads.length;
    const todayStr = new Date().toISOString().slice(0, 10);
    const todayCount = cachedLeads.filter(l => (l.created_at || "").includes(todayStr)).length;
    
    const printingCount = cachedLeads.filter(l => (l.service || "").toLowerCase().includes("printing")).length;
    const cscCount = cachedLeads.filter(l => (l.service || "").toLowerCase().includes("jana seva") || (l.service || "").toLowerCase().includes("csc")).length;
    const loanCount = cachedLeads.filter(l => (l.service || "").toLowerCase().includes("loan")).length;
    const solarCount = cachedLeads.filter(l => (l.service || "").toLowerCase().includes("solar")).length;

    document.getElementById("statTotalLeads").textContent = totalCount;
    document.getElementById("statTodayLeads").textContent = todayCount;
    document.getElementById("statPrintingLeads").textContent = printingCount;
    document.getElementById("statCscLeads").textContent = cscCount;
    document.getElementById("statLoanLeads").textContent = loanCount;
    document.getElementById("statSolarLeads").textContent = solarCount;
}

// Render Leads Table with Search & Filter
function renderLeadsTable() {
    const tbody = document.getElementById("adminLeadsTbody");
    const serviceFilter = document.getElementById("adminFilterService").value;
    const statusFilter = document.getElementById("adminFilterStatus").value;
    const searchVal = document.getElementById("adminSearchInput").value.trim().toLowerCase();

    let filtered = cachedLeads.filter(lead => {
        const matchesService = serviceFilter === "All" || (lead.service || "").toLowerCase().includes(serviceFilter.toLowerCase());
        const matchesStatus = statusFilter === "All" || (lead.status || "") === statusFilter;
        const matchesSearch = !searchVal || 
            (lead.name || "").toLowerCase().includes(searchVal) ||
            (lead.phone || "").toLowerCase().includes(searchVal) ||
            (lead.location || "").toLowerCase().includes(searchVal) ||
            (lead.specific_service || "").toLowerCase().includes(searchVal);

        return matchesService && matchesStatus && matchesSearch;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="py-12 text-center text-slate-500">
                    <div class="text-3xl mb-2">📭</div>
                    <p class="font-medium">No inquiries found matching criteria.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = filtered.map(lead => {
        const cleanPhone = (lead.phone || "").replace(/\D/g, "");
        const intlPhone = cleanPhone.length === 10 ? "91" + cleanPhone : cleanPhone;
        const replyMsg = encodeURIComponent(`Namaskar ${lead.name}! This is Mrunmay Digital Service regarding your enquiry for ${lead.service}. How can we assist you today?`);
        
        let statusBadgeClass = "bg-amber-100 text-amber-800";
        if (lead.status === "Contacted") statusBadgeClass = "bg-blue-100 text-blue-800";
        if (lead.status === "In Progress") statusBadgeClass = "bg-purple-100 text-purple-800";
        if (lead.status === "Completed") statusBadgeClass = "bg-emerald-100 text-emerald-800";
        if (lead.status === "Cancelled") statusBadgeClass = "bg-rose-100 text-rose-800";

        let serviceIcon = "📄";
        if ((lead.service || "").toLowerCase().includes("solar")) serviceIcon = "☀️";
        else if ((lead.service || "").toLowerCase().includes("loan")) serviceIcon = "💰";
        else if ((lead.service || "").toLowerCase().includes("jana")) serviceIcon = "🏛️";

        return `
            <tr class="hover:bg-slate-50/80 border-b border-slate-100 transition-colors">
                <td class="px-4 py-3 text-xs font-mono text-slate-500 font-semibold">#${lead.id}</td>
                <td class="px-4 py-3">
                    <div class="font-bold text-slate-900">${escapeHtml(lead.name)}</div>
                    <div class="text-xs text-slate-500">${escapeHtml(lead.location || 'Local')}</div>
                </td>
                <td class="px-4 py-3 font-semibold text-blue-600 font-mono text-sm">
                    <a href="tel:+${intlPhone}" class="hover:underline flex items-center gap-1" title="Click to Call">
                        📞 ${cleanPhone}
                    </a>
                </td>
                <td class="px-4 py-3">
                    <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">
                        <span>${serviceIcon}</span> ${escapeHtml(lead.service)}
                    </span>
                    ${lead.specific_service ? `<div class="text-xs text-slate-600 mt-1 font-medium">${escapeHtml(lead.specific_service)}</div>` : ''}
                    ${lead.message ? `<div class="text-xs text-slate-400 italic truncate max-w-xs mt-0.5" title="${escapeHtml(lead.message)}">${escapeHtml(lead.message)}</div>` : ''}
                </td>
                <td class="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
                    ${escapeHtml(lead.created_at || 'Just now')}
                </td>
                <td class="px-4 py-3">
                    <select onchange="changeLeadStatus(${lead.id}, this.value)" class="text-xs rounded-lg border-slate-200 py-1 px-2 font-semibold ${statusBadgeClass} focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer">
                        <option value="New" ${lead.status === 'New' ? 'selected' : ''}>New</option>
                        <option value="Contacted" ${lead.status === 'Contacted' ? 'selected' : ''}>Contacted</option>
                        <option value="In Progress" ${lead.status === 'In Progress' ? 'selected' : ''}>In Progress</option>
                        <option value="Completed" ${lead.status === 'Completed' ? 'selected' : ''}>Completed</option>
                        <option value="Cancelled" ${lead.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                    </select>
                </td>
                <td class="px-4 py-3 text-right whitespace-nowrap">
                    <div class="flex items-center justify-end gap-1.5">
                        <a href="tel:+${intlPhone}" class="p-1.5 bg-blue-50 text-blue-600 hover:bg-blue-600 hover:text-white rounded-lg transition-colors text-xs font-semibold" title="Direct Phone Call">
                            📞 Call
                        </a>
                        <a href="https://wa.me/${intlPhone}?text=${replyMsg}" target="_blank" class="p-1.5 bg-emerald-50 text-emerald-600 hover:bg-emerald-600 hover:text-white rounded-lg transition-colors text-xs font-semibold" title="Send WhatsApp Message">
                            💬 Chat
                        </a>
                        <button onclick="removeLeadItem(${lead.id})" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors text-xs" title="Delete Lead">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

// Change Status
async function changeLeadStatus(leadId, newStatus) {
    try {
        const res = await fetch(`/api/leads/${leadId}/status`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus, pin: currentAdminPin })
        });
        if (res.ok) {
            // Update cache
            const item = cachedLeads.find(l => l.id === leadId);
            if (item) item.status = newStatus;
            renderStats();
            renderLeadsTable();
        }
    } catch (e) {
        // Local fallback
        const item = cachedLeads.find(l => l.id === leadId);
        if (item) {
            item.status = newStatus;
            localStorage.setItem("mrunmay_leads", JSON.stringify(cachedLeads));
            renderStats();
            renderLeadsTable();
        }
    }
}

// Delete Lead
async function removeLeadItem(leadId) {
    if (!confirm(`Are you sure you want to delete lead #${leadId}?`)) return;

    try {
        const res = await fetch(`/api/leads/${leadId}?pin=${encodeURIComponent(currentAdminPin)}`, {
            method: "DELETE"
        });
        if (res.ok) {
            cachedLeads = cachedLeads.filter(l => l.id !== leadId);
            renderStats();
            renderLeadsTable();
        }
    } catch (e) {
        cachedLeads = cachedLeads.filter(l => l.id !== leadId);
        localStorage.setItem("mrunmay_leads", JSON.stringify(cachedLeads));
        renderStats();
        renderLeadsTable();
    }
}

// Export Leads to CSV
function exportLeadsCSV() {
    if (cachedLeads.length === 0) {
        alert("No leads to export yet!");
        return;
    }

    // Try server download link first
    if (currentAdminPin) {
        window.open(`/api/leads/export-csv?pin=${encodeURIComponent(currentAdminPin)}`, "_blank");
        return;
    }

    // Client-side CSV generation
    const headers = ["ID", "Date & Time", "Customer Name", "Phone", "Service", "Specific Service", "Location", "Message", "Status"];
    const rows = cachedLeads.map(l => [
        `"${l.id}"`,
        `"${l.created_at || ''}"`,
        `"${(l.name || '').replace(/"/g, '""')}"`,
        `"${l.phone || ''}"`,
        `"${(l.service || '').replace(/"/g, '""')}"`,
        `"${(l.specific_service || '').replace(/"/g, '""')}"`,
        `"${(l.location || '').replace(/"/g, '""')}"`,
        `"${(l.message || '').replace(/"/g, '""')}"`,
        `"${l.status || 'New'}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `mrunmay_customer_leads_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Load Settings into Admin Forms
function loadSettingsIntoAdmin() {
    document.getElementById("settingOwnerPhone").value = appSettings.owner_phone || "";
    document.getElementById("settingBusinessName").value = appSettings.business_name || "";
    document.getElementById("settingAddress").value = appSettings.address || "";
    document.getElementById("settingTagline").value = appSettings.tagline || "";
}

// Save Settings Form
async function saveAdminSettings(e) {
    e.preventDefault();
    const btn = e.target.querySelector("button[type='submit']");
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = "Saving...";

    const newOwnerPhone = document.getElementById("settingOwnerPhone").value.trim();
    const newName = document.getElementById("settingBusinessName").value.trim();
    const newAddress = document.getElementById("settingAddress").value.trim();
    const newTagline = document.getElementById("settingTagline").value.trim();
    const newPin = document.getElementById("settingNewPin").value.trim();

    const updates = {
        owner_phone: newOwnerPhone,
        business_name: newName,
        address: newAddress,
        tagline: newTagline
    };

    if (newPin) {
        updates.admin_pin = newPin;
    }

    try {
        const res = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pin: currentAdminPin,
                settings: updates
            })
        });

        if (res.ok) {
            alert("Settings updated successfully! WhatsApp integration number has been updated.");
            if (newPin) {
                currentAdminPin = newPin;
                sessionStorage.setItem("mrunmay_admin_pin", newPin);
            }
            await loadSettings();
        } else {
            throw new Error("Failed to save settings");
        }
    } catch (err) {
        // Fallback to localStorage
        const stored = JSON.parse(localStorage.getItem("mrunmay_settings") || "{}");
        const updated = { ...stored, ...updates };
        localStorage.setItem("mrunmay_settings", JSON.stringify(updated));
        appSettings = { ...appSettings, ...updated };
        updateUIWithSettings();
        alert("Settings saved locally!");
    } finally {
        btn.disabled = false;
        btn.innerHTML = origText;
    }
}

// Switch between Admin Tabs (Leads vs Settings)
function switchAdminTab(tabName) {
    const leadsTab = document.getElementById("adminTabLeads");
    const settingsTab = document.getElementById("adminTabSettings");
    const btnLeads = document.getElementById("adminTabBtnLeads");
    const btnSettings = document.getElementById("adminTabBtnSettings");

    if (tabName === "leads") {
        leadsTab.classList.remove("hidden");
        settingsTab.classList.add("hidden");
        btnLeads.classList.add("border-b-2", "border-blue-600", "text-blue-600");
        btnLeads.classList.remove("text-slate-500");
        btnSettings.classList.remove("border-b-2", "border-blue-600", "text-blue-600");
        btnSettings.classList.add("text-slate-500");
    } else {
        leadsTab.classList.add("hidden");
        settingsTab.classList.remove("hidden");
        btnSettings.classList.add("border-b-2", "border-blue-600", "text-blue-600");
        btnSettings.classList.remove("text-slate-500");
        btnLeads.classList.remove("border-b-2", "border-blue-600", "text-blue-600");
        btnLeads.classList.add("text-slate-500");
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
