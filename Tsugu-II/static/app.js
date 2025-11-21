// static/app.js
class PriceTrackerApp {
    constructor() {
        this.chart = null;
        this.currentProductId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadProducts();
    }

    bindEvents() {
        // 添加商品表单提交
        document.getElementById('addProductForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addProduct();
        });

        // 模态框关闭
        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        // 点击模态框外部关闭
        document.getElementById('historyModal').addEventListener('click', (e) => {
            if (e.target.id === 'historyModal') {
                this.closeModal();
            }
        });
    }

    async addProduct() {
        const form = document.getElementById('addProductForm');
        const formData = new FormData(form);
        const data = {
            url: formData.get('url'),
            target_price: formData.get('target_price') || null
        };

        this.showLoading(true);
        this.hideMessage();

        try {
            const response = await fetch('/api/add_product', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                this.showMessage('商品添加成功！', 'success');
                form.reset();
                this.loadProducts();
            } else {
                this.showMessage(result.error || '添加商品失败', 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
            console.error('添加商品错误:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async loadProducts() {
        try {
            const response = await fetch('/');
            const text = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            const productsGrid = doc.querySelector('.products-grid');
            
            if (productsGrid) {
                document.getElementById('productsList').innerHTML = productsGrid.innerHTML;
                this.bindProductEvents();
                this.toggleEmptyState();
            }
        } catch (error) {
            console.error('加载商品列表错误:', error);
        }
    }

    bindProductEvents() {
        // 绑定检查价格按钮
        document.querySelectorAll('.btn-check-price').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = e.target.closest('.product-card').dataset.productId;
                this.checkPrice(productId);
            });
        });

        // 绑定查看历史按钮
        document.querySelectorAll('.btn-history').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = e.target.closest('.product-card').dataset.productId;
                this.showPriceHistory(productId);
            });
        });

        // 绑定删除按钮
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productId = e.target.closest('.product-card').dataset.productId;
                this.deleteProduct(productId);
            });
        });
    }

    async checkPrice(productId) {
        this.showLoading(true);

        try {
            const response = await fetch(`/api/check_price/${productId}`);
            const result = await response.json();

            if (result.success) {
                this.showMessage(`价格更新成功！当前价格: ¥${result.price}`, 'success');
                this.loadProducts();
            } else {
                this.showMessage(result.error || '检查价格失败', 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
            console.error('检查价格错误:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async showPriceHistory(productId) {
        this.showLoading(true);
        this.currentProductId = productId;

        try {
            const response = await fetch(`/api/price_history/${productId}`);
            const result = await response.json();

            if (result.success) {
                this.renderPriceChart(result.history);
                this.renderPriceTable(result.history);
                this.openModal();
            } else {
                this.showMessage(result.error || '获取价格历史失败', 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
            console.error('获取价格历史错误:', error);
        } finally {
            this.showLoading(false);
        }
    }

    renderPriceChart(history) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        // 销毁之前的图表
        if (this.chart) {
            this.chart.destroy();
        }

        const labels = history.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('zh-CN');
        }).reverse();

        const prices = history.map(item => item.price).reverse();

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '价格趋势',
                    data: prices,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
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
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '¥' + value;
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderPriceTable(history) {
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = '';

        history.forEach(item => {
            const row = document.createElement('tr');
            const date = new Date(item.date);
            
            row.innerHTML = `
                <td>${date.toLocaleString('zh-CN')}</td>
                <td>¥${item.price}</td>
            `;
            
            tbody.appendChild(row);
        });
    }

    async deleteProduct(productId) {
        if (!confirm('确定要删除这个商品吗？')) {
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch(`/api/delete_product/${productId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showMessage('商品删除成功', 'success');
                this.loadProducts();
                this.closeModal();
            } else {
                this.showMessage(result.error || '删除商品失败', 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
            console.error('删除商品错误:', error);
        } finally {
            this.showLoading(false);
        }
    }

    openModal() {
        document.getElementById('historyModal').style.display = 'block';
    }

    closeModal() {
        document.getElementById('historyModal').style.display = 'none';
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    toggleEmptyState() {
        const productsList = document.getElementById('productsList');
        const emptyState = document.getElementById('emptyState');
        
        if (productsList.children.length === 0) {
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
        }
    }

    showMessage(message, type) {
        const messageEl = document.getElementById('formMessage');
        messageEl.textContent = message;
        messageEl.className = `message ${type}`;
        messageEl.style.display = 'block';

        // 3秒后自动隐藏
        setTimeout(() => {
            this.hideMessage();
        }, 3000);
    }

    hideMessage() {
        const messageEl = document.getElementById('formMessage');
        messageEl.style.display = 'none';
    }

    showLoading(show) {
        const loadingEl = document.getElementById('loading');
        loadingEl.style.display = show ? 'flex' : 'none';
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new PriceTrackerApp();
});

// 工具函数：格式化价格显示
function formatPrice(price) {
    return '¥' + parseFloat(price).toFixed(2);
}

// 工具函数：缩短URL显示
function shortenUrl(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.hostname + urlObj.pathname.substring(0, 30) + '...';
    } catch {
        return url.substring(0, 50) + '...';
    }
}