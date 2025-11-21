// 配置
const CONFIG = {
    API_BASE: window.location.origin + '/api',
    UPDATE_INTERVAL: 30000, // 30秒检查一次更新
    RETRY_DELAY: 2000,      // 重试延迟
    MAX_RETRIES: 3          // 最大重试次数
};

// 全局状态
let state = {
    products: [],
    priceChart: null,
    currentModal: null,
    connectionStatus: 'connecting',
    lastUpdate: null,
    retryCount: 0
};

// DOM 元素
const elements = {
    productsList: document.getElementById('productsList'),
    productUrl: document.getElementById('productUrl'),
    addBtn: document.getElementById('addBtn'),
    refreshBtn: document.getElementById('refreshBtn'),
    totalProducts: document.getElementById('totalProducts'),
    updatedToday: document.getElementById('updatedToday'),
    priceDrops: document.getElementById('priceDrops'),
    serverStatus: document.getElementById('serverStatus'),
    lastUpdate: document.getElementById('lastUpdate')
};

// 页面加载
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 每日价格追踪系统启动");
    initializeApp();
});

// 初始化应用
async function initializeApp() {
    try {
        // 测试服务器连接
        await testServerConnection();
        
        // 加载商品数据
        await loadProducts();
        
        // 启动定时任务
        startBackgroundTasks();
        
        // 设置事件监听器
        setupEventListeners();
        
        console.log("✅ 应用初始化完成");
    } catch (error) {
        console.error("❌ 应用初始化失败:", error);
        showMessage("系统初始化失败，请刷新页面重试", "error");
    }
}

// 测试服务器连接
async function testServerConnection() {
    try {
        const response = await fetchWithTimeout(`${CONFIG.API_BASE}/status`, {
            timeout: 5000
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        updateConnectionStatus('connected');
        console.log("✅ 服务器连接正常:", data);
        
    } catch (error) {
        console.error("❌ 服务器连接失败:", error);
        updateConnectionStatus('disconnected');
        throw error;
    }
}

// 更新连接状态
function updateConnectionStatus(status) {
    state.connectionStatus = status;
    const statusElement = elements.serverStatus;
    
    switch (status) {
        case 'connected':
            statusElement.innerHTML = '🟢 服务器正常';
            statusElement.style.color = '#27ae60';
            break;
        case 'connecting':
            statusElement.innerHTML = '🟡 连接中...';
            statusElement.style.color = '#f39c12';
            break;
        case 'disconnected':
            statusElement.innerHTML = '🔴 连接失败';
            statusElement.style.color = '#e74c3c';
            break;
    }
}

// 加载商品列表
async function loadProducts() {
    showLoadingState();
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}/products`);
        
        if (!response.ok) {
            throw new Error(`HTTP错误! 状态码: ${response.status}`);
        }
        
        const products = await response.json();
        state.products = products;
        
        renderProducts(products);
        updateStatistics(products);
        updateLastUpdateTime();
        
        console.log(`✅ 加载 ${products.length} 个商品`);
        
    } catch (error) {
        console.error('❌ 加载商品失败:', error);
        showErrorState('加载商品失败: ' + error.message);
        throw error;
    }
}

// 渲染商品列表
function renderProducts(products) {
    if (!products || products.length === 0) {
        showEmptyState();
        return;
    }

    const productsHTML = products.map(product => createProductCard(product)).join('');
    elements.productsList.innerHTML = productsHTML;
}

// 创建商品卡片
function createProductCard(product) {
    const priceChange = product.price_change || 0;
    const changeClass = priceChange > 0 ? 'change-up' : priceChange < 0 ? 'change-down' : '';
    const changeText = priceChange > 0 ? `+${priceChange}%` : priceChange < 0 ? `${priceChange}%` : '0%';
    
    const imageHTML = product.display_image ? 
        `<img src="${product.display_image}" alt="${product.name}" onerror="handleImageError(this)">` :
        `<div class="image-placeholder">
            <div class="placeholder-icon">📷</div>
            <div>暂无图片</div>
        </div>`;

    return `
        <div class="product-card" onclick="showProductDetail(${product.id})">
            <div class="product-image">
                ${imageHTML}
            </div>
            <div class="product-name" title="${escapeHtml(product.name)}">${escapeHtml(product.name)}</div>
            
            <div class="price-section">
                <div class="current-price">¥${formatPrice(product.current_price)}</div>
                ${product.lowest_price && product.lowest_price < product.current_price ? 
                    `<div class="lowest-price">历史最低: ¥${formatPrice(product.lowest_price)}</div>` : ''}
                ${priceChange !== 0 ? `<div class="price-change ${changeClass}">${changeText}</div>` : ''}
            </div>
            
            <div class="product-meta">
                <span class="platform-badge">${getPlatformName(product.platform)}</span>
                <span class="product-updated">${formatRelativeTime(product.last_updated)}</span>
            </div>
            
            <div class="product-actions" style="margin-top: 10px; display: flex; gap: 8px;">
                <button class="btn-secondary" onclick="event.stopPropagation(); setPriceAlert(${product.id})" style="padding: 6px 12px; font-size: 12px;">
                    🔔 提醒
                </button>
                <button class="btn-secondary" onclick="event.stopPropagation(); deleteProduct(${product.id})" style="padding: 6px 12px; font-size: 12px; background: #e74c3c; color: white;">
                    🗑️ 删除
                </button>
            </div>
        </div>
    `;
}

// 显示加载状态
function showLoadingState() {
    elements.productsList.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>加载商品列表中...</p>
        </div>
    `;
}

// 显示空状态
function showEmptyState() {
    elements.productsList.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">📦</div>
            <h3>还没有监控商品</h3>
            <p>添加第一个商品开始监控价格变化</p>
            <div style="margin-top: 20px;">
                <button class="btn-primary" onclick="showHelp()">查看使用帮助</button>
            </div>
        </div>
    `;
}

// 显示错误状态
function showErrorState(message) {
    elements.productsList.innerHTML = `
        <div class="message error">
            <strong>加载失败</strong>
            <p>${message}</p>
            <button class="btn-secondary" onclick="loadProducts()" style="margin-top: 10px;">重试</button>
        </div>
    `;
}

// 更新统计信息
function updateStatistics(products) {
    elements.totalProducts.textContent = products.length;
    
    const today = new Date().toDateString();
    const updatedToday = products.filter(p => 
        p.last_updated && new Date(p.last_updated).toDateString() === today
    ).length;
    elements.updatedToday.textContent = updatedToday;
    
    const priceDrops = products.filter(p => (p.price_change || 0) < 0).length;
    elements.priceDrops.textContent = priceDrops;
}

// 添加商品
async function addProduct() {
    const url = elements.productUrl.value.trim();
    
    if (!url) {
        showMessage('请输入商品链接', 'error');
        return;
    }
    
    // 验证URL格式
    if (!isValidUrl(url)) {
        showMessage('请输入有效的商品链接', 'error');
        return;
    }
    
    // 显示加载状态
    const addBtn = elements.addBtn;
    const originalText = addBtn.querySelector('.btn-text').textContent;
    const loadingText = addBtn.querySelector('.btn-loading');
    
    addBtn.disabled = true;
    addBtn.querySelector('.btn-text').style.display = 'none';
    loadingText.style.display = 'inline';
    
    try {
        console.log("🔄 添加商品:", url);
        
        const response = await fetch(`${CONFIG.API_BASE}/products`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const result = await response.json();
        console.log("✅ 添加商品响应:", result);

        if (response.ok) {
            showMessage('🎉 ' + result.message, 'success');
            elements.productUrl.value = '';
            
            // 重新加载商品列表
            await loadProducts();
            
        } else {
            showMessage('❌ ' + result.error, 'error');
        }
        
    } catch (error) {
        console.error('❌ 添加失败:', error);
        showMessage('❌ 网络错误: ' + error.message, 'error');
    } finally {
        // 恢复按钮状态
        addBtn.disabled = false;
        addBtn.querySelector('.btn-text').style.display = 'inline';
        loadingText.style.display = 'none';
    }
}

// 显示商品详情
async function showProductDetail(productId) {
    try {
        const product = state.products.find(p => p.id === productId);
        if (!product) return;

        // 获取价格历史和统计信息
        const [pricesResponse, statsResponse] = await Promise.all([
            fetch(`${CONFIG.API_BASE}/products/${productId}/prices`),
            fetch(`${CONFIG.API_BASE}/products/${productId}/stats`)
        ]);

        if (!pricesResponse.ok || !statsResponse.ok) {
            throw new Error('获取商品详情失败');
        }

        const prices = await pricesResponse.json();
        const stats = await statsResponse.json();

        // 渲染模态框内容
        renderProductModal(product, prices, stats);
        openModal('productModal');

    } catch (error) {
        console.error('❌ 加载商品详情失败:', error);
        showMessage('加载商品详情失败: ' + error.message, 'error');
    }
}

// 渲染商品详情模态框
function renderProductModal(product, prices, stats) {
    const modalContent = document.getElementById('modalContent');
    const priceChange = product.price_change || 0;
    const changeClass = priceChange > 0 ? 'change-up' : priceChange < 0 ? 'change-down' : '';
    const changeText = priceChange > 0 ? `+${priceChange}%` : priceChange < 0 ? `${priceChange}%` : '0%';

    modalContent.innerHTML = `
        <div class="product-detail">
            <div class="detail-header">
                <div class="detail-image">
                    ${product.display_image ? 
                        `<img src="${product.display_image}" alt="${product.name}" style="width: 200px; height: 200px; object-fit: cover; border-radius: 12px;">` :
                        '<div style="width: 200px; height: 200px; background: #f8f9fa; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: #95a5a6;">暂无图片</div>'
                    }
                </div>
                <div class="detail-info">
                    <h4>${escapeHtml(product.name)}</h4>
                    <div class="price-info">
                        <div class="current-price" style="font-size: 2em;">¥${formatPrice(product.current_price)}</div>
                        ${priceChange !== 0 ? `<div class="price-change ${changeClass}" style="font-size: 1.2em;">${changeText}</div>` : ''}
                    </div>
                    <div class="platform-info">
                        <span class="platform-badge">${getPlatformName(product.platform)}</span>
                        <span>最后更新: ${formatDateTime(product.last_updated)}</span>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-value">¥${formatPrice(stats.stats.min_price)}</div>
                            <div class="stat-label">历史最低</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">¥${formatPrice(stats.stats.max_price)}</div>
                            <div class="stat-label">历史最高</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">¥${formatPrice(stats.stats.average_price)}</div>
                            <div class="stat-label">平均价格</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.stats.total_records}</div>
                            <div class="stat-label">记录次数</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="price-chart-section">
                <h4>价格趋势 (最近30天)</h4>
                <div class="chart-container">
                    <canvas id="detailPriceChart"></canvas>
                </div>
            </div>
            
            <div class="modal-actions">
                <button class="btn-primary" onclick="setPriceAlert(${product.id})">
                    🔔 设置价格提醒
                </button>
                <button class="btn-secondary" onclick="openOriginalLink('${product.url}')">
                    🔗 查看原商品
                </button>
            </div>
        </div>
    `;

    // 渲染图表
    renderDetailChart(prices, product.name);
}

// 渲染详情图表
function renderDetailChart(prices, productName) {
    const ctx = document.getElementById('detailPriceChart').getContext('2d');
    
    if (state.priceChart) {
        state.priceChart.destroy();
    }
    
    const labels = prices.map((p, index) => {
        const date = new Date(p.timestamp);
        return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    });
    
    const data = prices.map(p => p.price);
    
    state.priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: productName,
                data: data,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3498db',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '价格趋势图',
                    font: {
                        size: 16
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `价格: ¥${context.parsed.y}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '价格 (元)'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'nearest'
            }
        }
    });
}

// 设置价格提醒
async function setPriceAlert(productId) {
    const product = state.products.find(p => p.id === productId);
    if (!product) return;

    const targetPrice = prompt(`为 "${product.name}" 设置价格提醒\n当前价格: ¥${formatPrice(product.current_price)}\n请输入目标价格:`);
    
    if (!targetPrice || isNaN(targetPrice)) {
        showMessage('请输入有效的价格', 'error');
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE}/alerts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                target_price: parseFloat(targetPrice)
            })
        });

        if (response.ok) {
            showMessage('🎯 价格提醒设置成功!', 'success');
        } else {
            const result = await response.json();
            showMessage('❌ ' + result.error, 'error');
        }
    } catch (error) {
        console.error('❌ 设置提醒失败:', error);
        showMessage('设置提醒失败: ' + error.message, 'error');
    }
}

// 删除商品
async function deleteProduct(productId) {
    const product = state.products.find(p => p.id === productId);
    if (!product) return;

    if (!confirm(`确定要删除 "${product.name}" 吗？\n此操作将删除所有价格历史记录。`)) {
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_BASE}/products/${productId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showMessage('🗑️ 商品删除成功', 'success');
            await loadProducts(); // 重新加载列表
        } else {
            const result = await response.json();
            showMessage('❌ ' + result.error, 'error');
        }
    } catch (error) {
        console.error('❌ 删除失败:', error);
        showMessage('删除失败: ' + error.message, 'error');
    }
}

// 设置示例URL
function setExampleUrl(platform) {
    const examples = {
        'taobao': 'https://item.taobao.com/item.htm?id=674255942670',
        'jd': 'https://item.jd.com/100038266593.html',
        'tmall': 'https://detail.tmall.com/item.htm?id=677654328790',
        'pdd': 'https://yangkeduo.com/goods.html?goods_id=123456789'
    };
    
    elements.productUrl.value = examples[platform] || '';
    showMessage(`已填入${getPlatformName(platform)}示例链接`, 'success');
}

// 显示帮助
function showHelp() {
    openModal('helpModal');
}

// 导出数据
function exportData() {
    const data = {
        exportTime: new Date().toISOString(),
        products: state.products
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `price-tracker-export-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showMessage('📥 数据导出成功', 'success');
}

// 工具函数
function formatPrice(price) {
    return parseFloat(price || 0).toFixed(2);
}

function formatRelativeTime(dateString) {
    if (!dateString) return '未知';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    if (diffDays < 7) return `${diffDays}天前`;
    
    return date.toLocaleDateString('zh-CN');
}

function formatDateTime(dateString) {
    if (!dateString) return '未知';
    return new Date(dateString).toLocaleString('zh-CN');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getPlatformName(platform) {
    const names = {
        'taobao': '淘宝',
        'tmall': '天猫',
        'jd': '京东',
        'pdd': '拼多多',
        'other': '其他'
    };
    return names[platform] || platform;
}

function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        state.currentModal = modalId;
    }
}

function closeModal() {
    if (state.currentModal) {
        const modal = document.getElementById(state.currentModal);
        if (modal) {
            modal.style.display = 'none';
            state.currentModal = null;
        }
    }
}

function closeHelp() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function openOriginalLink(url) {
    window.open(url, '_blank');
}

function handleImageError(img) {
    img.style.display = 'none';
    const parent = img.parentElement;
    parent.innerHTML = `
        <div class="image-placeholder">
            <div class="placeholder-icon">❌</div>
            <div>图片加载失败</div>
        </div>
    `;
}

function showMessage(text, type) {
    // 移除现有消息
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.innerHTML = text;
    
    document.querySelector('.main-content').insertBefore(message, document.querySelector('.card'));
    
    setTimeout(() => {
        message.remove();
    }, 5000);
}

function updateLastUpdateTime() {
    elements.lastUpdate.textContent = `最后更新: ${new Date().toLocaleTimeString('zh-CN')}`;
}

// 带超时的fetch
async function fetchWithTimeout(resource, options = {}) {
    const { timeout = 8000 } = options;
    
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(resource, {
        ...options,
        signal: controller.signal  
    });
    
    clearTimeout(id);
    return response;
}

// 设置事件监听器
function setupEventListeners() {
    // 回车键添加商品
    elements.productUrl.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addProduct();
        }
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
                state.currentModal = null;
            }
        });
    });
    
    // 刷新按钮
    elements.refreshBtn.addEventListener('click', async function() {
        this.disabled = true;
        await loadProducts();
        this.disabled = false;
    });
}

// 启动后台任务
function startBackgroundTasks() {
    // 定期检查更新
    setInterval(async () => {
        try {
            await loadProducts();
        } catch (error) {
            console.error('后台更新失败:', error);
        }
    }, CONFIG.UPDATE_INTERVAL);
    
    // 定期检查服务器状态
    setInterval(async () => {
        try {
            await testServerConnection();
        } catch (error) {
            console.error('服务器状态检查失败:', error);
        }
    }, 60000); // 每分钟检查一次
}

// 错误处理
window.addEventListener('error', function(e) {
    console.error('全局错误:', e.error);
    showMessage('系统出现错误，请刷新页面重试', 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('未处理的Promise拒绝:', e.reason);
    showMessage('网络请求失败，请检查连接', 'error');
    e.preventDefault();
});

console.log("🎯 每日价格追踪系统前端加载完成");