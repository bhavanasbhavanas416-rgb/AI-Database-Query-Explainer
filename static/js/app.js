/* ==========================================================================
   AI DATABASE QUERY EXPLAINER - FRONTEND SPA ENGINE
   ========================================================================== */

const browserFetch = window.fetch.bind(window);
window.fetch = (input, options = {}) => {
    const method = (options.method || 'GET').toUpperCase();
    if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
        const headers = new Headers(options.headers || {});
        const csrfCookie = document.cookie.split('; ').find(cookie => cookie.startsWith('csrftoken='));
        if (csrfCookie) headers.set('X-CSRFToken', decodeURIComponent(csrfCookie.split('=').slice(1).join('=')));
        options = { ...options, headers };
    }
    return browserFetch(input, options);
};

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    setupAuthentication();
});

// State Management
let state = {
    activeTab: 'nav-dashboard',
    activeConnection: null,
    currentQuery: '',
    historyId: null,
    chartInstance: null
};

function setupAuthentication() {
    const form = document.getElementById('auth-form');
    const modeToggle = document.getElementById('auth-mode-toggle');
    let mode = 'login';

    modeToggle.addEventListener('click', () => {
        mode = mode === 'login' ? 'register' : 'login';
        const registering = mode === 'register';
        document.getElementById('auth-title').innerText = registering ? 'Create your account' : 'Welcome back';
        document.getElementById('auth-description').innerText = registering
            ? 'Create an account to open your database workspace.'
            : 'Sign in to continue to your database workspace.';
        document.getElementById('auth-email-field').hidden = !registering;
        document.getElementById('auth-email').disabled = !registering;
        document.getElementById('auth-email').required = registering;
        document.getElementById('auth-password').autocomplete = registering ? 'new-password' : 'current-password';
        document.getElementById('auth-submit').innerText = registering ? 'Create account' : 'Sign in';
        modeToggle.innerText = registering ? 'Already registered? Sign in' : 'New here? Create an account';
        document.getElementById('auth-error').hidden = true;
    });

    form.addEventListener('submit', async event => {
        event.preventDefault();
        const error = document.getElementById('auth-error');
        const button = document.getElementById('auth-submit');
        error.hidden = true;
        button.disabled = true;
        button.innerText = mode === 'register' ? 'Creating account...' : 'Signing in...';
        const payload = {
            username: document.getElementById('auth-username').value.trim(),
            password: document.getElementById('auth-password').value,
        };
        if (mode === 'register') payload.email = document.getElementById('auth-email').value.trim();

        try {
            const response = await fetch(`/api/v1/auth/${mode === 'register' ? 'register' : 'login'}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Authentication failed.');
            const profileResponse = await fetch('/api/v1/auth/profile/');
            if (!profileResponse.ok) throw new Error('Your session could not be started. Please try again.');
            startWorkspace(await profileResponse.json());
        } catch (requestError) {
            error.innerText = requestError.message;
            error.hidden = false;
        } finally {
            button.disabled = false;
            button.innerText = mode === 'register' ? 'Create account' : 'Sign in';
        }
    });

    document.getElementById('logout-btn').addEventListener('click', async () => {
        await fetch('/api/v1/auth/logout/', { method: 'POST' });
        window.location.reload();
    });

    fetch('/api/v1/auth/profile/')
        .then(async response => response.ok ? response.json() : null)
        .then(profile => profile ? startWorkspace(profile) : showAuthentication())
        .catch(showAuthentication);
}

function showAuthentication() {
    document.getElementById('auth-screen').hidden = false;
}

function startWorkspace(profile) {
    document.getElementById('auth-screen').hidden = true;
    document.getElementById('sidebar-user-name').innerText = profile.username;
    document.getElementById('sidebar-user-role').innerText = profile.role === 'admin' ? 'Administrator' : 'Workspace member';
    const adminNav = document.querySelector('.nav-link-item[data-pane="nav-admin"]');
    if (adminNav) adminNav.hidden = !profile.is_admin;
    const avatar = document.querySelector('.sidebar-footer .avatar');
    if (avatar) avatar.innerText = profile.username.slice(0, 2).toUpperCase();
    initNavigation();
    loadActiveConnectionInfo();
    loadDashboardMetrics();
    loadSchemaExplorer();
    loadHistoryList();
    setupEventListeners();
}

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);

    // Sync user profile preference
    fetch('/api/v1/auth/profile/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme: newTheme })
    }).catch(err => console.log('Theme sync notice:', err));
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.className = theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
}

// Navigation Engine
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-link-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPaneId = item.getAttribute('data-pane');
            switchTab(targetPaneId, item);
        });
    });
}

function switchTab(paneId, activeNavItem) {
    state.activeTab = paneId;

    // Update nav links
    document.querySelectorAll('.nav-link-item').forEach(el => el.classList.remove('active'));
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    } else {
        const match = document.querySelector(`.nav-link-item[data-pane="${paneId}"]`);
        if (match) match.classList.add('active');
    }

    // Update tab panes
    document.querySelectorAll('.tab-pane-view').forEach(pane => pane.classList.remove('active-pane'));
    const targetPane = document.getElementById(paneId);
    if (targetPane) {
        targetPane.classList.add('active-pane');
    }

    // Trigger tab specific loads
    if (paneId === 'nav-connections') loadConnectionsList();
    if (paneId === 'nav-schema') loadSchemaExplorer();
    if (paneId === 'nav-history') loadHistoryList();
    if (paneId === 'nav-admin') loadAdminMetrics();
    if (paneId === 'nav-analytics') renderAnalyticsChart();
}

function setupEventListeners() {
    // Theme toggle button
    document.getElementById('theme-toggle-btn')?.addEventListener('click', toggleTheme);

    // NL to SQL Prompt Form
    document.getElementById('nl-sql-form')?.addEventListener('submit', handleNLToSQLSubmit);

    // Paste SQL Explainer Form
    document.getElementById('explain-sql-form')?.addEventListener('submit', handleExplainSQLSubmit);

    // Paste SQL Optimizer Form
    document.getElementById('optimize-sql-form')?.addEventListener('submit', handleOptimizeSQLSubmit);

    // SQL Runner Console Form
    document.getElementById('sql-runner-form')?.addEventListener('submit', handleExecuteSQLSubmit);

    // Export buttons
    document.getElementById('export-csv-btn')?.addEventListener('click', () => exportResults('csv'));
    document.getElementById('export-excel-btn')?.addEventListener('click', () => exportResults('excel'));

    // Schema Search input
    document.getElementById('schema-search-input')?.addEventListener('input', (e) => {
        loadSchemaExplorer(e.target.value);
    });

    // Profile & API Key Form
    document.getElementById('profile-settings-form')?.addEventListener('submit', handleSaveProfileSettings);

    // SQLite database upload form
    document.getElementById('sqlite-upload-form')?.addEventListener('submit', handleSQLiteUpload);
}

// API Calls & Actions

// 1. Connection & Active Info
function loadActiveConnectionInfo() {
    fetch('/api/v1/connections/')
        .then(res => res.json())
        .then(data => {
            const active = data.connections?.find(c => c.is_active);
            if (active) {
                state.activeConnection = active;
                const badge = document.getElementById('active-db-badge-text');
                if (badge) badge.innerText = `${active.name} (${active.engine.toUpperCase()})`;
            }
        }).catch(err => console.error(err));
}

function loadConnectionsList() {
    fetch('/api/v1/connections/')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('connections-list-container');
            if (!container) return;

            if (!data.connections || data.connections.length === 0) {
                container.innerHTML = '<div class="alert alert-info">No database connections found.</div>';
                return;
            }

            container.innerHTML = data.connections.map(c => `
                <div class="card-glass p-3 mb-3 d-flex align-items-center justify-content-between">
                    <div>
                        <h5 class="mb-1 text-white">${c.name} ${c.is_default_sample ? '<span class="badge bg-primary ms-2">100k+ Sample DB</span>' : ''}</h5>
                        <p class="mb-0 text-muted small"><i class="fa-solid fa-database me-1"></i> ${c.engine.toUpperCase()} | DB: ${c.db_name}</p>
                    </div>
                    <div>
                        ${c.is_active ? 
                            '<span class="badge bg-success px-3 py-2"><i class="fa-solid fa-circle-check me-1"></i> Active</span>' :
                            `<button class="btn btn-sm btn-outline-info" onclick="setActiveConnection(${c.id})">Set Active</button>`
                        }
                    </div>
                </div>
            `).join('');
        });
}

function setActiveConnection(id) {
    fetch(`/api/v1/connections/${id}/set-active/`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            showToast(data.message || 'Active connection updated!');
            loadActiveConnectionInfo();
            loadConnectionsList();
            loadSchemaExplorer();
        });
}

function handleSQLiteUpload(e) {
    e.preventDefault();
    const form = e.currentTarget;
    const fileInput = document.getElementById('sqlite-file-input');
    const file = fileInput.files[0];
    if (!file) return;

    const button = document.getElementById('sqlite-upload-btn');
    const formData = new FormData();
    formData.append('name', document.getElementById('sqlite-connection-name').value.trim());
    formData.append('engine', 'sqlite');
    formData.append('db_name', file.name);
    formData.append('sqlite_file', file);
    button.disabled = true;
    button.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Uploading...';

    fetch('/api/v1/connections/', { method: 'POST', body: formData })
        .then(async response => {
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Database upload failed.');
            return data;
        })
        .then(data => {
            showToast(data.message || 'Database connected successfully.', 'success');
            form.reset();
            loadActiveConnectionInfo();
            loadConnectionsList();
            loadSchemaExplorer();
        })
        .catch(error => showToast(error.message, 'danger'))
        .finally(() => {
            button.disabled = false;
            button.innerHTML = '<i class="fa-solid fa-upload me-2"></i>Upload & Connect';
        });
}

// 2. Schema Explorer
function loadSchemaExplorer(searchQuery = '') {
    const container = document.getElementById('schema-tables-container');
    if (!container) return;

    fetch(`/api/v1/schema/?q=${encodeURIComponent(searchQuery)}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }

            // Update stats
            document.getElementById('schema-total-tables').innerText = data.total_tables || 0;
            document.getElementById('schema-total-records').innerText = (data.total_records || 0).toLocaleString();

            // Render Table Cards
            container.innerHTML = data.tables.map(tbl => `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card-glass h-100 p-3">
                        <div class="d-flex align-items-center justify-content-between mb-2">
                            <h5 class="text-info mb-0"><i class="fa-solid fa-table me-2"></i>${tbl.table_name}</h5>
                            <span class="badge bg-secondary">${tbl.row_count.toLocaleString()} rows</span>
                        </div>
                        <hr class="border-secondary my-2">
                        <ul class="list-unstyled mb-0 small" style="max-height: 180px; overflow-y: auto;">
                            ${tbl.columns.map(c => `
                                <li class="py-1 d-flex justify-content-between text-muted border-bottom border-dark">
                                    <span>${c.primary_key ? '<i class="fa-solid fa-key text-warning me-1"></i>' : ''}${c.name}</span>
                                    <span class="text-info">${c.type}</span>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `).join('');

            // Render Relationships ER list
            const relContainer = document.getElementById('er-relationships-list');
            if (relContainer && data.relationships) {
                relContainer.innerHTML = data.relationships.map(r => `
                    <span class="badge bg-dark border border-secondary p-2 me-2 mb-2">
                        <i class="fa-solid fa-link text-cyan me-1"></i> ${r.from_table}.${r.from_column} &rarr; ${r.to_table}.${r.to_column}
                    </span>
                `).join('') || '<span class="text-muted">No explicit Foreign Keys defined.</span>';
            }
        });
}

// 3. NL to SQL Generator
function handleNLToSQLSubmit(e) {
    e.preventDefault();
    const promptInput = document.getElementById('nl-prompt-input');
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const btn = document.getElementById('generate-sql-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> AI Thinking...';

    fetch('/api/v1/query/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
    })
    .then(res => res.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles me-2"></i> Generate SQL Query';

        if (data.error) {
            showToast(data.error, 'danger');
            return;
        }

        state.currentQuery = data.generated_sql;
        state.historyId = data.history_id;

        // Populate generated SQL
        document.getElementById('generated-sql-display').innerText = data.generated_sql;
        document.getElementById('nl-sql-result-card').style.display = 'block';

        // Render Explanation Cards
        renderExplanationDetails('nl-explanation-container', data.explanation);

        // Render Optimization Score
        renderOptimizationDetails('nl-optimization-container', data.optimization);

        showToast('SQL Query successfully generated!', 'success');
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles me-2"></i> Generate SQL Query';
        showToast('Generation failed. Please try again.', 'danger');
    });
}

function runCurrentGeneratedSQL() {
    if (!state.currentQuery) return;
    document.getElementById('sql-runner-textarea').value = state.currentQuery;
    switchTab('nav-execution');
    document.getElementById('sql-runner-form').dispatchEvent(new Event('submit'));
}

// 4. SQL Query Explainer
function handleExplainSQLSubmit(e) {
    e.preventDefault();
    const sql = document.getElementById('explain-sql-input').value.trim();
    if (!sql) return;

    fetch('/api/v1/query/explain/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'danger');
            return;
        }
        document.getElementById('explain-result-card').style.display = 'block';
        renderExplanationDetails('direct-explain-container', data);
    });
}

function renderExplanationDetails(containerId, exp) {
    const el = document.getElementById(containerId);
    if (!el) return;

    el.innerHTML = `
        <div class="alert alert-dark border-info mb-3">
            <h6 class="text-cyan fw-bold mb-1"><i class="fa-solid fa-bullseye me-2"></i>Purpose Summary</h6>
            <p class="mb-0 small text-white">${exp.purpose}</p>
        </div>
        
        <div class="row mb-3">
            <div class="col-md-6 mb-2">
                <div class="p-2 bg-dark rounded border border-secondary">
                    <span class="text-muted small fw-bold">TABLES USED:</span>
                    <div class="mt-1">${exp.tables_used.map(t => `<span class="badge bg-primary me-1">${t}</span>`).join('') || 'None'}</div>
                </div>
            </div>
            <div class="col-md-6 mb-2">
                <div class="p-2 bg-dark rounded border border-secondary">
                    <span class="text-muted small fw-bold">SQL OPERATIONS:</span>
                    <div class="mt-1">${exp.sql_operations.map(o => `<span class="badge bg-info text-dark me-1">${o}</span>`).join('') || 'None'}</div>
                </div>
            </div>
        </div>

        <h6 class="text-cyan fw-bold mb-2"><i class="fa-solid fa-list-check me-2"></i>Line-by-Line Breakdown</h6>
        <div class="list-group mb-3">
            ${exp.line_by_line.map(l => `
                <div class="list-group-item bg-dark text-white border-secondary">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge bg-cyan text-dark">Line ${l.line_number}</span>
                        <code class="text-warning">${l.code}</code>
                    </div>
                    <p class="mb-0 small text-muted">${l.explanation}</p>
                </div>
            `).join('')}
        </div>
    `;
}

// 5. Query Optimization
function handleOptimizeSQLSubmit(e) {
    e.preventDefault();
    const sql = document.getElementById('optimize-sql-input').value.trim();
    if (!sql) return;

    fetch('/api/v1/query/optimize/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'danger');
            return;
        }
        document.getElementById('optimize-result-card').style.display = 'block';
        renderOptimizationDetails('direct-optimize-container', data);
    });
}

function renderOptimizationDetails(containerId, opt) {
    const el = document.getElementById(containerId);
    if (!el) return;

    const scoreColor = opt.performance_score >= 80 ? 'var(--accent-green)' : (opt.performance_score >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)');

    el.innerHTML = `
        <div class="row align-items-center mb-4">
            <div class="col-md-4 text-center">
                <div class="score-circle" style="border-color: ${scoreColor}; color: ${scoreColor};">
                    ${opt.performance_score}
                </div>
                <div class="score-label">Performance Score</div>
            </div>
            <div class="col-md-8">
                <span class="badge bg-secondary mb-2">Complexity: ${opt.query_complexity}</span>
                <h6 class="text-white fw-bold mb-2"><i class="fa-solid fa-lightbulb text-warning me-2"></i>Optimization Suggestions</h6>
                <ul class="small text-muted ps-3 mb-0">
                    ${opt.optimization_suggestions.map(s => `<li class="mb-1">${s}</li>`).join('')}
                </ul>
            </div>
        </div>

        ${opt.index_recommendations.length > 0 ? `
            <div class="p-3 bg-dark rounded border border-warning mb-3">
                <h6 class="text-warning small fw-bold mb-2"><i class="fa-solid fa-bolt me-2"></i>Recommended Indexes</h6>
                <pre class="mb-0 text-success small"><code>${opt.index_recommendations.join('\n')}</code></pre>
            </div>
        ` : ''}
    `;
}

// 6. Query Execution Engine & Export
function handleExecuteSQLSubmit(e) {
    e.preventDefault();
    const sql = document.getElementById('sql-runner-textarea').value.trim();
    if (!sql) return;

    state.currentQuery = sql;
    const btn = document.getElementById('execute-sql-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i> Executing...';

    fetch('/api/v1/query/execute/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql, history_id: state.historyId })
    })
    .then(res => res.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-play me-2"></i> Execute Query';

        if (data.error) {
            showToast(data.error, 'danger');
            return;
        }

        // Display summary metrics
        document.getElementById('exec-row-count').innerText = data.total_rows.toLocaleString();
        document.getElementById('exec-time-ms').innerText = `${data.execution_time_ms} ms`;
        document.getElementById('execution-result-card').style.display = 'block';

        // Render Data Table Header & Body
        const thead = document.getElementById('data-table-head');
        const tbody = document.getElementById('data-table-body');

        thead.innerHTML = `<tr>${data.columns.map(c => `<th>${c}</th>`).join('')}</tr>`;
        tbody.innerHTML = data.rows.map(r => `<tr>${r.map(v => `<td>${v !== null ? v : '<i class="text-muted">NULL</i>'}</td>`).join('')}</tr>`).join('');

        showToast(`Query executed in ${data.execution_time_ms} ms with ${data.total_rows} rows!`, 'success');
    })
    .catch(err => {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-play me-2"></i> Execute Query';
        showToast('Execution error occurred.', 'danger');
    });
}

function exportResults(format) {
    if (!state.currentQuery) {
        showToast('Please execute a SQL query first.', 'warning');
        return;
    }

    const endpoint = format === 'csv' ? '/api/v1/export/csv/' : '/api/v1/export/excel/';
    fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: state.currentQuery })
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `query_results.${format === 'csv' ? 'csv' : 'xlsx'}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast(`Downloaded results as ${format.toUpperCase()}`, 'success');
    });
}

// 7. Database Analytics Dashboard
function renderAnalyticsChart() {
    fetch('/api/v1/analytics/chart/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: state.currentQuery, chart_type: 'bar' })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return;

        document.getElementById('analytics-insights-text').innerText = data.insights;

        const ctx = document.getElementById('analyticsCanvas');
        if (!ctx) return;

        if (state.chartInstance) {
            state.chartInstance.destroy();
        }

        state.chartInstance = new Chart(ctx, {
            type: data.chart_type,
            data: {
                labels: data.labels,
                datasets: [{
                    label: data.title,
                    data: data.series,
                    backgroundColor: [
                        'rgba(6, 182, 212, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(139, 92, 246, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(245, 158, 11, 0.7)',
                        'rgba(244, 63, 94, 0.7)'
                    ],
                    borderColor: '#06b6d4',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: '#f9fafb' } }
                },
                scales: {
                    x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    });
}

// 8. History & Admin Metrics
function loadHistoryList() {
    fetch('/api/v1/query/history/')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('history-table-body');
            if (!container) return;

            if (!data.history || data.history.length === 0) {
                container.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No query history records.</td></tr>';
                return;
            }

            container.innerHTML = data.history.map(h => `
                <tr>
                    <td>${h.created_at}</td>
                    <td class="text-info">${h.user_question || 'SQL Console'}</td>
                    <td><code>${h.generated_sql || h.executed_sql}</code></td>
                    <td>${h.execution_time_ms} ms</td>
                    <td><span class="badge bg-${h.status === 'success' ? 'success' : 'secondary'}">${h.status}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-info" onclick="rerunHistorySQL('${encodeURIComponent(h.generated_sql || h.executed_sql)}')">
                            <i class="fa-solid fa-rotate-right me-1"></i> Run
                        </button>
                    </td>
                </tr>
            `).join('');
        });
}

function rerunHistorySQL(encodedSQL) {
    const sql = decodeURIComponent(encodedSQL);
    document.getElementById('sql-runner-textarea').value = sql;
    switchTab('nav-execution');
    document.getElementById('sql-runner-form').dispatchEvent(new Event('submit'));
}

function loadDashboardMetrics() {
    fetch('/api/v1/admin/metrics/')
        .then(res => res.json())
        .then(data => {
            if (document.getElementById('dash-total-users')) document.getElementById('dash-total-users').innerText = data.total_users;
            if (document.getElementById('dash-total-connections')) document.getElementById('dash-total-connections').innerText = data.total_connections;
            if (document.getElementById('dash-total-queries')) document.getElementById('dash-total-queries').innerText = data.total_queries;
            if (document.getElementById('dash-avg-speed')) document.getElementById('dash-avg-speed').innerText = `${data.avg_execution_speed_ms} ms`;
        });
}

function loadAdminMetrics() {
    loadDashboardMetrics();
    fetch('/api/v1/admin/metrics/')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('admin-recent-logs');
            if (container && data.recent_logs) {
                container.innerHTML = data.recent_logs.map(l => `
                    <tr>
                        <td>${l.created_at}</td>
                        <td><span class="badge bg-primary">${l.user}</span></td>
                        <td>${l.question}</td>
                        <td><code>${l.sql}</code></td>
                        <td>${l.time_ms} ms</td>
                    </tr>
                `).join('');
            }
        });
}

// Settings & Profile
function handleSaveProfileSettings(e) {
    e.preventDefault();
    const groqKey = document.getElementById('groq-key-input').value.trim();
    const email = document.getElementById('profile-email-input').value.trim();

    fetch('/api/v1/auth/profile/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ groq_api_key: groqKey, email: email })
    })
    .then(res => res.json())
    .then(data => {
        showToast('Settings saved successfully!', 'success');
    });
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed bottom-0 end-0 m-4 shadow-lg z- index-1000`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `<i class="fa-solid fa-circle-info me-2"></i>${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
