# QueueCTL - Step-by-Step Setup Commands

This document provides all the commands you need to run manually to set up and test QueueCTL.

## Step 1: Initial Setup

### 1.1 Navigate to Project Directory
```bash
cd C:\Users\shriy\queuectl
```

### 1.2 Check Git Status
```bash
git status
```

### 1.3 Create Virtual Environment (Recommended)
```bash
python -m venv venv
```

### 1.4 Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 1.5 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.6 Install QueueCTL Package
```bash
pip install -e .
```

This installs the `queuectl` command.

### 1.7 Verify Installation
```bash
queuectl --version
```

Expected output: `queuectl, version 1.0.0`

## Step 2: Initial Git Commit

### 2.1 Add All Files
```bash
git add .
```

### 2.2 Make Initial Commit
```bash
git commit -m "Initial commit: QueueCTL project structure and core implementation"
```

### 2.3 Add Remote Repository (if not already added)
```bash
git remote add origin https://github.com/shriyasanthosh/queuectl.git
```

### 2.4 Push to GitHub
```bash
git push -u origin master
```

## Step 3: Basic Testing

### 3.1 Test Basic Enqueue
```bash
queuectl enqueue '{"id":"test1","command":"echo Hello World"}'
```

Expected output: `Job 'test1' enqueued successfully`

### 3.2 Check Status
```bash
queuectl status
```

Expected output should show 1 pending job.

### 3.3 List Jobs
```bash
queuectl list
```

### 3.4 Test Configuration
```bash
queuectl config show
```

### 3.5 Set Configuration
```bash
queuectl config set max-retries 5
queuectl config show
```

## Step 4: Test Worker Functionality

### 4.1 Enqueue a Simple Job
```bash
queuectl enqueue '{"id":"worker-test1","command":"echo Worker Test"}'
```

### 4.2 Start Worker (in foreground)
```bash
queuectl worker start --count 1
```

**Note:** This will run in the foreground. Open a NEW terminal window for the next steps.

### 4.3 In New Terminal: Check Status
```bash
cd C:\Users\shriy\queuectl
venv\Scripts\activate
queuectl status
```

Wait a few seconds and check again - job should be completed.

### 4.4 Stop Worker
Press `Ctrl+C` in the terminal where worker is running, or run:
```bash
queuectl worker stop
```

## Step 5: Test Retry and DLQ

### 5.1 Set Retry Configuration
```bash
queuectl config set max-retries 3
queuectl config set backoff-base 2.0
```

### 5.2 Enqueue a Failing Job
```bash
queuectl enqueue '{"id":"fail-test1","command":"invalid-command-xyz","max_retries":3}'
```

### 5.3 Start Worker
```bash
queuectl worker start --count 1
```

### 5.4 Monitor Progress (in another terminal)
```bash
queuectl list --state failed
queuectl status
```

Wait for retries to complete (about 14 seconds total: 2 + 4 + 8).

### 5.5 Check DLQ
```bash
queuectl dlq list
```

### 5.6 Retry from DLQ
```bash
queuectl dlq retry fail-test1
queuectl status
```

## Step 6: Test Multiple Workers

### 6.1 Enqueue Multiple Jobs
```bash
queuectl enqueue '{"id":"multi1","command":"sleep 1"}'
queuectl enqueue '{"id":"multi2","command":"sleep 1"}'
queuectl enqueue '{"id":"multi3","command":"sleep 1"}'
queuectl enqueue '{"id":"multi4","command":"sleep 1"}'
queuectl enqueue '{"id":"multi5","command":"sleep 1"}'
```

### 6.2 Start 3 Workers
```bash
queuectl worker start --count 3
```

### 6.3 Monitor (in another terminal)
```bash
queuectl status
```

Jobs should process in parallel.

## Step 7: Test Persistence

### 7.1 Enqueue Jobs
```bash
queuectl enqueue '{"id":"persist1","command":"echo test1"}'
queuectl enqueue '{"id":"persist2","command":"echo test2"}'
```

### 7.2 Check Status
```bash
queuectl status
```

### 7.3 Stop Workers
```bash
queuectl worker stop
```

### 7.4 Verify jobs.json Exists
```bash
type jobs.json
```

### 7.5 Restart and Check
```bash
queuectl status
```

Jobs should still be there.

## Step 8: Run Test Scripts

### 8.1 Run Basic Test
```bash
python test_queuectl.py
```

### 8.2 Run Specific Test Scenario
```bash
python test_scenarios.py --test basic
python test_scenarios.py --test retry
python test_scenarios.py --test workers
python test_scenarios.py --test persistence
```

## Step 9: Regular Git Commits

After each major test or feature verification, commit your progress:

```bash
git add .
git commit -m "Test: Verified [feature name] functionality"
git push
```

### Example Commit Messages:
```bash
git commit -m "Test: Verified basic job enqueue and execution"
git commit -m "Test: Verified retry mechanism and DLQ functionality"
git commit -m "Test: Verified multiple workers and parallel processing"
git commit -m "Test: Verified persistence across restarts"
```

## Step 10: Final Verification Checklist

Before final submission, verify:

- [ ] All commands work: `queuectl --help`
- [ ] Jobs persist after restart
- [ ] Retry mechanism works with exponential backoff
- [ ] DLQ functionality works
- [ ] Multiple workers process jobs correctly
- [ ] Configuration management works
- [ ] Test scripts run successfully
- [ ] README is complete
- [ ] All code is committed and pushed

## Step 11: Final Push

```bash
git add .
git commit -m "Final: Complete QueueCTL implementation with all features"
git push
```

## Troubleshooting Commands

### Check Python Version
```bash
python --version
```
Should be 3.7 or higher.

### Reinstall Package
```bash
pip uninstall queuectl
pip install -e .
```

### Clear All Jobs (for testing)
```bash
# Manually delete jobs.json
del jobs.json
```

### Check for Errors
```bash
python -m queuectl.cli --help
```

## Notes

1. **Workers run in foreground**: When you run `queuectl worker start`, it runs in the foreground. Use a separate terminal for other commands.

2. **Windows Command Line**: On Windows, use double quotes for JSON in some cases:
   ```bash
   queuectl enqueue "{\"id\":\"test1\",\"command\":\"echo hello\"}"
   ```

3. **Virtual Environment**: Always activate your virtual environment before running commands.

4. **File Locations**: 
   - Jobs stored in: `jobs.json`
   - Config stored in: `config.json`
   - Worker PID in: `worker.pid`

5. **Regular Commits**: Make commits after each major test to ensure progress is saved.

