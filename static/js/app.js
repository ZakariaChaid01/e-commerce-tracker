let eventSource = null;

async function api(endpoint, options = {}) {
    const res = await fetch(endpoint, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}

function showToast(msg, type = 'info') {
    const div = document.createElement('div');
    div.className = `toast ${type}`;
    div.textContent = msg;
    document.getElementById('toast-container').appendChild(div);
    setTimeout(() => {
        div.style.opacity = '0';
        div.style.transform = 'translateX(30px)';
        div.style.transition = 'all 0.3s ease';
        setTimeout(() => div.remove(), 300);
    }, 3000);
}

function openConfigModal() { document.getElementById('config-modal').classList.remove('hidden'); }
function closeConfigModal() { document.getElementById('config-modal').classList.add('hidden'); }
function openHistoryModal() { document.getElementById('history-modal').classList.remove('hidden'); }
function closeHistoryModal() { document.getElementById('history-modal').classList.add('hidden'); }

async function saveConfig() {
    const key = document.getElementById('serpapi-key').value;
    try {
        await api('/api/config/serpapi', { method: 'POST', body: JSON.stringify({ key }) });
        showToast('Config saved successfully', 'success');
        closeConfigModal();
    } catch (e) { showToast(e.message, 'error'); }
}

async function loadStats() {
    try {
        const data = await api('/api/stats');
        animateValue('stat-total', data.stats.total_products);
        animateValue('stat-out-of-stock', data.stats.out_of_stock);
        animateValue('stat-price-drops', data.stats.price_drops);
        document.getElementById('stat-avg-price').textContent = `$${data.stats.avg_price.toFixed(2)}`;
        animateValue('stat-categories', data.stats.total_categories);
        document.getElementById('stat-stock-pct').textContent = `${data.stats.in_stock_pct}%`;

        const catSelect = document.getElementById('category-filter');
        const currentCat = catSelect.value;
        catSelect.innerHTML = '<option value="">All Categories</option>';
        data.categories.forEach(cat => {
            catSelect.innerHTML += `<option value="${cat}" ${cat === currentCat ? 'selected' : ''}>${cat}</option>`;
        });
    } catch (e) {
        console.error('Failed to load stats:', e);
    }
}

function animateValue(id, target) {
    const el = document.getElementById(id);
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    const duration = 600;
    const start = performance.now();
    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(current + (target - current) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

async function loadAnalytics() {
    try {
        const data = await api('/api/analytics');
        renderPriceDistribution(data.price_distribution);
        renderStockChart(data.stock_status);
        renderCategoryChart(data.categories);
        renderCategoryPriceChart(data.category_ranges);
        renderTopDrops(data.top_drops);
        renderTopIncreases(data.top_increases);
    } catch (e) {
        console.error('Failed to load analytics:', e);
    }
}

function renderTopDrops(drops) {
    const el = document.getElementById('top-drops-list');
    if (!drops || drops.length === 0) {
        el.innerHTML = '<div class="empty-state">No price drops detected yet.</div>';
        return;
    }
    el.innerHTML = drops.map(d => {
        const diff = (d.original_price - d.current_price).toFixed(2);
        const pct = ((diff / d.original_price) * 100).toFixed(1);
        return `<div class="mover-item">
            <div>
                <div class="mover-title">${d.title.substring(0, 45)}${d.title.length > 45 ? '...' : ''}</div>
                <div class="mover-prices">$${d.original_price.toFixed(2)} → $${d.current_price.toFixed(2)}</div>
            </div>
            <span class="mover-change drop">-$${diff} (${pct}%)</span>
        </div>`;
    }).join('');
}

function renderTopIncreases(increases) {
    const el = document.getElementById('top-increases-list');
    if (!increases || increases.length === 0) {
        el.innerHTML = '<div class="empty-state">No price increases detected yet.</div>';
        return;
    }
    el.innerHTML = increases.map(d => {
        const diff = (d.current_price - d.original_price).toFixed(2);
        const pct = ((diff / d.original_price) * 100).toFixed(1);
        return `<div class="mover-item">
            <div>
                <div class="mover-title">${d.title.substring(0, 45)}${d.title.length > 45 ? '...' : ''}</div>
                <div class="mover-prices">$${d.original_price.toFixed(2)} → $${d.current_price.toFixed(2)}</div>
            </div>
            <span class="mover-change increase">+$${diff} (${pct}%)</span>
        </div>`;
    }).join('');
}

async function startScraping() {
    const keyword = document.getElementById('keyword-input').value;
    const mode = document.getElementById('mode-select').value;
    if (!keyword) return showToast('Please enter a keyword or category', 'error');

    try {
        await api('/api/scrape', { method: 'POST', body: JSON.stringify({ keyword, mode }) });
        document.getElementById('btn-scrape').classList.add('hidden');
        document.getElementById('btn-stop').classList.remove('hidden');
        document.getElementById('live-feed').classList.remove('hidden');
        document.getElementById('feed-counter').textContent = '0';

        eventSource = new EventSource('/api/scrape/stream');
        eventSource.onmessage = (e) => {
            const data = JSON.parse(e.data);
            if (data.type === 'product') {
                const count = parseInt(document.getElementById('feed-counter').textContent) + 1;
                document.getElementById('feed-counter').textContent = count;
            } else if (data.type === 'complete' || data.type === 'error') {
                stopScrapingUI();
                refreshAll();
                showToast(
                    data.type === 'complete'
                        ? `Tracking complete — ${data.count || 0} products found`
                        : 'Error: ' + data.message,
                    data.type === 'complete' ? 'success' : 'error'
                );
            }
        };
    } catch (e) { showToast(e.message, 'error'); }
}

async function stopScraping() {
    await api('/api/scrape/stop', { method: 'POST' });
    stopScrapingUI();
}

function stopScrapingUI() {
    if (eventSource) eventSource.close();
    document.getElementById('btn-scrape').classList.remove('hidden');
    document.getElementById('btn-stop').classList.add('hidden');
    document.getElementById('live-feed').classList.add('hidden');
}

function refreshAll() {
    loadStats();
    loadTable();
    loadAnalytics();
}

// Close modals on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.add('hidden');
    }
});

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal:not(.hidden)').forEach(m => m.classList.add('hidden'));
    }
});

document.addEventListener('DOMContentLoaded', () => {
    refreshAll();
    api('/api/config').then(data => {
        if (data.serpapi_configured) document.getElementById('serpapi-key').value = data.serpapi_key_preview;
    });
});
