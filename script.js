// Ma'lumotlar
let data = {
    balance: 0,
    income: 0,
    expense: 0,
    transactions: [],
    cards: [],
    contacts: [],
    messages: []
};

// LocalStorage dan yuklash
function loadData() {
    const saved = localStorage.getItem('financeData');
    if (saved) {
        data = JSON.parse(saved);
    }
}

// LocalStorage ga saqlash
function saveData() {
    localStorage.setItem('financeData', JSON.stringify(data));
}

// Tranzaktsiya qo'shish
function addTransaction() {
    const type = document.querySelector('.btn-type.active').dataset.type;
    const category = document.getElementById('categorySelect').value;
    const amount = parseFloat(document.getElementById('amountInput').value);
    const description = document.getElementById('descriptionInput').value || 'Izohsiz';
    
    if (!amount || amount <= 0) {
        alert('Iltimos, summani kiriting!');
        return;
    }
    
    const transaction = {
        id: Date.now(),
        type: type,
        category: category,
        amount: amount,
        description: description,
        date: new Date().toLocaleString()
    };
    
    data.transactions.unshift(transaction);
    
    if (type === 'income') {
        data.income += amount;
        data.balance += amount;
    } else {
        data.expense += amount;
        data.balance -= amount;
    }
    
    saveData();
    updateUI();
    
    // Formani tozalash
    document.getElementById('amountInput').value = '';
    document.getElementById('descriptionInput').value = '';
    
    // Xabar
    showNotification('✅ Tranzaktsiya qo\'shildi!');
}

// UI yangilash
function updateUI() {
    // Balans
    document.getElementById('totalBalance').textContent = formatNumber(data.balance);
    document.getElementById('totalIncome').textContent = formatNumber(data.income);
    document.getElementById('totalExpense').textContent = formatNumber(data.expense);
    
    // Profil
    document.getElementById('profileIncome').textContent = formatNumber(data.income);
    document.getElementById('profileExpense').textContent = formatNumber(data.expense);
    document.getElementById('profileBalance').textContent = formatNumber(data.balance);
    
    // Tranzaktsiyalar
    renderTransactions();
    renderRecentTransactions();
    renderCards();
    renderContacts();
    renderMessages();
    updateChart();
}

// Format number
function formatNumber(num) {
    return num.toLocaleString('uz-UZ');
}

// Tranzaktsiyalarni render qilish
function renderTransactions() {
    const container = document.getElementById('allTransactions');
    if (data.transactions.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#888;padding:20px;">Hali tranzaktsiyalar yo\'q</p>';
        return;
    }
    
    container.innerHTML = data.transactions.map(t => `
        <div class="transaction-item">
            <div class="left">
                <div class="icon ${t.type}">
                    ${t.type === 'income' ? '💰' : '💸'}
                </div>
                <div class="info">
                    <h4>${t.category}</h4>
                    <p>${t.description} • ${t.date}</p>
                </div>
            </div>
            <div class="amount ${t.type}">
                ${t.type === 'income' ? '+' : '-'} ${formatNumber(t.amount)}
            </div>
        </div>
    `).join('');
}

// So'nggi tranzaktsiyalar
function renderRecentTransactions() {
    const container = document.getElementById('recentTransactions');
    const recent = data.transactions.slice(0, 5);
    
    if (recent.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#888;padding:10px;">Hali tranzaktsiyalar yo\'q</p>';
        return;
    }
    
    container.innerHTML = recent.map(t => `
        <div class="transaction-item">
            <div class="left">
                <div class="icon ${t.type}">
                    ${t.type === 'income' ? '💰' : '💸'}
                </div>
                <div class="info">
                    <h4>${t.category}</h4>
                    <p>${t.description}</p>
                </div>
            </div>
            <div class="amount ${t.type}">
                ${t.type === 'income' ? '+' : '-'} ${formatNumber(t.amount)}
            </div>
        </div>
    `).join('');
}

// Kartalar
function renderCards() {
    const container = document.getElementById('cardsList');
    if (data.cards.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#888;padding:20px;">Hali kartalar yo\'q</p>';
        return;
    }
    
    container.innerHTML = data.cards.map(c => `
        <div class="card-item">
            <div style="display:flex;justify-content:space-between;">
                <span>💳 ${c.name}</span>
                <span style="opacity:0.7;">${c.expiry}</span>
            </div>
            <div class="card-number">${maskCard(c.number)}</div>
            <div class="card-balance">${formatNumber(c.balance)} so'm</div>
        </div>
    `).join('');
}

function maskCard(number) {
    const clean = number.replace(/\s/g, '');
    if (clean.length >= 16) {
        return '**** ' + clean.slice(-4);
    }
    return number;
}

// Kontaktlar
function renderContacts() {
    const container = document.getElementById('contactsList');
    if (data.contacts.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#888;padding:20px;">Hali kontaktlar yo\'q</p>';
        return;
    }
    
    container.innerHTML = data.contacts.map(c => `
        <div class="contact-item">
            <div class="left">
                <div class="contact-avatar">${c.name.charAt(0)}</div>
                <div class="contact-info">
                    <h4>${c.name}</h4>
                    <p>${c.phone}</p>
                </div>
            </div>
            <div class="actions">
                <button class="btn-message" onclick="openMessage('${c.name}', '${c.phone}')">💬</button>
                <button class="btn-transfer" onclick="transferMoney('${c.name}')">💸</button>
            </div>
        </div>
    `).join('');
}

// Xabarlar
function renderMessages() {
    const container = document.getElementById('messagesList');
    if (data.messages.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:#888;padding:10px;">Hali xabarlar yo\'q</p>';
        return;
    }
    
    container.innerHTML = data.messages.map(m => `
        <div class="message-item">
            <div class="msg-header">
                <span>${m.from}</span>
                <span>${m.time}</span>
            </div>
            <div class="msg-text">${m.text}</div>
        </div>
    `).join('');
}

// Karta qo'shish
function openAddCard() {
    document.getElementById('addCardModal').style.display = 'flex';
}

function addCard() {
    const name = document.getElementById('cardName').value;
    const number = document.getElementById('cardNumber').value;
    const expiry = document.getElementById('cardExpiry').value;
    const balance = parseFloat(document.getElementById('cardBalance').value) || 0;
    
    if (!name || !number || !expiry) {
        alert('Iltimos, barcha maydonlarni to\'ldiring!');
        return;
    }
    
    data.cards.push({ name, number, expiry, balance });
    saveData();
    updateUI();
    closeModal('addCardModal');
    showNotification('✅ Karta qo\'shildi!');
}

// Kontakt qo'shish
function openAddContact() {
    document.getElementById('addContactModal').style.display = 'flex';
}

function addContact() {
    const name = document.getElementById('contactName').value;
    const phone = document.getElementById('contactPhone').value;
    const email = document.getElementById('contactEmail').value;
    
    if (!name || !phone) {
        alert('Iltimos, ism va telefon raqamini kiriting!');
        return;
    }
    
    data.contacts.push({ name, phone, email });
    saveData();
    updateUI();
    closeModal('addContactModal');
    showNotification('✅ Kontakt qo\'shildi!');
}

// Xabar yuborish
function openMessage(name, phone) {
    document.getElementById('messageModal').style.display = 'flex';
    document.getElementById('messageContact').innerHTML = `
        <div style="display:flex;align-items:center;gap:12px;padding:12px 0;">
            <div class="contact-avatar" style="width:40px;height:40px;background:#667eea;color:white;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;">${name.charAt(0)}</div>
            <div>
                <h4>${name}</h4>
                <p style="color:#888;font-size:12px;">${phone}</p>
            </div>
        </div>
    `;
    document.getElementById('messageModal').dataset.contactName = name;
}

function sendMessage() {
    const name = document.getElementById('messageModal').dataset.contactName;
    const text = document.getElementById('messageText').value;
    
    if (!text) {
        alert('Xabar matnini kiriting!');
        return;
    }
    
    data.messages.push({
        from: name,
        text: text,
        time: new Date().toLocaleString()
    });
    
    saveData();
    updateUI();
    closeModal('messageModal');
    showNotification('✅ Xabar yuborildi!');
}

// Pul o'tkazish
function transferMoney(name) {
    const amount = prompt(`💸 ${name} ga qancha pul o'tkazmoqchisiz?`, '100000');
    if (amount && !isNaN(amount) && parseFloat(amount) > 0) {
        const amountNum = parseFloat(amount);
        if (data.balance >= amountNum) {
            data.balance -= amountNum;
            data.expense += amountNum;
            data.transactions.unshift({
                id: Date.now(),
                type: 'expense',
                category: 'Pul o\'tkazma',
                amount: amountNum,
                description: `${name} ga pul o'tkazma`,
                date: new Date().to