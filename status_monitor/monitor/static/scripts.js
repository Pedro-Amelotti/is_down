const REFRESH_INTERVAL = 15 * 60 * 1000; // 15 minutos
const STORAGE_KEY = 'monitorState';
const STATE_VERSION = 2;

let monitorState = null;
let refreshTimeoutId = null;
let downtimeChart = null;
let refreshTickerId = null;

function getDefaultState() {
    return {
        version: STATE_VERSION,
        servers: {},
        statuses: {},
        counts: {
            active: 0,
            forbidden: 0,
            down: 0,
        },
        chartData: [],
        detailAnchor: '#main-container',
        nextRefreshAt: null,
        lastUpdated: null,
    };
}

function loadStateFromStorage() {
    if (typeof sessionStorage === 'undefined') {
        return null;
    }
    try {
        const stored = sessionStorage.getItem(STORAGE_KEY);
        if (!stored) {
            return null;
        }

        const parsed = JSON.parse(stored);
        if (parsed.version !== STATE_VERSION) {
            return null;
        }
        return {
            ...getDefaultState(),
            ...parsed,
            servers: parsed.servers || {},
            statuses: parsed.statuses || {},
            counts: {
                ...getDefaultState().counts,
                ...(parsed.counts || {}),
            },
            chartData: parsed.chartData || [],
        };
    } catch (error) {
        console.warn('Não foi possível carregar o estado salvo:', error);
        return null;
    }
}

function persistState() {
    if (!monitorState) {
        return;
    }
    if (typeof sessionStorage === 'undefined') {
        return;
    }
    monitorState.version = STATE_VERSION;
    try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(monitorState));
    } catch (error) {
        console.warn('Não foi possível salvar o estado:', error);
    }
}

function makeSafeId(value) {
    return value.toLowerCase().replace(/[^a-z0-9]+/gi, '-');
}

function escapeSelector(value) {
    if (window.CSS && typeof window.CSS.escape === 'function') {
        return window.CSS.escape(value);
    }
    return value.replace(/[^a-zA-Z0-9_-]/g, '\\$&');
}

function getStatusClass(status) {
    if (!status) {
        return 'other';
    }
    const normalized = status.toLowerCase().replace(/\s+/g, '-');
    if (['up', 'down', 'forbidden', 'loading'].includes(normalized)) {
        return normalized;
    }
    return normalized || 'other';
}

function formatTimestamp(date = new Date()) {
    return date.toISOString().replace('T', ' ').slice(0, 19);
}

function applyStatusToCard(card, data) {
    const statusText = data.status || 'DESCONHECIDO';
    const statusClass = getStatusClass(statusText);

    card.className = `system-card ${statusClass}`;

    const statusElement = card.querySelector('.system-status');
    if (statusElement) {
        statusElement.textContent = statusText;
    }

    const timestampElement = card.querySelector('.system-timestamp');
    if (timestampElement) {
        timestampElement.textContent = data.checked_at
            ? `Última verificação: ${data.checked_at}`
            : '';
    }

    const loadingBar = card.querySelector('.loading-bar');
    if (loadingBar) {
        loadingBar.remove();
    }
}

function createSystemCard(system, statusData = null) {
    const statusText = statusData?.status || 'CARREGANDO';
    const statusClass = statusData ? getStatusClass(statusText) : 'loading';

    const card = document.createElement('div');
    card.className = `system-card ${statusClass}`;
    card.dataset.systemName = system.name;

    const timestampText = statusData?.checked_at
        ? `Última verificação: ${statusData.checked_at}`
        : '';

    card.innerHTML = `
        <div class="system-name">${system.name}</div>
        <div class="system-status">${statusText}</div>
        <a href="${system.url}" target="_blank" class="system-url" rel="noopener">Link</a>
        <div class="system-timestamp">${timestampText}</div>
        ${statusData ? '' : '<div class="loading-bar"></div>'}
    `;

    if (statusData) {
        applyStatusToCard(card, statusData);
    }

    return card;
}

function ingestServerStatuses(servers) {
    Object.values(servers).forEach((systems) => {
        systems.forEach((system) => {
            if (system.status) {
                monitorState.statuses[system.name] = {
                    status: system.status,
                    checked_at: system.checked_at,
                };
            }
        });
    });
}

function renderServers(servers) {
    const container = document.getElementById('main-container');
    if (!container) {
        return;
    }

    container.innerHTML = '';

    Object.entries(servers).forEach(([serverName, systems]) => {
        const panel = document.createElement('div');
        panel.className = 'systems-panel';

        const title = document.createElement('h2');
        title.className = 'server-title';
        title.textContent = serverName;
        panel.appendChild(title);

        const safeId = makeSafeId(serverName);

        const filterContainer = document.createElement('div');
        filterContainer.className = 'filter-container';
        filterContainer.innerHTML = `
            <input type="text" id="searchInput-${safeId}" onkeyup="filterSystems('${safeId}')" placeholder="Buscar por nome...">
            <button onclick="filterByStatus('down', '${safeId}')">DOWN</button>
            <button onclick="filterByStatus('forbidden', '${safeId}')">FORBIDDEN</button>
            <button onclick="filterByStatus('', '${safeId}')">Limpar</button>
        `;
        panel.appendChild(filterContainer);

        const grid = document.createElement('div');
        grid.className = 'systems-grid';
        grid.id = `systems-grid-${safeId}`;
        panel.appendChild(grid);

        systems.forEach((system) => {
            const cachedStatus = monitorState.statuses[system.name];
            const card = createSystemCard(system, cachedStatus);
            grid.appendChild(card);
        });

        container.appendChild(panel);
    });
}

function updateDashboardCards(counts) {
    const activeElement = document.getElementById('active-count');
    const forbiddenElement = document.getElementById('forbidden-count');
    const downElement = document.getElementById('down-count');

    if (activeElement) {
        activeElement.textContent = counts?.active ?? 0;
    }
    if (forbiddenElement) {
        forbiddenElement.textContent = counts?.forbidden ?? 0;
    }
    if (downElement) {
        downElement.textContent = counts?.down ?? 0;
    }
}

function clearRefreshTicker() {
    if (refreshTickerId) {
        clearInterval(refreshTickerId);
        refreshTickerId = null;
    }
}

function formatCountdown(ms) {
    const seconds = Math.max(0, Math.floor(ms / 1000));
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds
        .toString()
        .padStart(2, '0')}`;
}

function updateMetaInfo() {
    const lastUpdatedElement = document.getElementById('last-updated');
    const nextRefreshElement = document.getElementById('next-refresh');

    if (lastUpdatedElement) {
        if (monitorState?.lastUpdated) {
            const date = new Date(monitorState.lastUpdated);
            lastUpdatedElement.textContent = date.toLocaleString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
            });
        } else {
            lastUpdatedElement.textContent = '--';
        }
    }

    if (nextRefreshElement) {
        if (monitorState?.nextRefreshAt) {
            const remaining = monitorState.nextRefreshAt - Date.now();
            if (remaining <= 0) {
                nextRefreshElement.textContent = 'Atualizando...';
            } else {
                const nextTime = new Date(monitorState.nextRefreshAt).toLocaleTimeString(
                    'pt-BR',
                    {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                    }
                );
                nextRefreshElement.textContent = `${formatCountdown(remaining)} (às ${nextTime})`;
            }
        } else {
            nextRefreshElement.textContent = '--';
        }
    }
}

function startRefreshTicker() {
    clearRefreshTicker();
    updateMetaInfo();
    if (!monitorState?.nextRefreshAt) {
        return;
    }
    refreshTickerId = setInterval(() => {
        if (!monitorState?.nextRefreshAt) {
            clearRefreshTicker();
            return;
        }
        updateMetaInfo();
    }, 1000);
}

function renderDowntimeChart(data) {
    const canvas = document.getElementById('downtime-chart');
    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    const labels = data.map((item) => item.name);
    const durations = data.map((item) => item.total_minutes);

    if (downtimeChart) {
        downtimeChart.data.labels = labels;
        downtimeChart.data.datasets[0].data = durations;
        downtimeChart.update();
        return;
    }

    downtimeChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    data: durations,
                    backgroundColor: '#dc3545',
                    borderRadius: 6,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.parsed.y} min`,
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        autoSkip: false,
                        maxRotation: 45,
                        minRotation: 0,
                    },
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Minutos',
                    },
                },
            },
        },
    });
}

function updateDetailLink(anchor) {
    const detailLink = document.getElementById('detail-link');
    if (!detailLink) {
        return;
    }
    detailLink.href = anchor || '#main-container';
}

function scheduleNextLoad(delay) {
    if (refreshTimeoutId) {
        clearTimeout(refreshTimeoutId);
    }
    refreshTimeoutId = setTimeout(() => {
        loadSystems();
    }, delay);
    startRefreshTicker();
}

function getCardElement(systemName) {
    const selectorName = escapeSelector(systemName);
    return document.querySelector(`.system-card[data-system-name="${selectorName}"]`);
}

async function updateSystemStatus(card, system) {
    try {
        const response = await fetch(`/system_status/?url=${encodeURIComponent(system.url)}&name=${encodeURIComponent(system.name)}`);
        if (!response.ok) {
            throw new Error('Falha ao consultar status do sistema');
        }
        const data = await response.json();
        applyStatusToCard(card, data);
        monitorState.statuses[system.name] = data;
        persistState();
        return data;
    } catch (error) {
        console.error(`Erro ao atualizar o status de ${system.name}:`, error);
        const fallback = {
            status: 'ERRO',
            checked_at: formatTimestamp(),
        };
        applyStatusToCard(card, fallback);
        monitorState.statuses[system.name] = fallback;
        persistState();
        return fallback;
    }
}

async function loadDashboardSummary() {
    try {
        const response = await fetch('/dashboard_summary/');
        if (!response.ok) {
            throw new Error('Falha ao carregar o resumo');
        }
        const data = await response.json();
        monitorState.counts = data.counts || monitorState.counts;
        monitorState.chartData = data.downtime_chart || [];
        monitorState.detailAnchor = data.detail_anchor || '#main-container';
        persistState();
        updateDashboardCards(monitorState.counts);
        renderDowntimeChart(monitorState.chartData);
        updateDetailLink(monitorState.detailAnchor);
    } catch (error) {
        console.error('Erro ao carregar resumo do dashboard:', error);
    }
}

async function loadSystems() {
    const container = document.getElementById('main-container');
    if (!container) {
        return;
    }

    try {
        const response = await fetch('/systems_list/');
        if (!response.ok) {
            throw new Error('Falha ao carregar a lista de sistemas');
        }
        const servers = await response.json();
        monitorState.servers = servers;
        ingestServerStatuses(servers);
        persistState();

        renderServers(servers);

        const statusPromises = [];
        Object.values(servers).forEach((systems) => {
            systems.forEach((system) => {
                const card = getCardElement(system.name);
                if (card) {
                    statusPromises.push(updateSystemStatus(card, system));
                }
            });
        });

        await Promise.all(statusPromises);
        await loadDashboardSummary();

        monitorState.lastUpdated = new Date().toISOString();
        monitorState.nextRefreshAt = Date.now() + REFRESH_INTERVAL;
        persistState();

        scheduleNextLoad(REFRESH_INTERVAL);
        updateMetaInfo();
    } catch (error) {
        console.error('Erro ao carregar sistemas:', error);
        container.innerHTML = '<div class="system-card down">Erro ao carregar a lista de servidores</div>';
        monitorState.nextRefreshAt = null;
        persistState();
        updateMetaInfo();
        clearRefreshTicker();
    }
}

function renderFromState() {
    if (!monitorState) {
        return;
    }
    if (monitorState.servers && Object.keys(monitorState.servers).length > 0) {
        renderServers(monitorState.servers);
    }
    updateDashboardCards(monitorState.counts);
    renderDowntimeChart(monitorState.chartData);
    updateDetailLink(monitorState.detailAnchor);
    updateMetaInfo();
}

function initializeDashboard() {
    clearRefreshTicker();
    monitorState = loadStateFromStorage() || getDefaultState();
    renderFromState();

    const now = Date.now();
    if (monitorState.nextRefreshAt && monitorState.nextRefreshAt > now) {
        scheduleNextLoad(monitorState.nextRefreshAt - now);
    } else {
        loadSystems();
    }
}

function filterSystems(serverId) {
    const input = document.getElementById(`searchInput-${serverId}`);
    const filter = (input?.value || '').toUpperCase();
    const grid = document.getElementById(`systems-grid-${serverId}`);
    if (!grid) {
        return;
    }

    const cards = grid.getElementsByClassName('system-card');
    Array.from(cards).forEach((card) => {
        const nameElement = card.getElementsByClassName('system-name')[0];
        if (!nameElement) {
            card.style.display = 'none';
            return;
        }
        if (nameElement.innerHTML.toUpperCase().includes(filter)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function filterByStatus(status, serverId) {
    const grid = document.getElementById(`systems-grid-${serverId}`);
    if (!grid) {
        return;
    }
    const cards = grid.getElementsByClassName('system-card');
    Array.from(cards).forEach((card) => {
        if (!status || card.classList.contains(status)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

window.filterSystems = filterSystems;
window.filterByStatus = filterByStatus;

document.addEventListener('DOMContentLoaded', initializeDashboard);
