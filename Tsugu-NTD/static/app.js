// static/app.js
class PriceTrackerApp {
    constructor() {
        this.chart = null;
        this.currentProductId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateProductCount();
    }

    bindEvents() {
        // 添加商品表单提交
        document.getElementById('addProductForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addProduct();
        });

        // 刷新按钮
        document.getElementById('refreshProducts').addEventListener('click', () => {
            location.reload();
        });

        // 重置演示数据
        document.getElementById('resetDemo').addEventListener('click', () => {
            this.resetDemoData();
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

        // 绑定商品操作事件
        this.bindProductEvents();
    }

    bindProductEvents() {
        // 绑定检查价格按钮
        document.querySelectorAll('.btn-check-price').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productCard = e.target.closest('.product-card');
                const productId = productCard.dataset.productId;
                this.checkPrice(productId);
            });
        });

        // 绑定查看历史按钮
        document.querySelectorAll('.btn-history').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productCard = e.target.closest('.product-card');
                const productId = productCard.dataset.productId;
                this.showPriceHistory(productId);
            });
        });

        // 绑定删除按钮
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const productCard = e.target.closest('.product-card');
                const productId = productCard.dataset.productId;
                const productName = productCard.querySelector('.product-name').textContent;
                this.deleteProduct(productId, productName);
            });
        });
    }

    updateProductCount() {
        const count = document.querySelectorAll('.product-card').length;
        document.getElementById('productCount').textContent = `${count} 个商品`;
    }

    async addProduct() {
        const form = document.getElementById('addProductForm');
        const formData = new FormData(form);
        const url = formData.get('url');
        const targetPrice = formData.get('target_price');
        const productName = formData.get('name');

        if (!url) {
            this.showMessage('请输入商品链接', 'error');
            return;
        }

        this.showLoading(true);

        const data = {
            url: url,
            target_price: targetPrice || null,
            name: productName || `商品 ${new Date().toLocaleTimeString()}`
        };

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
                this.showMessage(result.message, 'success');
                form.reset();
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showMessage(result.error, 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
            console.error('添加商品错误:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async checkPrice(productId) {
        const button = document.querySelector(`[data-product-id="${productId}"] .btn-check-price`);
        const originalText = button.innerHTML;
        
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 检查中...';
        button.disabled = true;

        try {
            const response = await fetch(`/api/check_price/${productId}`);
            const result = await response.json();

            if (result.success) {
                this.showMessage(result.message, 'success');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showMessage(result.error, 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
        } finally {
            button.innerHTML = originalText;
            button.disabled = false;
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
                this.showMessage(result.error, 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderPriceChart(history) {
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        const sortedHistory = [...history].reverse();
        const labels = sortedHistory.map((item, index) => {
            if (index === 0 || index === sortedHistory.length - 1 || index % 5 === 0) {
                return new Date(item.date).toLocaleDateString();
            }
            return '';
        });

        const prices = sortedHistory.map(item => item.price);

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
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '¥' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    renderPriceTable(history) {
        const tbody = document.getElementById('historyTableBody');
        tbody.innerHTML = '';

        history.forEach((item, index) => {
            const row = document.createElement('tr');
            const date = new Date(item.date);
            
            if (index === 0) {
                row.classList.add('latest-record');
            }
            
            row.innerHTML = `
                <td>${date.toLocaleString()}</td>
                <td>¥${item.price.toFixed(2)}</td>
            `;
            
            tbody.appendChild(row);
        });
    }

    async deleteProduct(productId, productName) {
        if (!confirm(`确定要删除商品 "${productName}" 吗？`)) {
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
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showMessage(result.error, 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async resetDemoData() {
        if (!confirm('确定要重置所有数据吗？这将删除所有商品。')) {
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/api/demo/reset');
            const result = await response.json();

            if (result.success) {
                this.showMessage('数据重置成功', 'success');
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                this.showMessage(result.error, 'error');
            }
        } catch (error) {
            this.showMessage('网络错误，请稍后重试', 'error');
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

    showMessage(message, type) {
        const messageEl = document.getElementById('formMessage');
        messageEl.textContent = message;
        messageEl.className = `message ${type}`;
        messageEl.style.display = 'block';

        setTimeout(() => {
            messageEl.style.display = 'none';
        }, 3000);
    }

    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'flex' : 'none';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new PriceTrackerApp();
});