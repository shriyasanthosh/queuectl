// API Configuration
const API_BASE = '';

// Application State
let autoRefreshInterval = null;
let currentStateFilter = '';
let currentEditingConfigKey = null;
let searchFilter = '';

// Configuration Descriptions
const CONFIG_DESCRIPTIONS = {
    'max-retries': 'Maximum retry attempts before moving to DLQ',
    'backoff-base': 'Base for exponential backoff calculation (seconds)',
    'worker-poll-interval': 'How often workers check for new jobs (seconds)',
    'job-timeout': 'Maximum job execution time (seconds)'
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeEventListeners();
    loadAllData();
    
    // Start auto-refresh if enabled
    if (document.getElementById('autoRefresh').checked) {
        startAutoRefresh();
    }
    
    // Show dashboard by default
    showSection('dashboard');
});

// Navigation
function initializeNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const section = item.getAttribute('data-section');
            showSection(section);
        });
    });
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    const section = document.getElementById(`${sectionName}-section`);
    if (section) {
        section.classList.add('active');
    }
    
    // Update nav item
    const navItem = document.querySelector(`[data-section="${sectionName}"]`);
    if (navItem) {
        navItem.classList.add('active');
    }
    
    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'jobs': 'Job Management',
        'workers': 'Worker Management',
        'dlq': 'Dead Letter Queue',
        'config': 'Configuration'
    };
    document.getElementById('pageTitle').textContent = titles[sectionName] || 'Dashboard';
    
    // Load section-specific data
    if (sectionName === 'jobs') {
        loadJobs();
    } else if (sectionName === 'workers') {
        loadWorkersStatus();
    } else if (sectionName === 'dlq') {
        loadDLQ();
    } else if (sectionName === 'config') {
        loadConfig();
    }
}

// Event Listeners
function initializeEventListeners() {
    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadAllData();
    });
    
    // Auto-refresh toggle
    document.getElementById('autoRefresh').addEventListener('change', (e) => {
        if (e.target.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
    
    // Enqueue form
    document.getElementById('enqueueForm').addEventListener('submit', handleEnqueue);
    
    // State filter
    document.getElementById('stateFilter').addEventListener('change', (e) => {
        currentStateFilter = e.target.value;
        loadJobs();
    });
    
    // Search
    document.getElementById('jobSearch').addEventListener('input', (e) => {
        searchFilter = e.target.value.toLowerCase();
        filterJobs();
    });
    
    // Worker management
    document.getElementById('startWorkersBtn').addEventListener('click', handleStartWorkers);
    document.getElementById('stopWorkersBtn').addEventListener('click', handleStopWorkers);
    
    // Config edit form
    document.getElementById('configEditForm').addEventListener('submit', handleConfigEdit);
    
    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Close modals on outside click
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

// Auto-refresh
function startAutoRefresh() {
    stopAutoRefresh();
    autoRefreshInterval = setInterval(() => {
        loadAllData();
    }, 5000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Load All Data
function loadAllData() {
    loadStatus();
    loadWorkersStatus();
    
    // Only load if section is active
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection) {
        if (activeSection.id === 'jobs-section') {
            loadJobs();
        } else if (activeSection.id === 'dlq-section') {
            loadDLQ();
        } else if (activeSection.id === 'config-section') {
            loadConfig();
        }
    }
}

// Status
async function loadStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        
        document.getElementById('totalJobs').textContent = data.total_jobs;
        document.getElementById('pendingJobs').textContent = data.pending;
        document.getElementById('processingJobs').textContent = data.processing;
        document.getElementById('completedJobs').textContent = data.completed;
        document.getElementById('failedJobs').textContent = data.failed;
        document.getElementById('deadJobs').textContent = data.dead;
        document.getElementById('activeWorkers').textContent = data.active_workers;
    } catch (error) {
        console.error('Error loading status:', error);
        showToast('Error loading status', 'error');
    }
}

// Workers
async function loadWorkersStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/workers/status`);
        if (!response.ok) {
            // If endpoint doesn't exist, use status endpoint
            const statusResponse = await fetch(`${API_BASE}/api/status`);
            const statusData = await statusResponse.json();
            updateWorkerUI({
                running: statusData.active_workers > 0,
                active_count: statusData.active_workers,
                total_workers: statusData.active_workers
            });
            return;
        }
        
        const data = await response.json();
        updateWorkerUI(data);
    } catch (error) {
        console.error('Error loading workers status:', error);
        // Fallback to status endpoint
        try {
            const statusResponse = await fetch(`${API_BASE}/api/status`);
            const statusData = await statusResponse.json();
            updateWorkerUI({
                running: statusData.active_workers > 0,
                active_count: statusData.active_workers,
                total_workers: statusData.active_workers
            });
        } catch (e) {
            console.error('Error loading worker status fallback:', e);
        }
    }
}

function updateWorkerUI(data) {
    document.getElementById('workerStatus').textContent = data.running ? 'Running' : 'Stopped';
    document.getElementById('workerCountDisplay').textContent = data.active_count || 0;
    
    const statusDot = document.getElementById('workerStatusDot');
    const startBtn = document.getElementById('startWorkersBtn');
    const stopBtn = document.getElementById('stopWorkersBtn');
    
    if (data.running) {
        statusDot.classList.add('running');
        startBtn.disabled = true;
        startBtn.style.opacity = '0.5';
        stopBtn.disabled = false;
        stopBtn.style.opacity = '1';
    } else {
        statusDot.classList.remove('running');
        startBtn.disabled = false;
        startBtn.style.opacity = '1';
        stopBtn.disabled = true;
        stopBtn.style.opacity = '0.5';
    }
}

async function handleStartWorkers() {
    const count = parseInt(document.getElementById('workerCount').value) || 1;
    
    if (count < 1 || count > 10) {
        showToast('Worker count must be between 1 and 10', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/workers/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ count: count })
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(data.message || 'Workers started successfully!', 'success');
            loadWorkersStatus();
            loadStatus();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to start workers', 'error');
        }
    } catch (error) {
        console.error('Error starting workers:', error);
        showToast('Error starting workers', 'error');
    }
}

async function handleStopWorkers() {
    if (!confirm('Are you sure you want to stop all workers?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/workers/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            showToast(data.message || 'Workers stopped successfully!', 'success');
            loadWorkersStatus();
            loadStatus();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to stop workers', 'error');
        }
    } catch (error) {
        console.error('Error stopping workers:', error);
        showToast('Error stopping workers', 'error');
    }
}

// Jobs
let allJobs = [];

async function loadJobs() {
    try {
        const url = currentStateFilter 
            ? `${API_BASE}/api/jobs?state=${currentStateFilter}`
            : `${API_BASE}/api/jobs`;
        
        const response = await fetch(url);
        allJobs = await response.json();
        filterJobs();
    } catch (error) {
        console.error('Error loading jobs:', error);
        showToast('Error loading jobs', 'error');
    }
}

function filterJobs() {
    const tbody = document.getElementById('jobsTableBody');
    tbody.innerHTML = '';
    
    let filteredJobs = allJobs;
    
    if (searchFilter) {
        filteredJobs = allJobs.filter(job => 
            job.id.toLowerCase().includes(searchFilter) ||
            job.command.toLowerCase().includes(searchFilter)
        );
    }
    
    if (filteredJobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No jobs found</td></tr>';
        return;
    }
    
    filteredJobs.forEach(job => {
        const row = createJobRow(job);
        tbody.appendChild(row);
    });
}

function createJobRow(job) {
    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.addEventListener('click', () => showJobDetails(job.id));
    
    const stateBadge = `<span class="state-badge ${job.state}">${job.state}</span>`;
    const attempts = `${job.attempts}/${job.max_retries}`;
    const command = job.command.length > 60 
        ? job.command.substring(0, 60) + '...' 
        : job.command;
    
    const createdDate = new Date(job.created_at).toLocaleString();
    const updatedDate = new Date(job.updated_at).toLocaleString();
    
    let actions = '';
    if (job.state === 'dead') {
        actions = `<button class="btn-success" style="padding: 6px 12px; font-size: 12px;" onclick="event.stopPropagation(); retryJob('${job.id}')">Retry</button> `;
    }
    actions += `<button class="btn-danger" style="padding: 6px 12px; font-size: 12px;" onclick="event.stopPropagation(); deleteJob('${job.id}')">Delete</button>`;
    
    tr.innerHTML = `
        <td><strong>${job.id}</strong></td>
        <td>${stateBadge}</td>
        <td>${attempts}</td>
        <td title="${job.command}">${command}</td>
        <td class="text-muted text-small">${createdDate}</td>
        <td class="text-muted text-small">${updatedDate}</td>
        <td>${actions}</td>
    `;
    
    return tr;
}

async function showJobDetails(jobId) {
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${jobId}`);
        if (!response.ok) {
            showToast('Job not found', 'error');
            return;
        }
        
        const job = await response.json();
        const detailsDiv = document.getElementById('jobDetails');
        
        const createdDate = new Date(job.created_at).toLocaleString();
        const updatedDate = new Date(job.updated_at).toLocaleString();
        const nextRetryDate = job.next_retry_at ? new Date(job.next_retry_at).toLocaleString() : 'N/A';
        
        detailsDiv.innerHTML = `
            <div class="detail-item">
                <strong>Job ID</strong>
                <div>${job.id}</div>
            </div>
            <div class="detail-item">
                <strong>State</strong>
                <div><span class="state-badge ${job.state}">${job.state}</span></div>
            </div>
            <div class="detail-item">
                <strong>Command</strong>
                <code>${job.command}</code>
            </div>
            <div class="detail-item">
                <strong>Attempts</strong>
                <div>${job.attempts} / ${job.max_retries}</div>
            </div>
            <div class="detail-item">
                <strong>Created At</strong>
                <div>${createdDate}</div>
            </div>
            <div class="detail-item">
                <strong>Updated At</strong>
                <div>${updatedDate}</div>
            </div>
            <div class="detail-item">
                <strong>Next Retry At</strong>
                <div>${nextRetryDate}</div>
            </div>
            ${job.error_message ? `
            <div class="detail-item" style="background: #fee2e2; border-color: #ef4444;">
                <strong>Error Message</strong>
                <div style="color: #ef4444;">${job.error_message}</div>
            </div>
            ` : ''}
            <div class="detail-actions">
                ${job.state === 'dead' ? `<button class="btn-success" onclick="retryJob('${job.id}'); closeJobDetailsModal();">Retry Job</button>` : ''}
                <button class="btn-danger" onclick="deleteJob('${job.id}'); closeJobDetailsModal();">Delete Job</button>
            </div>
        `;
        
        document.getElementById('jobDetailsModal').style.display = 'block';
    } catch (error) {
        console.error('Error loading job details:', error);
        showToast('Error loading job details', 'error');
    }
}

function closeJobDetailsModal() {
    document.getElementById('jobDetailsModal').style.display = 'none';
}

async function deleteJob(jobId) {
    if (!confirm(`Are you sure you want to delete job '${jobId}'?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${jobId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Job deleted successfully!', 'success');
            loadStatus();
            loadJobs();
            loadDLQ();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to delete job', 'error');
        }
    } catch (error) {
        console.error('Error deleting job:', error);
        showToast('Error deleting job', 'error');
    }
}

// DLQ
async function loadDLQ() {
    try {
        const response = await fetch(`${API_BASE}/api/dlq`);
        const jobs = await response.json();
        
        const container = document.getElementById('dlqContainer');
        container.innerHTML = '';
        
        if (jobs.length === 0) {
            container.innerHTML = '<div class="empty-state">No jobs in Dead Letter Queue</div>';
            return;
        }
        
        jobs.forEach(job => {
            const item = createDLQItem(job);
            container.appendChild(item);
        });
    } catch (error) {
        console.error('Error loading DLQ:', error);
        showToast('Error loading DLQ', 'error');
    }
}

function createDLQItem(job) {
    const div = document.createElement('div');
    div.className = 'dlq-item';
    
    const createdDate = new Date(job.created_at).toLocaleString();
    const updatedDate = new Date(job.updated_at).toLocaleString();
    
    div.innerHTML = `
        <h3>${job.id}</h3>
        <p><strong>Command:</strong> ${job.command}</p>
        <p><strong>Attempts:</strong> ${job.attempts} / ${job.max_retries}</p>
        <p><strong>Failed At:</strong> ${updatedDate}</p>
        ${job.error_message ? `<p class="error"><strong>Error:</strong> ${job.error_message}</p>` : ''}
        <div class="dlq-actions">
            <button class="btn-success" onclick="retryJob('${job.id}')">Retry Job</button>
            <button class="btn-danger" onclick="deleteJob('${job.id}')">Delete</button>
        </div>
    `;
    
    return div;
}

// Configuration
async function loadConfig() {
    try {
        const response = await fetch(`${API_BASE}/api/config`);
        const config = await response.json();
        
        const tbody = document.getElementById('configTableBody');
        tbody.innerHTML = '';
        
        const keyMap = {
            'max_retries': 'max-retries',
            'backoff_base': 'backoff-base',
            'worker_poll_interval': 'worker-poll-interval',
            'job_timeout': 'job-timeout'
        };
        
        for (const [key, value] of Object.entries(config)) {
            const displayKey = keyMap[key] || key;
            const description = CONFIG_DESCRIPTIONS[displayKey] || '';
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${displayKey}</strong></td>
                <td>${value}</td>
                <td class="text-muted">${description}</td>
                <td><button class="btn-primary" style="padding: 6px 12px; font-size: 12px;" onclick="openConfigModal('${displayKey}', '${value}')">Edit</button></td>
            `;
            tbody.appendChild(tr);
        }
    } catch (error) {
        console.error('Error loading config:', error);
        showToast('Error loading configuration', 'error');
    }
}

function openConfigModal(key, value) {
    currentEditingConfigKey = key;
    document.getElementById('configKeyLabel').textContent = key + ':';
    document.getElementById('configValueInput').value = value;
    document.getElementById('configDescription').textContent = CONFIG_DESCRIPTIONS[key] || '';
    document.getElementById('configModal').style.display = 'block';
}

function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
    currentEditingConfigKey = null;
}

async function handleConfigEdit(e) {
    e.preventDefault();
    
    if (!currentEditingConfigKey) return;
    
    const value = document.getElementById('configValueInput').value;
    
    try {
        const response = await fetch(`${API_BASE}/api/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                key: currentEditingConfigKey,
                value: value
            })
        });
        
        if (response.ok) {
            showToast('Configuration updated successfully!', 'success');
            closeConfigModal();
            loadConfig();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to update configuration', 'error');
        }
    } catch (error) {
        console.error('Error updating config:', error);
        showToast('Error updating configuration', 'error');
    }
}

// Enqueue Job
function openJobModal() {
    document.getElementById('jobModal').style.display = 'block';
}

function closeJobModal() {
    document.getElementById('jobModal').style.display = 'none';
    document.getElementById('enqueueForm').reset();
}

async function handleEnqueue(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const jobData = {
        id: formData.get('jobId'),
        command: formData.get('jobCommand'),
        max_retries: parseInt(formData.get('maxRetries')) || 3
    };
    
    try {
        const response = await fetch(`${API_BASE}/api/jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jobData)
        });
        
        if (response.ok) {
            showToast('Job enqueued successfully!', 'success');
            closeJobModal();
            loadStatus();
            loadJobs();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to enqueue job', 'error');
        }
    } catch (error) {
        console.error('Error enqueueing job:', error);
        showToast('Error enqueueing job', 'error');
    }
}

async function retryJob(jobId) {
    try {
        const response = await fetch(`${API_BASE}/api/jobs/${jobId}/retry`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showToast('Job moved back to queue for retry', 'success');
            loadStatus();
            loadJobs();
            loadDLQ();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to retry job', 'error');
        }
    } catch (error) {
        console.error('Error retrying job:', error);
        showToast('Error retrying job', 'error');
    }
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Global functions for onclick handlers
window.showSection = showSection;
window.openJobModal = openJobModal;
window.closeJobModal = closeJobModal;
window.closeJobDetailsModal = closeJobDetailsModal;
window.openConfigModal = openConfigModal;
window.closeConfigModal = closeConfigModal;
window.retryJob = retryJob;
window.deleteJob = deleteJob;
