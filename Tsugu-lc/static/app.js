const API_BASE = 'http://localhost:5000/api';
let priceChart = null;

// 页面加载
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 页面加载完成");
    loadProducts();
});

// 测试连接
async function testConnection() {
    try {
        console.log("🔗 测试后端连接...");
        const response = await fetch(`${API_BASE}/test`);
        
        if (!response.ok) {
            throw new Error(`HTTP错误! 状态码: ${response.status}`);
        }
        
        const result = await response.json();
        console.log("✅ 后端连接正常:", result);
        showMessage('✅ 后端服务连接正常', 'success');
        return true;
    } catch (error) {
        console.error('❌ 后端连接失败:', error);
        showMessage('❌ 后端服务连接失败: ' + error.message, 'error');
        return false;
    }
}

// 设置示例URL
function setExampleUrl(platform) {
    const urlInput = document.getElementById('productUrl');
    if (platform === 'taobao') {
        urlInput.value = 'https://item.taobao.com/item.htm?id=674255942670';
    } else if (platform === 'jd') {
        urlInput.value = 'https://item.jd.com/100038266593.html';
    }
    showMessage('已填入示例链接，点击"开始监控"测试', 'success');
}

// 加载商品列表
async function loadProducts() {
    const productsList = document.getElementById('productsList');
    productsList.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        console.log("📦 正在加载商品列表...");
        const response = await fetch(`${API_BASE}/products`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const products = await response.json();
        console.log("✅ 加载到商品:", products);

        if (products.length === 0) {
            productsList.innerHTML = `
                <div class="loading">
                    <p>还没有监控商品</p>
                    <p>请使用上面的表单添加商品链接</p>
                    <p>或者点击"淘宝示例"/"京东示例"按钮测试</p>
                </div>
            `;
            return;
        }

        productsList.innerHTML = products.map(product => `
            <div class="product-card" onclick="showPriceChart(${product.id}, '${escapeHtml(product.name)}')">
                <div class="product-image">
                    ${product.image_url ? 
                        `<img src="${product.image_url}" alt="${product.name}" onerror="this.parentElement.innerHTML='🖼️ 图片加载失败'">` : 
                        '🖼️ 无图片'
                    }
                </div>
                <div class="product-name">${product.name}</div>
                <div class="product-price">¥${product.current_price || '0.00'}</div>
                <div class="product-platform">平台: ${product.platform || '未知'}</div>
                <div class="product-updated">更新: ${formatDate(product.last_updated)}</div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('❌ 加载失败:', error);
        productsList.innerHTML = `
            <div class="message error">
                <p>加载失败</p>
                <p>错误信息: ${error.message}</p>
                <p>请检查后端服务是否正常运行</p>
            </div>
        `;
    }
}

// 添加商品
async function addProduct() {
    const urlInput = document.getElementById('productUrl');
    const url = urlInput.value.trim();

    if (!url) {
        showMessage('请输入商品链接', 'error');
        return;
    }

    try {
        console.log("🔄 正在添加商品:", url);
        const response = await fetch(`${API_BASE}/products`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const result = await response.json();
        console.log("✅ 添加商品响应:", result);

        if (response.ok) {
            showMessage('🎉 商品添加成功！', 'success');
            urlInput.value = '';
            // 延迟一下再加载，确保数据已保存
            setTimeout(loadProducts, 500);
        } else {
            showMessage(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('❌ 添加失败:', error);
        showMessage('❌ 网络错误，请检查后端服务', 'error');
    }
}

// 显示价格图表
async function showPriceChart(productId, productName) {
    try {
        console.log("📊 加载价格历史:", productId);
        const response = await fetch(`${API_BASE}/products/${productId}/prices`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const prices = await response.json();
        console.log("✅ 价格数据:", prices);

        const modal = document.getElementById('chartModal');
        const chartTitle = document.getElementById('chartTitle');
        
        chartTitle.textContent = `${productName} - 价格历史`;
        modal.style.display = 'block';

        renderChart(prices, productName);
    } catch (error) {
        console.error('❌ 加载图表失败:', error);
        showMessage('❌ 加载价格历史失败: ' + error.message, 'error');
    }
}

// 渲染图表
function renderChart(prices, productName) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    // 销毁之前的图表
    if (priceChart) {
        priceChart.destroy();
    }
    
    const labels = prices.map((p, index) => `记录 ${index + 1}`);
    const data = prices.map(p => p.price);
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: productName,
                data: data,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: '价格趋势图'
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: '价格 (元)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '时间点'
                    }
                }
            }
        }
    });
}

// 关闭模态框
function closeModal() {
    document.getElementById('chartModal').style.display = 'none';
}

// 显示消息
function showMessage(text, type) {
    // 移除现有消息
    const existingMessages = document.querySelectorAll('.message');
    existingMessages.forEach(msg => msg.remove());
    
    const message = document.createElement('div');
    message.className = `message ${type}`;
    message.textContent = text;
    
    document.querySelector('.main-content').insertBefore(message, document.querySelector('.card'));
    
    setTimeout(() => {
        message.remove();
    }, 4000);
}

// 工具函数
function formatDate(dateString) {
    if (!dateString) return '未知';
    try {
        return new Date(dateString).toLocaleDateString('zh-CN');
    } catch {
        return '未知';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('chartModal');
    if (event.target === modal) {
        closeModal();
    }
}

// 回车键添加商品
document.getElementById('productUrl').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        addProduct();
    }
});

// 测试API连接
async function testConnection() {
    try {
        const response = await fetch(`${API_BASE}/test`);
        const result = await response.json();
        console.log("✅ API连接测试:", result);
    } catch (error) {
        console.error("❌ API连接失败:", error);
    }
}

// 页面加载时测试连接
testConnection();