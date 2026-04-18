<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>SAIKA PREMIUM</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg: #0a0b10;
            --card: #13151f;
            --primary: #3b82f6;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text: #ffffff;
            --text-secondary: #9ca3af;
            --border: #1f2937;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 16px; min-height: 100vh; padding-bottom: 30px; }

        .header { text-align: center; margin-bottom: 24px; padding-top: 20px; }
        .logo { 
            width: 80px; height: 80px; 
            background-image: url('https://files.catbox.moe/h05hbj.jpg');
            background-size: cover; background-position: center;
            border-radius: 22px; margin: 0 auto 16px; 
            box-shadow: 0 10px 30px rgba(59,130,246,0.3);
            border: 2px solid var(--primary);
        }
        h1 { font-size: 26px; font-weight: 800; background: linear-gradient(135deg, #fff, #9ca3af); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .badge { display: inline-block; background: rgba(59,130,246,0.2); padding: 4px 12px; border-radius: 20px; font-size: 12px; color: var(--primary); margin-top: 6px; border: 1px solid rgba(59,130,246,0.3); }

        .tabs { display: flex; flex-wrap: wrap; background: var(--card); border-radius: 18px; padding: 6px; margin-bottom: 20px; border: 1px solid var(--border); }
        .tab { flex: 1; padding: 12px 8px; text-align: center; border-radius: 14px; cursor: pointer; font-weight: 600; color: var(--text-secondary); transition: all 0.3s; font-size: 12px; }
        .tab i { margin-right: 4px; }
        .tab.active { background: var(--primary); color: white; box-shadow: 0 4px 15px rgba(59,130,246,0.3); }

        .page { display: none; animation: fadeIn 0.3s; }
        .page.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .category-title { font-size: 14px; font-weight: 700; color: var(--primary); margin: 24px 0 12px; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }

        .product-card { background: var(--card); border-radius: 20px; padding: 16px; margin-bottom: 10px; display: flex; align-items: center; cursor: pointer; border: 1px solid var(--border); transition: all 0.2s; }
        .product-card:active { transform: scale(0.98); background: #1a1e2e; }
        .product-icon { width: 54px; height: 54px; background: rgba(59,130,246,0.1); border-radius: 16px; display: flex; align-items: center; justify-content: center; margin-right: 16px; font-size: 24px; border: 1px solid rgba(59,130,246,0.2); }
        .product-info { flex: 1; }
        .product-name { font-weight: 700; margin-bottom: 6px; font-size: 16px; }
        .price-box { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
        .price-new { color: var(--success); font-size: 20px; font-weight: 800; }
        .price-old { color: var(--danger); text-decoration: line-through; font-size: 13px; opacity: 0.8; }
        .stock { font-size: 11px; color: var(--text-secondary); margin-top: 6px; }

        .profile-card { background: var(--card); border-radius: 24px; padding: 28px 20px; text-align: center; border: 1px solid var(--border); }
        .profile-avatar { width: 100px; height: 100px; border-radius: 30px; border: 3px solid var(--primary); margin-bottom: 16px; object-fit: cover; }
        .profile-name { font-size: 22px; font-weight: 800; margin-bottom: 4px; }
        .profile-id { color: var(--text-secondary); font-size: 13px; margin-bottom: 20px; }
        .stats { display: flex; gap: 12px; margin-top: 20px; }
        .stat { flex: 1; background: rgba(255,255,255,0.03); padding: 16px; border-radius: 18px; border: 1px solid var(--border); }
        .stat-value { font-size: 24px; font-weight: 800; color: var(--primary); }
        .stat-label { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; margin-top: 4px; }

        .orders-list { display: flex; flex-direction: column; gap: 12px; }
        .order-card { background: var(--card); border-radius: 20px; padding: 18px; border: 1px solid var(--border); }
        .order-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
        .order-status { font-size: 11px; padding: 5px 12px; border-radius: 20px; font-weight: 600; text-transform: uppercase; }
        .order-status.pending { background: rgba(245,158,11,0.2); color: var(--warning); border: 1px solid rgba(245,158,11,0.3); }
        .order-status.confirmed { background: rgba(16,185,129,0.2); color: var(--success); border: 1px solid rgba(16,185,129,0.3); }
        .order-status.declined { background: rgba(239,68,68,0.2); color: var(--danger); border: 1px solid rgba(239,68,68,0.3); }
        .order-product { font-weight: 700; margin-bottom: 6px; font-size: 16px; }
        .order-price { color: var(--success); font-weight: 700; margin-bottom: 8px; }

        .order-screenshot { 
            margin: 12px 0; 
            max-height: 200px;
            overflow: hidden;
            border-radius: 16px;
            cursor: pointer;
            position: relative;
            border: 1px solid var(--border);
        }
        .order-screenshot img { 
            width: 100%; 
            height: auto;
            max-height: 200px;
            object-fit: cover;
            border-radius: 16px; 
            transition: all 0.3s;
        }
        .order-screenshot.expanded {
            max-height: none;
        }
        .order-screenshot.expanded img {
            max-height: none;
            object-fit: contain;
        }
        .screenshot-overlay {
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            backdrop-filter: blur(5px);
        }

        .user-order-card { background: var(--card); border-radius: 20px; padding: 18px; border: 1px solid var(--border); margin-bottom: 12px; }
        .user-order-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .user-order-product { font-weight: 700; font-size: 16px; }
        .user-order-price { color: var(--success); font-weight: 700; }
        .user-order-date { color: var(--text-secondary); font-size: 12px; margin: 8px 0; }
        
        .order-file-block { margin-top: 16px; padding: 16px; background: rgba(59,130,246,0.1); border-radius: 16px; border: 1px solid var(--primary); }
        .order-file-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; color: var(--primary); font-weight: 600; }
        .file-download-btn { display: flex; align-items: center; justify-content: center; gap: 10px; background: var(--primary); color: white; padding: 14px; border-radius: 14px; text-decoration: none; font-weight: 600; margin-top: 12px; transition: 0.2s; cursor: pointer; }
        .file-download-btn:active { transform: scale(0.97); }
        .file-preview { max-width: 100%; border-radius: 12px; margin-bottom: 12px; border: 1px solid var(--border); max-height: 200px; object-fit: contain; }

        .file-card { background: var(--card); border-radius: 16px; padding: 16px; border: 1px solid var(--border); margin-bottom: 12px; }
        .file-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .file-name { font-weight: 600; }
        .file-meta { color: var(--text-secondary); font-size: 12px; margin: 8px 0; }
        .file-actions { display: flex; gap: 10px; margin-top: 12px; }
        .file-actions .btn { flex: 1; padding: 10px; font-size: 13px; }

        .modal { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--bg); padding: 20px; overflow-y: auto; z-index: 1000; }
        .modal-content { max-width: 500px; margin: 20px auto; background: var(--card); border-radius: 28px; padding: 28px; border: 1px solid var(--border); }
        .modal-title { font-size: 20px; font-weight: 800; margin-bottom: 20px; text-align: center; }

        .bank-box { background: rgba(0,0,0,0.3); border-radius: 20px; padding: 20px; margin: 20px 0; border: 1px solid var(--border); }
        .bank-row { margin-bottom: 16px; }
        .bank-label { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 6px; }
        .bank-value { font-size: 17px; font-weight: 600; display: flex; align-items: center; gap: 12px; font-family: 'Courier New', monospace; }
        .copy-btn { background: var(--border); border: none; color: var(--text); padding: 6px 14px; border-radius: 10px; cursor: pointer; font-size: 12px; }

        .upload-area { background: rgba(59,130,246,0.05); border: 2px dashed var(--primary); border-radius: 24px; padding: 36px 20px; text-align: center; margin: 20px 0; cursor: pointer; }
        .upload-area i { font-size: 48px; color: var(--primary); margin-bottom: 12px; }
        .preview-image { max-width: 100%; border-radius: 20px; margin: 16px 0; display: none; border: 1px solid var(--border); }

        textarea { width: 100%; background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 18px; padding: 16px; color: var(--text); font-size: 14px; margin: 16px 0; resize: vertical; }

        .btn { padding: 16px 20px; border-radius: 18px; border: none; font-weight: 700; font-size: 15px; cursor: pointer; transition: all 0.2s; text-align: center; display: block; width: 100%; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-success { background: var(--success); color: white; }
        .btn-danger { background: var(--danger); color: white; }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
        .btn:active { transform: scale(0.97); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .toast { position: fixed; bottom: 30px; left: 20px; right: 20px; background: var(--card); border: 1px solid var(--border); border-radius: 20px; padding: 16px 20px; display: flex; align-items: center; gap: 14px; z-index: 2000; max-width: 500px; margin: 0 auto; }
        .toast.success i { color: var(--success); }
        .toast.error i { color: var(--danger); }
        .toast.info i { color: var(--primary); }
        .toast-content { flex: 1; }
        .toast-title { font-weight: 700; margin-bottom: 4px; }
        .toast-message { font-size: 13px; color: var(--text-secondary); }

        .empty-state { text-align: center; padding: 40px 20px; color: var(--text-secondary); }
        .empty-state i { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }

        .admin-badge { background: var(--danger); color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-left: 8px; }
        .refresh-btn { background: var(--primary); color: white; padding: 8px 16px; border-radius: 12px; border: none; cursor: pointer; font-size: 13px; margin-left: 10px; }
    </style>
</head>
<body>

<div class="header">
    <div class="logo"></div>
    <h1>SAIKA PREMIUM</h1>
    <div class="badge"><i class="fas fa-shield-alt"></i> PRIVATE VPN</div>
</div>

<div class="tabs">
    <div class="tab active" onclick="switchTab('shop')"><i class="fas fa-store"></i> Магазин</div>
    <div class="tab" onclick="switchTab('profile')"><i class="fas fa-user"></i> Профиль</div>
    <div class="tab" onclick="switchTab('myOrders')"><i class="fas fa-history"></i> Мои заказы</div>
    <div class="tab" onclick="switchTab('orders')" id="ordersTab" style="display:none;"><i class="fas fa-clipboard-list"></i> Проверка</div>
    <div class="tab" onclick="switchTab('files')" id="filesTab" style="display:none;"><i class="fas fa-folder"></i> Файлы</div>
</div>

<!-- SHOP -->
<div id="shop" class="page active"><div id="productsList"></div></div>

<!-- PROFILE -->
<div id="profile" class="page">
    <div class="profile-card">
        <img id="profilePhoto" class="profile-avatar" src="">
        <h3 id="profileName" class="profile-name"></h3>
        <p id="profileId" class="profile-id"></p>
        <div class="stats">
            <div class="stat"><div class="stat-value" id="ordersCount">0</div><div class="stat-label">Заказов</div></div>
            <div class="stat"><div class="stat-value"><i class="fas fa-crown" style="color: #fbbf24;"></i></div><div class="stat-label">Premium</div></div>
        </div>
    </div>
</div>

<!-- MY ORDERS -->
<div id="myOrders" class="page">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <h3><i class="fas fa-history" style="color: var(--primary);"></i> История заказов</h3>
        <button class="refresh-btn" onclick="syncOrders()"><i class="fas fa-sync-alt"></i> Обновить</button>
    </div>
    <div id="myOrdersList"></div>
</div>

<!-- ORDERS (ADMIN) -->
<div id="orders" class="page">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
        <h3><i class="fas fa-clipboard-list" style="color: var(--primary);"></i> Заказы на проверку</h3>
        <button class="refresh-btn" onclick="syncAdminOrders()"><i class="fas fa-sync-alt"></i> Обновить</button>
    </div>
    <div id="ordersList" class="orders-list"></div>
</div>

<!-- FILES (MAIN ADMIN ONLY) -->
<div id="files" class="page">
    <h3 style="margin-bottom: 20px;"><i class="fas fa-folder" style="color: var(--primary);"></i> Все отправленные файлы</h3>
    <div id="filesList"></div>
</div>

<!-- MODALS -->
<div class="modal" id="payModal">
    <div class="modal-content">
        <div class="modal-title"><i class="fas fa-credit-card"></i> Оформление</div>
        <h3 id="payProduct" style="text-align:center;"></h3>
        <div style="font-size:42px;font-weight:800;color:var(--success);text-align:center;margin:20px 0;" id="payPrice"></div>
        <div class="bank-box">
            <div class="bank-row"><div class="bank-label">Банк</div><div class="bank-value">Т-Банк</div></div>
            <div class="bank-row"><div class="bank-label">Карта</div><div class="bank-value">2200 7021 4895 7363 <button class="copy-btn" onclick="copyCard()"><i class="fas fa-copy"></i></button></div></div>
            <div class="bank-row"><div class="bank-label">Получатель</div><div class="bank-value">Саид К.</div></div>
        </div>
        <button class="btn btn-success" onclick="openUploadModal()"><i class="fas fa-check-circle"></i> Я ОПЛАТИЛ</button>
        <button class="btn btn-outline" onclick="closePayModal()" style="margin-top:10px;">Отмена</button>
    </div>
</div>

<div class="modal" id="uploadModal">
    <div class="modal-content">
        <div class="modal-title"><i class="fas fa-cloud-upload-alt"></i> Загрузить чек</div>
        <h3 id="uploadProduct" style="text-align:center;"></h3>
        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
            <i class="fas fa-cloud-upload-alt"></i>
            <p style="font-weight:600;">Нажмите чтобы выбрать скриншот</p>
        </div>
        <input type="file" id="fileInput" accept="image/*" style="display:none;" onchange="handleFileSelect(this)">
        <img id="previewImage" class="preview-image" src="" alt="Preview">
        <textarea id="orderComment" placeholder="Комментарий..."></textarea>
        <button class="btn btn-success" id="sendBtn" onclick="sendOrder()" disabled><i class="fas fa-paper-plane"></i> ОТПРАВИТЬ</button>
        <button class="btn btn-outline" onclick="closeUploadModal()" style="margin-top:10px;">Назад</button>
    </div>
</div>

<div class="modal" id="sendFileModal">
    <div class="modal-content">
        <div class="modal-title"><i class="fas fa-file-upload"></i> Отправить файл</div>
        <h3 id="sendFileProduct" style="text-align:center;"></h3>
        <p id="sendFileUser" style="text-align:center;color:var(--text-secondary);"></p>
        <div class="upload-area" onclick="document.getElementById('adminFileInput').click()">
            <i class="fas fa-file"></i>
            <p style="font-weight:600;" id="fileSelectText">Выберите файл</p>
            <p style="font-size:12px;color:var(--text-secondary);" id="selectedFileName"></p>
        </div>
        <input type="file" id="adminFileInput" style="display:none;" onchange="handleAdminFileSelect(this)">
        <textarea id="fileDescription" placeholder="Описание к файлу..."></textarea>
        <button class="btn btn-success" id="sendFileBtn" onclick="sendFileToUser()" disabled><i class="fas fa-paper-plane"></i> ОТПРАВИТЬ</button>
        <button class="btn btn-outline" onclick="closeSendFileModal()" style="margin-top:10px;">Отмена</button>
    </div>
</div>

<script>
    let tg = window.Telegram.WebApp;
    tg.expand();
    tg.ready();
    
    const MAIN_ADMIN = 1471307057;
    const SECOND_ADMIN = 7066870264;
    const ADMIN_IDS = [MAIN_ADMIN, SECOND_ADMIN];
    const BOT_USERNAME = 'vpnsaika_bot';
    
    let currentUser = tg.initDataUnsafe.user || {};
    let isAdmin = ADMIN_IDS.includes(currentUser.id);
    let isMainAdmin = currentUser.id === MAIN_ADMIN;
    
    let currentProduct = null;
    let selectedFile = null;
    let adminSelectedFile = null;
    let currentOrderId = null;
    
    let orders = [];
    let sentFiles = [];
    
    const products = {
        vpn: [
            {name:"SAIKA S1 VPN", price:79, old:1199, stock:"9", icon:'<i class="fas fa-bolt"></i>'},
            {name:"VIP VPN", price:79, old:529, stock:"10", icon:'<i class="fas fa-crown" style="color:#fbbf24;"></i>'},
            {name:"GTR VPN", price:79, old:899, stock:"∞", icon:'<i class="fas fa-car"></i>'},
            {name:"ULTRA MAX VPN", price:79, old:629, stock:"8", icon:'<i class="fas fa-fire"></i>'},
            {name:"STRONG VPN", price:79, old:499, stock:"∞", icon:'<i class="fas fa-dumbbell"></i>'},
            {name:"UNLY VPN", price:79, old:399, stock:"∞", icon:'<i class="fas fa-infinity"></i>'},
            {name:"TDM SKILL VPN", price:79, old:199, stock:"∞", icon:'<i class="fas fa-crosshairs"></i>'},
            {name:"FUCK VPN", price:49, old:139, stock:"∞", icon:'<i class="fas fa-skull"></i>'},
            {name:"DEAD ALL VPN", price:79, old:1299, stock:"∞", icon:'<i class="fas fa-ghost"></i>'}
        ],
        extra: [
            {name:"Магнит андроид", price:169, old:259, stock:"∞", icon:'<i class="fab fa-android"></i>'},
            {name:"Магнит ios", price:269, old:null, stock:"∞", icon:'<i class="fab fa-apple"></i>'},
            {name:"Пак сайки", price:639, old:1789, stock:"∞", icon:'<i class="fas fa-box-open"></i>'},
            {name:"Пак unly", price:79, old:1299, stock:"10", icon:'<i class="fas fa-archive"></i>'}
        ],
        dns: [
            {name:"DNS android", price:129, old:239, stock:"∞", icon:'<i class="fas fa-network-wired"></i>'},
            {name:"DNS Ios", price:129, old:239, stock:"∞", icon:'<i class="fas fa-wifi"></i>'}
        ]
    };
    
    function showToast(title, message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        let icon = 'info-circle';
        if (type === 'success') icon = 'check-circle';
        if (type === 'error') icon = 'exclamation-circle';
        toast.innerHTML = `<i class="fas fa-${icon}"></i><div class="toast-content"><div class="toast-title">${title}</div><div class="toast-message">${message}</div></div>`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }
    
    function downloadFile(dataUrl, fileName) {
        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast('📥 Скачивание', fileName, 'success');
    }
    
    function loadFromStorage() {
        const storedOrders = localStorage.getItem('saika_orders');
        if (storedOrders) orders = JSON.parse(storedOrders);
        
        const storedFiles = localStorage.getItem('saika_sent_files');
        if (storedFiles) sentFiles = JSON.parse(storedFiles);
    }
    
    function saveToStorage() {
        localStorage.setItem('saika_orders', JSON.stringify(orders));
        localStorage.setItem('saika_sent_files', JSON.stringify(sentFiles));
    }
    
    function syncOrders() {
        loadFromStorage();
        renderMyOrders();
        updateOrdersCount();
        showToast('🔄 Обновлено', 'Данные синхронизированы', 'info');
    }
    
    function syncAdminOrders() {
        loadFromStorage();
        renderOrders();
        showToast('🔄 Обновлено', 'Данные синхронизированы', 'info');
    }
    
    function init() {
        if (!currentUser.id) {
            showToast('❌ Ошибка', 'Не удалось получить данные пользователя. Перезапустите приложение.', 'error');
            return;
        }
        
        if (isAdmin) {
            document.getElementById('ordersTab').style.display = 'block';
        }
        if (isMainAdmin) {
            document.getElementById('filesTab').style.display = 'block';
        }
        
        const avatar = document.getElementById('profilePhoto');
        if (currentUser.photo_url) {
            avatar.src = currentUser.photo_url;
        } else {
            avatar.src = 'https://ui-avatars.com/api/?name=' + encodeURIComponent(currentUser.first_name || 'U') + '&background=3b82f6&color=fff&size=100';
        }
        
        let displayName = currentUser.first_name + (currentUser.last_name ? ' ' + currentUser.last_name : '');
        if (currentUser.id === MAIN_ADMIN) displayName += ' <span class="admin-badge">ГЛАВНЫЙ</span>';
        else if (isAdmin) displayName += ' <span class="admin-badge">АДМИН</span>';
        
        document.getElementById('profileName').innerHTML = displayName;
        document.getElementById('profileId').innerHTML = '<i class="fas fa-id-card"></i> ID: ' + currentUser.id;
        
        loadFromStorage();
        updateOrdersCount();
        renderProducts();
        renderOrders();
        renderMyOrders();
        renderFiles();
    }
    
    function updateOrdersCount() {
        let userOrders = orders.filter(o => o.userId === currentUser.id);
        document.getElementById('ordersCount').innerText = userOrders.length;
    }
    
    function renderProducts() {
        let html = '';
        html += `<div class="category-title"><i class="fas fa-shield-virus" style="color:#3b82f6;"></i> VPN ДЛЯ PUBG</div>`;
        products.vpn.forEach(p => html += renderProductCard(p));
        html += `<div class="category-title"><i class="fas fa-cubes" style="color:#8b5cf6;"></i> МАГНИТ & ПАКИ</div>`;
        products.extra.forEach(p => html += renderProductCard(p));
        html += `<div class="category-title"><i class="fas fa-globe" style="color:#10b981;"></i> DNS СЕРВИСЫ</div>`;
        products.dns.forEach(p => html += renderProductCard(p));
        document.getElementById('productsList').innerHTML = html;
    }
    
    function renderProductCard(p) {
        return `<div class="product-card" onclick="openPayModal('${p.name}', ${p.price})">
            <div class="product-icon">${p.icon}</div>
            <div class="product-info">
                <div class="product-name">${p.name}</div>
                <div class="price-box">
                    <span class="price-new">${p.price} ₽</span>
                    ${p.old ? `<span class="price-old">${p.old} ₽</span>` : ''}
                </div>
                <div class="stock"><i class="fas fa-box"></i> В наличии: ${p.stock} шт.</div>
            </div>
            <i class="fas fa-chevron-right" style="color:var(--text-secondary);"></i>
        </div>`;
    }
    
    function renderMyOrders() {
        let userOrders = orders.filter(o => o.userId === currentUser.id);
        if (userOrders.length === 0) {
            document.getElementById('myOrdersList').innerHTML = `<div class="empty-state"><i class="fas fa-shopping-bag"></i><p>У вас пока нет заказов</p><button class="btn btn-primary" onclick="switchTab('shop')" style="margin-top:20px;">Перейти в магазин</button></div>`;
            return;
        }
        
        let html = '';
        userOrders.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp)).forEach(order => {
            const date = new Date(order.timestamp).toLocaleString('ru-RU', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
            let statusIcon = '⏳', statusText = 'Ожидает', statusClass = 'pending';
            if (order.status === 'confirmed') { statusIcon = '✅'; statusText = 'Выполнен'; statusClass = 'confirmed'; }
            else if (order.status === 'declined') { statusIcon = '❌'; statusText = 'Отклонён'; statusClass = 'declined'; }
            
            html += `<div class="user-order-card">
                <div class="user-order-header">
                    <span class="user-order-product"><i class="fas fa-box"></i> ${order.product}</span>
                    <span class="order-status ${statusClass}">${statusIcon} ${statusText}</span>
                </div>
                <div class="user-order-price"><i class="fas fa-ruble-sign"></i> ${order.price} ₽</div>
                <div class="user-order-date"><i class="far fa-calendar"></i> ${date}</div>
                ${order.comment ? `<div class="order-comment"><i class="fas fa-comment"></i> ${order.comment}</div>` : ''}`;
            
            if (order.status === 'confirmed' && order.fileData) {
                const fileExt = order.fileName ? order.fileName.split('.').pop().toLowerCase() : '';
                const isImage = ['jpg','jpeg','png','gif','webp'].includes(fileExt);
                
                html += `<div class="order-file-block">
                    <div class="order-file-header"><i class="fas fa-check-circle" style="color:var(--success);"></i> Файл готов</div>`;
                
                if (isImage) {
                    html += `<img src="${order.fileData}" class="file-preview" alt="Preview">`;
                }
                
                html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                    <i class="fas fa-file"></i> <span>${order.fileName || 'file'}</span>
                </div>`;
                
                if (order.fileDescription) {
                    html += `<div class="order-comment"><i class="fas fa-align-left"></i> ${order.fileDescription}</div>`;
                }
                
                html += `<button class="file-download-btn" onclick="downloadFile('${order.fileData}', '${order.fileName || 'file'}')">
                    <i class="fas fa-download"></i> СКАЧАТЬ ФАЙЛ
                </button>`;
                
                html += `<button class="btn btn-outline" style="margin-top:10px;" onclick="tg.openTelegramLink('https://t.me/${BOT_USERNAME}')">
                    <i class="fab fa-telegram"></i> ПОЛУЧИТЬ В БОТЕ
                </button></div>`;
            } else if (order.status === 'confirmed' && !order.fileData) {
                html += `<div class="order-file-block"><div class="order-file-header"><i class="fas fa-hourglass-half"></i> Файл загружается...</div><p style="color:var(--text-secondary);">Нажмите "Получить в боте" или обновите страницу</p>
                <button class="btn btn-primary" style="margin-top:10px;" onclick="tg.openTelegramLink('https://t.me/${BOT_USERNAME}')">
                    <i class="fab fa-telegram"></i> ПОЛУЧИТЬ В БОТЕ
                </button></div>`;
            } else if (order.status === 'declined') {
                html += `<div class="order-file-block" style="background:rgba(239,68,68,0.1);border-color:var(--danger);"><div class="order-file-header" style="color:var(--danger);"><i class="fas fa-exclamation-circle"></i> Заказ отклонён</div><p style="color:var(--text-secondary);">Свяжитесь с @saikasupport</p></div>`;
            }
            
            html += `</div>`;
        });
        document.getElementById('myOrdersList').innerHTML = html;
    }
    
    function renderOrders() {
        if (!isAdmin) return;
        let pendingOrders = orders.filter(o => o.status === 'pending');
        if (pendingOrders.length === 0) {
            document.getElementById('ordersList').innerHTML = `<div class="empty-state"><i class="fas fa-inbox"></i><p>Нет заказов на проверку</p></div>`;
            return;
        }
        let html = '';
        pendingOrders.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp)).forEach(order => {
            const date = new Date(order.timestamp).toLocaleString('ru-RU', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
            html += `<div class="order-card">
                <div class="order-header"><span class="order-user"><i class="fas fa-user"></i> @${order.username || 'User'}</span><span class="order-status pending"><i class="fas fa-clock"></i> Ожидает</span></div>
                <div class="order-product"><i class="fas fa-tag"></i> ${order.product}</div>
                <div class="order-price"><i class="fas fa-ruble-sign"></i> ${order.price} ₽</div>
                <div style="color:var(--text-secondary);font-size:12px;margin:5px 0;"><i class="fas fa-id-card"></i> ID: ${order.userId} | ${date}</div>
                ${order.comment ? `<div class="order-comment"><i class="fas fa-comment"></i> ${order.comment}</div>` : ''}
                ${order.screenshot ? `
                    <div class="order-screenshot" onclick="this.classList.toggle('expanded')">
                        <img src="${order.screenshot}" onclick="event.stopPropagation(); window.open('${order.screenshot}')">
                        <span class="screenshot-overlay"><i class="fas fa-search-plus"></i> Развернуть</span>
                    </div>
                ` : ''}
                <div class="order-actions">
                    <button class="btn btn-success" onclick="confirmOrder('${order.id}')"><i class="fas fa-check"></i> Подтвердить</button>
                    <button class="btn btn-danger" onclick="declineOrder('${order.id}')"><i class="fas fa-times"></i> Отклонить</button>
                </div>
            </div>`;
        });
        document.getElementById('ordersList').innerHTML = html;
    }
    
    function renderFiles() {
        if (!isMainAdmin) return;
        
        if (sentFiles.length === 0) {
            document.getElementById('filesList').innerHTML = `<div class="empty-state"><i class="fas fa-folder-open"></i><p>Нет отправленных файлов</p></div>`;
            return;
        }
        
        let html = '';
        sentFiles.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp)).forEach(file => {
            const date = new Date(file.timestamp).toLocaleString('ru-RU', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
            const sentBy = file.sentBy === MAIN_ADMIN ? 'Главный админ' : `Админ ${file.sentBy}`;
            
            html += `<div class="file-card">
                <div class="file-header">
                    <span class="file-name"><i class="fas fa-file"></i> ${file.fileName}</span>
                    <span style="color:var(--text-secondary);font-size:12px;">${date}</span>
                </div>
                <div class="file-meta">
                    <div><i class="fas fa-user"></i> Отправил: ${sentBy}</div>
                    <div><i class="fas fa-user-plus"></i> Покупатель: @${file.buyerUsername} (ID: ${file.buyerId})</div>
                    <div><i class="fas fa-box"></i> Товар: ${file.product}</div>
                    <div><i class="fas fa-tag"></i> Сумма: ${file.price} ₽</div>
                    ${file.description ? `<div><i class="fas fa-align-left"></i> ${file.description}</div>` : ''}
                </div>
                <div class="file-actions">
                    <button class="btn btn-primary" onclick="downloadFile('${file.fileData}', '${file.fileName}')"><i class="fas fa-download"></i> Скачать</button>
                </div>
            </div>`;
        });
        document.getElementById('filesList').innerHTML = html;
    }
    
    function switchTab(tab) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        const tabs = ['shop', 'profile', 'myOrders', 'orders', 'files'];
        const index = tabs.indexOf(tab);
        if (index >= 0) {
            document.querySelectorAll('.tab')[index].classList.add('active');
            document.getElementById(tab).classList.add('active');
        }
        
        if (tab === 'profile') updateOrdersCount();
        if (tab === 'myOrders') syncOrders();
        if (tab === 'orders' && isAdmin) syncAdminOrders();
        if (tab === 'files' && isMainAdmin) renderFiles();
    }
    
    function openPayModal(name, price) {
        currentProduct = {name, price};
        document.getElementById('payProduct').innerHTML = `<i class="fas fa-shopping-cart"></i> ${name}`;
        document.getElementById('payPrice').innerText = price + ' ₽';
        document.getElementById('payModal').style.display = 'block';
    }
    
    function closePayModal() { document.getElementById('payModal').style.display = 'none'; }
    function copyCard() { navigator.clipboard?.writeText('2200702148957363'); showToast('✅ Скопировано', 'Номер карты в буфере', 'success'); }
    
    function openUploadModal() {
        closePayModal();
        document.getElementById('uploadProduct').innerHTML = `<i class="fas fa-file-invoice"></i> ${currentProduct.name} - ${currentProduct.price} ₽`;
        document.getElementById('uploadModal').style.display = 'block';
    }
    
    function closeUploadModal() {
        document.getElementById('uploadModal').style.display = 'none';
        selectedFile = null;
        document.getElementById('previewImage').style.display = 'none';
        document.getElementById('sendBtn').disabled = true;
        document.getElementById('fileInput').value = '';
        document.getElementById('orderComment').value = '';
    }
    
    function handleFileSelect(input) {
        if (input.files && input.files[0]) {
            selectedFile = input.files[0];
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('previewImage').src = e.target.result;
                document.getElementById('previewImage').style.display = 'block';
                document.getElementById('sendBtn').disabled = false;
            };
            reader.readAsDataURL(selectedFile);
        }
    }
    
    function sendOrder() {
        const comment = document.getElementById('orderComment').value;
        const reader = new FileReader();
        reader.onload = (e) => {
            const orderId = Date.now() + '_' + currentUser.id;
            const order = {
                id: orderId, userId: currentUser.id, username: currentUser.username || currentUser.first_name,
                product: currentProduct.name, price: currentProduct.price, comment: comment,
                screenshot: e.target.result, status: 'pending', timestamp: new Date().toISOString()
            };
            orders.push(order);
            saveToStorage();
            
            tg.sendData(JSON.stringify({action: 'new_order', order: order}));
            showToast('✅ Заказ отправлен!', 'Статус можно отслеживать во вкладке "Мои заказы"', 'success');
            closeUploadModal();
            updateOrdersCount();
        };
        if (selectedFile) reader.readAsDataURL(selectedFile);
    }
    
    function confirmOrder(orderId) {
        const order = orders.find(o => o.id === orderId);
        if (!order) return;
        currentOrderId = orderId;
        document.getElementById('sendFileProduct').innerHTML = `<i class="fas fa-box"></i> ${order.product}`;
        document.getElementById('sendFileUser').innerHTML = `<i class="fas fa-user"></i> @${order.username} (ID: ${order.userId})`;
        document.getElementById('sendFileModal').style.display = 'block';
    }
    
    function declineOrder(orderId) {
        const order = orders.find(o => o.id === orderId);
        if (!order) return;
        order.status = 'declined';
        saveToStorage();
        tg.sendData(JSON.stringify({action: 'decline_order', order: order}));
        showToast('❌ Заказ отклонён', '', 'error');
        renderOrders();
    }
    
    function closeSendFileModal() {
        document.getElementById('sendFileModal').style.display = 'none';
        adminSelectedFile = null;
        document.getElementById('sendFileBtn').disabled = true;
        document.getElementById('adminFileInput').value = '';
        document.getElementById('fileSelectText').innerHTML = 'Выберите файл';
        document.getElementById('selectedFileName').innerHTML = '';
        document.getElementById('fileDescription').value = '';
    }
    
    function handleAdminFileSelect(input) {
        if (input.files && input.files[0]) {
            adminSelectedFile = input.files[0];
            document.getElementById('fileSelectText').innerHTML = '<i class="fas fa-check-circle" style="color:var(--success);"></i> Файл выбран';
            document.getElementById('selectedFileName').innerHTML = adminSelectedFile.name + ' (' + (adminSelectedFile.size / 1024).toFixed(1) + ' KB)';
            document.getElementById('sendFileBtn').disabled = false;
        }
    }
    
    function sendFileToUser() {
        if (!adminSelectedFile || !currentOrderId) return;
        const order = orders.find(o => o.id === currentOrderId);
        if (!order) return;
        const description = document.getElementById('fileDescription').value;
        const reader = new FileReader();
        reader.onload = (e) => {
            order.status = 'confirmed';
            order.fileData = e.target.result;
            order.fileName = adminSelectedFile.name;
            order.fileDescription = description;
            saveToStorage();
            
            const fileRecord = {
                id: Date.now() + '_file',
                orderId: order.id,
                fileName: adminSelectedFile.name,
                fileData: e.target.result,
                description: description,
                sentBy: currentUser.id,
                buyerId: order.userId,
                buyerUsername: order.username,
                product: order.product,
                price: order.price,
                timestamp: new Date().toISOString()
            };
            sentFiles.push(fileRecord);
            saveToStorage();
            
            tg.sendData(JSON.stringify({
                action: 'send_file',
                order: order,
                file: e.target.result,
                fileName: adminSelectedFile.name,
                description: description
            }));
            
            showToast('✅ Файл отправлен!', `Покупатель @${order.username} получит уведомление`, 'success');
            closeSendFileModal();
            renderOrders();
            if (isMainAdmin) renderFiles();
        };
        reader.readAsDataURL(adminSelectedFile);
    }
    
    init();
    tg.MainButton.hide();
</script>
</body>
</html>
