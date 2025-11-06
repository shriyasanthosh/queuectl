# QueueCTL - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### 1. Install Dependencies
```bash
cd C:\Users\shriy\queuectl
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### 2. Verify Installation
```bash
queuectl --version
```

### 3. Test Basic Functionality
```bash
# Enqueue a job
queuectl enqueue '{"id":"test1","command":"echo Hello World"}'

# Check status
queuectl status

# Start worker (in one terminal)
queuectl worker start --count 1

# In another terminal, check status again
queuectl status
```

## 📋 All Available Commands

### Job Management
```bash
# Enqueue a job
queuectl enqueue '{"id":"job1","command":"echo hello"}'

# List all jobs
queuectl list

# List jobs by state
queuectl list --state pending
queuectl list --state completed
queuectl list --state failed
queuectl list --state dead

# Check queue status
queuectl status
```

### Worker Management
```bash
# Start 1 worker
queuectl worker start

# Start multiple workers
queuectl worker start --count 3

# Stop workers (Ctrl+C or)
queuectl worker stop
```

### Dead Letter Queue (DLQ)
```bash
# List DLQ jobs
queuectl dlq list

# Retry a DLQ job
queuectl dlq retry job1
```

### Configuration
```bash
# Show current config
queuectl config show

# Set configuration
queuectl config set max-retries 5
queuectl config set backoff-base 3.0
queuectl config set worker-poll-interval 0.5
queuectl config set job-timeout 600
```

## 🧪 Testing Commands

### Run Test Suite
```bash
python test_queuectl.py
```

### Run Specific Test Scenario
```bash
python test_scenarios.py --test basic
python test_scenarios.py --test retry
python test_scenarios.py --test workers
python test_scenarios.py --test persistence
```

## 📝 Example Workflows

### Workflow 1: Basic Job Processing
```bash
# 1. Enqueue job
queuectl enqueue '{"id":"workflow1","command":"echo Success"}'

# 2. Start worker
queuectl worker start --count 1

# 3. Wait 2-3 seconds, then check
queuectl status
queuectl list --state completed
```

### Workflow 2: Test Retry Mechanism
```bash
# 1. Set retry config
queuectl config set max-retries 3
queuectl config set backoff-base 2.0

# 2. Enqueue failing job
queuectl enqueue '{"id":"retry-test","command":"invalid-cmd","max_retries":3}'

# 3. Start worker
queuectl worker start --count 1

# 4. Monitor (in another terminal)
queuectl list --state failed
queuectl status

# 5. After ~14 seconds, check DLQ
queuectl dlq list
```

### Workflow 3: Multiple Workers
```bash
# 1. Enqueue multiple jobs
queuectl enqueue '{"id":"w1","command":"sleep 1"}'
queuectl enqueue '{"id":"w2","command":"sleep 1"}'
queuectl enqueue '{"id":"w3","command":"sleep 1"}'

# 2. Start 3 workers
queuectl worker start --count 3

# 3. Monitor
queuectl status
```

## 🔧 Troubleshooting

### Command Not Found
```bash
# Reinstall package
pip install -e .
```

### Jobs Not Processing
```bash
# Check if workers are running
queuectl status

# Check job states
queuectl list --state pending
```

### Clear All Data (for testing)
```bash
# Delete storage files
del jobs.json
del config.json
del worker.pid
```

## 📦 Git Commands for Regular Commits

```bash
# After testing each feature
git add .
git commit -m "Test: Verified [feature]"
git push

# Example commits
git commit -m "Test: Verified basic job execution"
git commit -m "Test: Verified retry and DLQ functionality"
git commit -m "Test: Verified multiple workers"
git commit -m "Test: Verified persistence"
```

## 📚 Full Documentation

See `README.md` for complete documentation and `SETUP_COMMANDS.md` for detailed step-by-step setup.

