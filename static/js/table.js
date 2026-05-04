let tableState = { page: 1, perPage: 25, search: '', category: '' };

async function loadTable() {
    try {
        const query = new URLSearchParams({
            page: tableState.page,
            per_page: tableState.perPage,
            ...(tableState.search && { search: tableState.search }),
            ...(tableState.category && { category: tableState.category })
        });

        const data = await api(`/api/products?${query}`);
        renderTable(data.products);
        updatePagination(data);
    } catch (e) {
        showToast('Failed to load products', 'error');
    }
}

function renderTable(products) {
    const tbody = document.getElementById('products-tbody');
    if (!products || products.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-state">
            <div class="empty-state-icon">📦</div>
            No products found.
        </td></tr>`;
        return;
    }

    tbody.innerHTML = products.map(p => {
        const currentPrice = p.current_price !== null ? parseFloat(p.current_price) : null;
        const origPrice = p.original_price !== null ? parseFloat(p.original_price) : null;
        const currentStr = currentPrice !== null ? `$${currentPrice.toFixed(2)}` : 'N/A';
        const origStr = origPrice !== null ? `$${origPrice.toFixed(2)}` : 'N/A';

        // Calculate change
        let changeHtml = '<span style="color: var(--text-muted)">—</span>';
        if (currentPrice !== null && origPrice !== null && origPrice !== 0) {
            const diff = currentPrice - origPrice;
            const pct = ((diff / origPrice) * 100).toFixed(1);
            if (diff < 0) {
                changeHtml = `<span style="color: var(--emerald); font-weight: 600;">↓ ${Math.abs(pct)}%</span>`;
            } else if (diff > 0) {
                changeHtml = `<span style="color: var(--rose); font-weight: 600;">↑ ${pct}%</span>`;
            } else {
                changeHtml = `<span style="color: var(--text-muted);">— 0%</span>`;
            }
        }

        const titleSafe = p.title.replace(/'/g, "\\'").replace(/"/g, '&quot;');

        return `
            <tr>
                <td>
                    <div class="product-name">${p.title.substring(0, 55)}${p.title.length > 55 ? '...' : ''}</div>
                    <a href="${p.url}" target="_blank" class="product-link">View Product ↗</a>
                </td>
                <td><span class="badge cat-badge">${p.category || '—'}</span></td>
                <td style="font-weight: 600;">${currentStr}</td>
                <td style="color: var(--text-muted);">${origStr}</td>
                <td>${changeHtml}</td>
                <td>
                    ${p.in_stock
                        ? '<span class="badge stock-in">In Stock</span>'
                        : '<span class="badge stock-out">Out of Stock</span>'}
                </td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="viewHistory(${p.id}, '${titleSafe}')">
                        📈 History
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function updatePagination(data) {
    const totalPages = data.total_pages || 1;
    const start = data.total === 0 ? 0 : (data.page - 1) * data.per_page + 1;
    const end = Math.min(data.page * data.per_page, data.total);
    document.getElementById('page-info').textContent = `Showing ${start}–${end} of ${data.total} products`;
    document.getElementById('btn-prev').disabled = data.page <= 1;
    document.getElementById('btn-next').disabled = data.page >= totalPages;
}

let searchTimeout;
function handleSearch(value) {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        tableState.search = value;
        tableState.page = 1;
        loadTable();
    }, 300);
}

function handleCategoryFilter(value) {
    tableState.category = value;
    tableState.page = 1;
    loadTable();
}

function prevPage() { if (tableState.page > 1) { tableState.page--; loadTable(); } }
function nextPage() { tableState.page++; loadTable(); }

function exportData(format) {
    const params = new URLSearchParams();
    if (tableState.search) params.set('search', tableState.search);
    if (tableState.category) params.set('category', tableState.category);

    const url = `/api/export/${format}?${params.toString()}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = '';
    document.body.appendChild(a);
    a.click();
    a.remove();
    showToast(`Exporting as ${format.toUpperCase()}...`, 'success');
}

async function clearAllData() {
    if (confirm('Delete all tracked products and price history? This cannot be undone.')) {
        await api('/api/clear', { method: 'DELETE' });
        refreshAll();
        showToast('All data cleared', 'success');
    }
}
