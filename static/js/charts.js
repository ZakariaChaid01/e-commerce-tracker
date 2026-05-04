/* ========== Chart.js Global Defaults ========== */
Chart.defaults.color = '#7c85a3';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
Chart.defaults.plugins.legend.labels.padding = 16;

const chartInstances = {};

function destroyChart(key) {
    if (chartInstances[key]) {
        chartInstances[key].destroy();
        delete chartInstances[key];
    }
}

/* ========== Price Distribution (Bar) ========== */
function renderPriceDistribution(dist) {
    destroyChart('priceDist');
    const ctx = document.getElementById('chart-price-dist');
    if (!dist || !dist.labels.length) return;

    chartInstances.priceDist = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dist.labels,
            datasets: [{
                label: 'Products',
                data: dist.values,
                backgroundColor: createGradientBar(ctx, '#6366f1', '#a855f7'),
                borderRadius: 6,
                borderSkipped: false,
                maxBarThickness: 48,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(13,15,20,0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { weight: '600' },
                    callbacks: {
                        label: (ctx) => `${ctx.parsed.y} products`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { precision: 0 }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } }
                }
            }
        }
    });
}

function createGradientBar(canvas, color1, color2) {
    const ctx2d = canvas.getContext('2d');
    const gradient = ctx2d.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2 + '66');
    return gradient;
}

/* ========== Stock Status (Doughnut) ========== */
function renderStockChart(stock) {
    destroyChart('stock');
    const ctx = document.getElementById('chart-stock');
    if (!stock || (stock.in_stock === 0 && stock.out_of_stock === 0)) return;

    chartInstances.stock = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['In Stock', 'Out of Stock'],
            datasets: [{
                data: [stock.in_stock, stock.out_of_stock],
                backgroundColor: ['#34d399', '#fb7185'],
                borderColor: 'transparent',
                borderWidth: 0,
                spacing: 3,
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20, font: { size: 12, weight: '500' } }
                },
                tooltip: {
                    backgroundColor: 'rgba(13,15,20,0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((ctx.parsed / total) * 100).toFixed(1);
                            return `${ctx.label}: ${ctx.parsed} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

/* ========== Category Breakdown (Horizontal Bar) ========== */
function renderCategoryChart(categories) {
    destroyChart('categories');
    const ctx = document.getElementById('chart-categories');
    if (!categories || !categories.length) return;

    const colors = ['#6366f1', '#8b5cf6', '#a855f7', '#22d3ee', '#34d399', '#fbbf24', '#fb7185', '#a78bfa', '#f472b6', '#38bdf8'];

    chartInstances.categories = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories.map(c => c.category.length > 20 ? c.category.substring(0, 20) + '...' : c.category),
            datasets: [{
                label: 'Products',
                data: categories.map(c => c.count),
                backgroundColor: categories.map((_, i) => colors[i % colors.length] + 'cc'),
                borderRadius: 6,
                borderSkipped: false,
                maxBarThickness: 32,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(13,15,20,0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        afterLabel: (ctx) => {
                            const cat = categories[ctx.dataIndex];
                            return cat.avg_price ? `Avg: $${cat.avg_price}` : '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { precision: 0 }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } }
                }
            }
        }
    });
}

/* ========== Category Avg Price (Bar) ========== */
function renderCategoryPriceChart(ranges) {
    destroyChart('catPrices');
    const ctx = document.getElementById('chart-cat-prices');
    if (!ranges || !ranges.length) return;

    chartInstances.catPrices = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ranges.map(r => r.category.length > 18 ? r.category.substring(0, 18) + '...' : r.category),
            datasets: [
                {
                    label: 'Avg Price',
                    data: ranges.map(r => r.avg_price),
                    backgroundColor: 'rgba(99, 102, 241, 0.7)',
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 36,
                },
                {
                    label: 'Min',
                    data: ranges.map(r => r.min_price),
                    backgroundColor: 'rgba(52, 211, 153, 0.5)',
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 36,
                },
                {
                    label: 'Max',
                    data: ranges.map(r => r.max_price),
                    backgroundColor: 'rgba(251, 113, 133, 0.5)',
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 36,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { size: 11 }, padding: 12 }
                },
                tooltip: {
                    backgroundColor: 'rgba(13,15,20,0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.y.toFixed(2)}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.04)' },
                    ticks: { callback: v => '$' + v }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 } }
                }
            }
        }
    });
}

/* ========== Price History Modal Chart ========== */
let priceChart = null;

async function viewHistory(productId, title) {
    document.getElementById('history-modal-title').textContent = title;
    openHistoryModal();

    try {
        const data = await api(`/api/products/${productId}/history`);
        renderPriceHistoryChart(data.history);
    } catch (e) {
        showToast('Failed to load history', 'error');
    }
}

function renderPriceHistoryChart(history) {
    const ctx = document.getElementById('price-chart').getContext('2d');

    if (priceChart) priceChart.destroy();

    const dates = history.map(h => {
        const d = new Date(h.timestamp);
        return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    const prices = history.map(h => h.price);

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.01)');

    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Price ($)',
                data: prices,
                borderColor: '#6366f1',
                backgroundColor: gradient,
                borderWidth: 2.5,
                pointBackgroundColor: '#6366f1',
                pointBorderColor: '#fff',
                pointBorderWidth: 1.5,
                pointRadius: 4,
                pointHoverRadius: 7,
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: 'rgba(255, 255, 255, 0.06)' },
                    ticks: { color: '#7c85a3', callback: v => '$' + v.toFixed(2) }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#7c85a3', maxRotation: 45, minRotation: 45, font: { size: 10 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(13,15,20,0.95)',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: (ctx) => `Price: $${ctx.parsed.y.toFixed(2)}`
                    }
                }
            }
        }
    });
}
