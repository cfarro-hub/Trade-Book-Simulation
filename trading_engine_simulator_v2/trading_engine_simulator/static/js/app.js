/* ─────────────────────────────────────────────────────
   TradeSim v2.1 — Frontend with REAL Binance Data
   ───────────────────────────────────────────────────── */

// ═══════════════════════════ STATE ════════════════════
let currentSymbol = 'BTCUSDT';
let ws = null;
let chart = null;
let candleSeries = null;
let volumeSeries = null;
let currentCandle = null;
let reconnectAttempts = 0;
let subscribedChannels = [];
let bookRefreshInterval = null;

const PRICE_DECIMALS = {
    BTCUSDT: 2, ETHUSDT: 2, BNBUSDT: 2,
    SOLUSDT: 2, XRPUSDT: 4
};

function dp(symbol) { return PRICE_DECIMALS[symbol] || 2; }

// ═══════════════════════════ WEBSOCKET ════════════════

function initWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws`);

    ws.onopen = () => {
        reconnectAttempts = 0;
        setWsStatus(true);
        subscribe(`trades:${currentSymbol}`);
        subscribe(`book:${currentSymbol}`);
        subscribe('orders');
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        switch (msg.type) {
            case 'trade':       handleTrade(msg.data); break;
            case 'book_update': renderOrderBook(msg.data); break;
            case 'order_update': handleOrderUpdate(msg.data); break;
        }
    };

    ws.onclose = () => {
        setWsStatus(false);
        reconnectAttempts++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        setTimeout(initWebSocket, delay);
    };

    ws.onerror = () => { ws.close(); };
}

function subscribe(channel) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'subscribe', channel }));
        if (!subscribedChannels.includes(channel)) subscribedChannels.push(channel);
    }
}

function unsubscribe(channel) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'unsubscribe', channel }));
    }
    subscribedChannels = subscribedChannels.filter(c => c !== channel);
}

function setWsStatus(online) {
    document.getElementById('ws-dot').className = 'ws-dot ' + (online ? 'online' : 'offline');
    document.getElementById('ws-label').textContent = online ? 'Connected' : 'Disconnected';
}

// ═══════════════════════════ CHART ════════════════════

function initChart() {
    const container = document.getElementById('chart-container');
    chart = LightweightCharts.createChart(container, {
        width: container.clientWidth,
        height: container.clientHeight,
        layout: {
            background: { type: 'solid', color: '#1a1f2e' },
            textColor: '#8b949e',
        },
        grid: {
            vertLines: { color: '#2a2f3e' },
            horzLines: { color: '#2a2f3e' },
        },
        crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
        rightPriceScale: { borderColor: '#30363d' },
        timeScale: { borderColor: '#30363d', timeVisible: true, secondsVisible: false },
    });

    candleSeries = chart.addCandlestickSeries({
        upColor: '#00d09c', downColor: '#ff5252',
        borderUpColor: '#00d09c', borderDownColor: '#ff5252',
        wickUpColor: '#00d09c', wickDownColor: '#ff5252',
    });

    volumeSeries = chart.addHistogramSeries({
        priceFormat: { type: 'volume' },
        priceScaleId: '',
    });
    volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.85, bottom: 0 },
    });

    window.addEventListener('resize', () => {
        chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
    });
}

async function loadRealKlines(symbol, interval = '1m', limit = 300) {
    try {
        const resp = await fetch(`/market/klines/${symbol}?interval=${interval}&limit=${limit}`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const candles = await resp.json();
        if (!candles.length) return;

        candleSeries.setData(candles.map(c => ({
            time: c.time, open: c.open, high: c.high, low: c.low, close: c.close,
        })));

        volumeSeries.setData(candles.map(c => ({
            time: c.time, value: c.volume,
            color: c.close >= c.open ? '#00d09c80' : '#ff525280',
        })));

        const last = candles[candles.length - 1];
        currentCandle = {
            time: last.time, open: last.open, high: last.high,
            low: last.low, close: last.close, volume: last.volume,
        };

        updateWatchlistPrice(symbol, last.close);
        document.getElementById('stat-last').textContent = last.close.toFixed(dp(symbol));
        chart.timeScale().fitContent();
    } catch (e) {
        console.error('Failed to load klines:', e);
        showToast('Could not load chart data from Binance', 'error');
    }
}

function handleTrade(trade) {
    if (trade.symbol !== currentSymbol) {
        updateWatchlistPrice(trade.symbol, trade.price);
        return;
    }

    const ts = Math.floor(new Date(trade.timestamp).getTime() / 1000);
    const candleTime = ts - (ts % 60);
    const price = trade.price;
    const qty = trade.quantity;

    if (currentCandle && currentCandle.time === candleTime) {
        currentCandle.high = Math.max(currentCandle.high, price);
        currentCandle.low = Math.min(currentCandle.low, price);
        currentCandle.close = price;
        currentCandle.volume += qty;
    } else {
        currentCandle = {
            time: candleTime, open: price, high: price,
            low: price, close: price, volume: qty,
        };
    }

    candleSeries.update({
        time: currentCandle.time, open: currentCandle.open,
        high: currentCandle.high, low: currentCandle.low, close: currentCandle.close,
    });
    volumeSeries.update({
        time: currentCandle.time, value: currentCandle.volume,
        color: currentCandle.close >= currentCandle.open ? '#00d09c80' : '#ff525280',
    });

    updateWatchlistPrice(trade.symbol, price);
    addTradeToFeed(trade);
    document.getElementById('stat-last').textContent = price.toFixed(dp(trade.symbol));
}

function updateWatchlistPrice(symbol, price) {
    const el = document.getElementById(`wl-price-${symbol}`);
    if (el) { el.textContent = price.toFixed(dp(symbol)); el.style.color = '#e1e4e8'; }
}

// ═══════════════════════════ ORDER BOOK ═══════════════

function renderOrderBook(data) {
    if (!data) return;
    const bidsEl = document.getElementById('bids-list');
    const asksEl = document.getElementById('asks-list');
    const spreadEl = document.getElementById('book-spread');
    const bids = data.bids || [];
    const asks = data.asks || [];
    const allQty = [...bids.map(b => b.quantity), ...asks.map(a => a.quantity)];
    const maxQty = Math.max(...allQty, 0.001);

    let bidTotal = 0;
    bidsEl.innerHTML = bids.length ? bids.map(b => {
        bidTotal += b.quantity;
        const pct = (b.quantity / maxQty * 100).toFixed(1);
        return `<div class="book-row">
            <div class="book-bar" style="width:${pct}%"></div>
            <span class="price">${b.price.toFixed(dp(currentSymbol))}</span>
            <span>${b.quantity.toFixed(4)}</span>
            <span>${bidTotal.toFixed(4)}</span>
        </div>`;
    }).join('') : '<div class="empty-state">No bids</div>';

    let askTotal = 0;
    asksEl.innerHTML = asks.length ? asks.map(a => {
        askTotal += a.quantity;
        const pct = (a.quantity / maxQty * 100).toFixed(1);
        return `<div class="book-row">
            <div class="book-bar" style="width:${pct}%"></div>
            <span class="price">${a.price.toFixed(dp(currentSymbol))}</span>
            <span>${a.quantity.toFixed(4)}</span>
            <span>${askTotal.toFixed(4)}</span>
        </div>`;
    }).join('') : '<div class="empty-state">No asks</div>';

    if (bids.length && asks.length) {
        const spread = asks[0].price - bids[0].price;
        spreadEl.textContent = `Spread: ${spread.toFixed(dp(currentSymbol))}`;
        document.getElementById('stat-bid').textContent = bids[0].price.toFixed(dp(currentSymbol));
        document.getElementById('stat-ask').textContent = asks[0].price.toFixed(dp(currentSymbol));
        document.getElementById('stat-spread').textContent = spread.toFixed(dp(currentSymbol));
    }
    if (data.last_trade_price) {
        document.getElementById('stat-last').textContent =
            data.last_trade_price.toFixed(dp(currentSymbol));
    }
}

// ═══════════════════════════ TRADES FEED ══════════════

function addTradeToFeed(trade) {
    const list = document.getElementById('trades-list');
    const time = new Date(trade.timestamp);
    const timeStr = time.toLocaleTimeString('en-GB', { hour12: false });
    const isBuy = trade.buyer_order_id === trade.taker_order_id;
    const sideClass = isBuy ? 'side-buy' : 'side-sell';
    const row = document.createElement('div');
    row.className = 'trade-row';
    row.innerHTML = `
        <span>${timeStr}</span>
        <span class="${sideClass}">${trade.price.toFixed(dp(currentSymbol))}</span>
        <span>${trade.quantity.toFixed(4)}</span>
        <span class="${sideClass}">${isBuy ? 'BUY' : 'SELL'}</span>
    `;
    list.prepend(row);
    while (list.children.length > 50) list.removeChild(list.lastChild);
}

// ═══════════════════════════ MY ORDERS ════════════════

function handleOrderUpdate() { fetchAndRenderOrders(); }

async function fetchAndRenderOrders() {
    try {
        const resp = await fetch('/orders');
        const orders = await resp.json();
        const list = document.getElementById('myorders-list');
        const relevant = orders.filter(o =>
            ['NEW', 'PARTIALLY_FILLED', 'PENDING_TRIGGER'].includes(o.status)
        ).reverse().slice(0, 50);

        if (!relevant.length) {
            list.innerHTML = '<div class="empty-state">No open orders</div>';
            return;
        }
        list.innerHTML = relevant.map(o => {
            const sc = o.side === 'BUY' ? 'buy' : 'sell';
            const canCancel = ['NEW', 'PARTIALLY_FILLED', 'PENDING_TRIGGER'].includes(o.status);
            return `<div class="order-row">
                <span>${o.symbol}</span>
                <span class="${sc}">${o.side}</span>
                <span>${o.type}</span>
                <span>${o.price ? o.price.toFixed(dp(o.symbol)) : '\u2014'}</span>
                <span>${o.original_quantity.toFixed(4)}</span>
                <span>${o.filled_quantity.toFixed(4)}</span>
                <span>${o.status}</span>
                <span>${canCancel ? `<button class="btn-cancel" onclick="cancelOrder('${o.order_id}')">Cancel</button>` : ''}</span>
            </div>`;
        }).join('');
    } catch (e) { console.error('Failed to fetch orders', e); }
}

async function cancelOrder(orderId) {
    try {
        const resp = await fetch(`/orders/${orderId}`, { method: 'DELETE' });
        const data = await resp.json();
        showToast(`Order canceled: ${data.status}`, 'info');
        fetchAndRenderOrders();
    } catch (e) { showToast('Failed to cancel order', 'error'); }
}

// ═══════════════════════════ ORDER FORM ═══════════════

function setupOrderForm() {
    const form = document.getElementById('order-form');
    const typeSelect = document.getElementById('order-type');
    const buyBtn = document.getElementById('side-buy');
    const sellBtn = document.getElementById('side-sell');
    const submitBtn = document.getElementById('submit-btn');
    const priceGroup = document.getElementById('price-group');
    const stopGroup = document.getElementById('stop-price-group');
    let currentSide = 'BUY';

    buyBtn.addEventListener('click', () => {
        currentSide = 'BUY';
        buyBtn.classList.add('active'); sellBtn.classList.remove('active');
        submitBtn.textContent = 'Place BUY Order';
        submitBtn.className = 'btn btn-submit btn-buy';
    });
    sellBtn.addEventListener('click', () => {
        currentSide = 'SELL';
        sellBtn.classList.add('active'); buyBtn.classList.remove('active');
        submitBtn.textContent = 'Place SELL Order';
        submitBtn.className = 'btn btn-submit btn-sell';
    });

    typeSelect.addEventListener('change', () => {
        const t = typeSelect.value;
        priceGroup.style.display = (t === 'MARKET') ? 'none' : 'flex';
        stopGroup.style.display = (t === 'STOP_LOSS' || t === 'STOP_LOSS_LIMIT') ? 'flex' : 'none';
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const orderType = typeSelect.value;
        const body = {
            symbol: currentSymbol, side: currentSide, type: orderType,
            quantity: parseFloat(document.getElementById('order-quantity').value),
            time_in_force: document.getElementById('order-tif').value,
        };
        if (orderType !== 'MARKET') {
            const pv = parseFloat(document.getElementById('order-price').value);
            if (!isNaN(pv) && pv > 0) body.price = pv;
        }
        if (orderType === 'STOP_LOSS' || orderType === 'STOP_LOSS_LIMIT') {
            const sp = parseFloat(document.getElementById('order-stop-price').value);
            if (!isNaN(sp) && sp > 0) body.stop_price = sp;
        }

        try {
            const resp = await fetch('/orders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await resp.json();
            if (data.status === 'REJECTED') showToast(`Rejected: ${data.reject_reason}`, 'error');
            else if (data.status === 'FILLED') showToast(`Order FILLED — ${data.filled_quantity} qty`, 'success');
            else showToast(`Order placed: ${data.status}`, 'success');
            document.getElementById('order-quantity').value = '';
            fetchAndRenderOrders();
        } catch (err) { showToast('Failed to submit order', 'error'); }
    });
}

// ═══════════════════════════ SEED MARKET ══════════════
// NOW USES REAL BINANCE DATA!

async function seedMarket() {
    showToast(`Fetching real Binance data for ${currentSymbol}...`, 'info');
    try {
        const resp = await fetch(`/market/seed/${currentSymbol}?depth=10`, { method: 'POST' });
        const data = await resp.json();
        if (resp.ok) showToast(data.message, 'success');
        else showToast(`Seed failed: ${data.detail || 'Unknown error'}`, 'error');
        setTimeout(() => { fetchAndRenderBook(); fetchAndRenderOrders(); }, 500);
    } catch (e) {
        showToast('Failed to seed — check internet connection', 'error');
    }
}

// ═══════════════════════════ FETCH DATA ═══════════════

async function fetchAndRenderBook() {
    try {
        const resp = await fetch(`/book/${currentSymbol}`);
        const data = await resp.json();
        renderOrderBook(data);
    } catch (e) { console.error('Failed to fetch book', e); }
}

async function fetchAndRenderTrades() {
    try {
        const resp = await fetch(`/trades/${currentSymbol}`);
        const trades = await resp.json();
        document.getElementById('trades-list').innerHTML = '';
        trades.reverse().forEach(addTradeToFeed);
    } catch (e) { console.error('Failed to fetch trades', e); }
}

// ═══════════════════════════ SYMBOL SWITCH ════════════

async function switchSymbol(symbol) {
    if (symbol === currentSymbol) return;
    unsubscribe(`trades:${currentSymbol}`);
    unsubscribe(`book:${currentSymbol}`);
    currentSymbol = symbol;

    document.querySelectorAll('.watchlist-item').forEach(el => {
        el.classList.toggle('active', el.dataset.symbol === symbol);
    });
    document.getElementById('symbol-select').value = symbol;

    currentCandle = null;
    candleSeries.setData([]);
    volumeSeries.setData([]);
    document.getElementById('trades-list').innerHTML = '';
    document.getElementById('bids-list').innerHTML = '<div class="empty-state">Loading...</div>';
    document.getElementById('asks-list').innerHTML = '<div class="empty-state">Loading...</div>';

    await loadRealKlines(symbol);

    subscribe(`trades:${currentSymbol}`);
    subscribe(`book:${currentSymbol}`);

    fetchAndRenderBook();
    fetchAndRenderTrades();
    fetchAndRenderOrders();
}

// ═══════════════════════════ TABS ═════════════════════

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(tc => {
        tc.classList.toggle('active', tc.id === `tab-${tabName}`);
    });
    if (tabName === 'myorders') fetchAndRenderOrders();
}

// ═══════════════════════════ TOAST ════════════════════

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('toast-fade');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ═══════════════════════════ INIT ═════════════════════

document.addEventListener('DOMContentLoaded', async () => {
    initChart();

    // Load REAL Binance historical data into the chart
    await loadRealKlines(currentSymbol, '1m', 300);

    // Init WebSocket AFTER chart has history
    initWebSocket();

    setupOrderForm();

    // Watchlist clicks
    document.querySelectorAll('.watchlist-item').forEach(item => {
        item.addEventListener('click', () => switchSymbol(item.dataset.symbol));
    });

    // Symbol dropdown
    document.getElementById('symbol-select').addEventListener('change', (e) => {
        switchSymbol(e.target.value);
    });

    // Tab clicks
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Seed market
    document.getElementById('seed-btn').addEventListener('click', seedMarket);

    // Refresh chart
    document.getElementById('refresh-chart-btn').addEventListener('click', () => {
        loadRealKlines(currentSymbol, '1m', 300);
        showToast('Chart refreshed with latest Binance data', 'info');
    });

    // Periodic book refresh as fallback (every 3 seconds)
    bookRefreshInterval = setInterval(fetchAndRenderBook, 3000);

    // Initial data
    fetchAndRenderBook();
    fetchAndRenderTrades();
    fetchAndRenderOrders();

    // Load real prices for all watchlist symbols
    for (const sym of ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']) {
        fetch(`/market/price/${sym}`)
            .then(r => r.json())
            .then(d => updateWatchlistPrice(d.symbol, d.price))
            .catch(() => {});
    }
});
