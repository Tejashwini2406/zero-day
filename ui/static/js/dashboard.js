// Dashboard JavaScript for Zero-Day Detection UI

let refreshInterval;

document.addEventListener('DOMContentLoaded', function() {
    // Initial load
    loadSystemStatus();
    loadAlerts();
    loadMetrics();
    loadGraphData();

    // Set up auto-refresh every 30 seconds
    refreshInterval = setInterval(function() {
        loadSystemStatus();
        loadMetrics();
        loadGraphData();
        updateLastUpdated();
    }, 30000);

    updateLastUpdated();
});

function updateLastUpdated() {
    const now = new Date();
    document.getElementById('last-updated').textContent =
        'Last updated: ' + now.toLocaleTimeString();
}

function loadSystemStatus() {
    fetch('/api/system-status')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('system-status');
            let html = '';

            for (const [namespace, status] of Object.entries(data)) {
                if (status.error) {
                    html += `
                        <div class="mb-3">
                            <strong>${namespace}:</strong>
                            <span class="status-danger">Error</span>
                        </div>`;
                } else {
                    const healthClass = status.failed > 0 ? 'status-danger' :
                                      status.running < status.total ? 'status-warning' : 'status-healthy';
                    html += `
                        <div class="mb-3">
                            <strong>${namespace}:</strong>
                            <span class="${healthClass}">${status.running}/${status.total} running</span>
                        </div>`;
                }
            }

            container.innerHTML = html;
        })
        .catch(error => {
            document.getElementById('system-status').innerHTML =
                '<div class="text-danger">Error loading system status</div>';
        });
}

function loadAlerts() {
    fetch('/api/alerts')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('alerts-list');
            if (data.error) {
                container.innerHTML = '<div class="text-danger">Error loading alerts</div>';
                return;
            }

            if (data.length === 0) {
                container.innerHTML = '<div class="text-muted">No active alerts</div>';
                return;
            }

            let html = '';
            data.forEach(alert => {
                const spec = alert.spec || {};
                html += `
                    <div class="alert-item">
                        <strong>${spec.pod_name || 'Unknown'}</strong> in ${spec.namespace || 'unknown'}
                        <br><small class="text-muted">${alert.metadata?.creationTimestamp || 'Unknown time'}</small>
                        <br><small>Action: ${spec.action || 'Unknown'}</small>
                    </div>`;
            });

            container.innerHTML = html;
        })
        .catch(error => {
            document.getElementById('alerts-list').innerHTML =
                '<div class="text-danger">Error loading alerts</div>';
        });
}

function refreshAlerts() {
    loadAlerts();
}

function loadMetrics() {
    fetch('/api/metrics')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('metrics');
            if (data.error) {
                container.innerHTML = '<div class="text-danger">Error loading metrics</div>';
                return;
            }

            const html = `
                <div class="mb-3">
                    <div class="metric-value">${(data.anomaly_score_avg * 100).toFixed(1)}%</div>
                    <div class="metric-label">Avg Anomaly Score</div>
                </div>
                <div class="mb-3">
                    <div class="metric-value">${data.alerts_today}</div>
                    <div class="metric-label">Alerts Today</div>
                </div>
                <div class="mb-3">
                    <div class="metric-value">${data.models_loaded?.length || 0}</div>
                    <div class="metric-label">Models Loaded</div>
                </div>
                <div class="mb-3">
                    <div class="metric-label">Last Training</div>
                    <div class="small">${new Date(data.last_training).toLocaleString()}</div>
                </div>`;

            container.innerHTML = html;
        })
        .catch(error => {
            document.getElementById('metrics').innerHTML =
                '<div class="text-danger">Error loading metrics</div>';
        });
}

function loadGraphData() {
    fetch('/api/graphs')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('graph-data');
            if (data.error) {
                container.innerHTML = '<div class="text-danger">Error loading graph data</div>';
                return;
            }

            const html = `
                <div class="row">
                    <div class="col-6">
                        <div class="metric-value">${data.nodes}</div>
                        <div class="metric-label">Nodes</div>
                    </div>
                    <div class="col-6">
                        <div class="metric-value">${data.edges}</div>
                        <div class="metric-label">Edges</div>
                    </div>
                </div>
                <div class="mt-3">
                    <div class="metric-value">${data.windows}</div>
                    <div class="metric-label">Time Windows</div>
                </div>
                <div class="mt-3">
                    <div class="metric-label">Last Updated</div>
                    <div class="small">${new Date(data.last_updated).toLocaleString()}</div>
                </div>`;

            container.innerHTML = html;
        })
        .catch(error => {
            document.getElementById('graph-data').innerHTML =
                '<div class="text-danger">Error loading graph data</div>';
        });
}

function loadLogs() {
    const component = document.getElementById('log-component').value;
    const display = document.getElementById('logs-display');

    display.textContent = 'Loading logs...';

    fetch(`/api/logs/${component}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                display.textContent = `Error: ${data.error}`;
            } else {
                display.textContent = data.logs || 'No logs available';
            }
        })
        .catch(error => {
            display.textContent = 'Error loading logs';
        });
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});
