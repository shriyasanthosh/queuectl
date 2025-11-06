# QueueCTL - Complete Manual Command List

This document contains ALL commands you need to run manually to set up, test, and use QueueCTL.

## ⚠️ IMPORTANT NOTES

1. **Workers run in foreground**: When you run `queuectl worker start`, it runs in the foreground. Use a **separate terminal window** for other commands.

2. **Virtual Environment**: Always activate your virtual environment before running commands:
   ```bash
   venv\Scripts\activate
   ```

3. **Windows JSON**: On Windows CMD, you may need to escape quotes differently. If single quotes don't work, try:
   ```bash
   queuectl enqueue "{\"id\":\"test1\",\"command\":\"echo hello\"}"
   ```

4. **Regular Commits**: After testing each feature, commit your progress for stability.

---

## 📦 SETUP PHASE

### Phase 1: Initial Setup

```bash
# 1. Navigate to project
cd C:\Users\shriy\queuectl

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install QueueCTL package
pip install -e .

# 6. Verify installation
queuectl --version
```

**Expected Output**: `queuectl, version 1.0.0`

### Phase 2: Initial Git Commit

```bash
# 1. Check status
git status

# 2. Add all files
git add .

# 3. Commit
git commit -m "Initial commit: QueueCTL project structure and core implementation"

# 4. Push to GitHub
git push -u origin master
```

---

## 🧪 TESTING PHASE

### Test 1: Basic Job Enqueue

```bash
# 1. Enqueue a simple job
queuectl enqueue '{"id":"test1","command":"echo Hello World"}'

# 2. Check status
queuectl status

# 3. List jobs
queuectl list

# 4. Commit progress
git add .
git commit -m "Test: Verified basic job enqueue"
git push
```

**Expected**: Job should appear in status as "Pending: 1"

### Test 2: Job Execution

```bash
# 1. Enqueue a job
queuectl enqueue '{"id":"exec1","command":"echo Test Execution"}'

# 2. Start worker (Terminal 1)
queuectl worker start --count 1

# 3. In Terminal 2, wait 2-3 seconds, then check status
queuectl status

# 4. Check completed jobs
queuectl list --state completed

# 5. Stop worker (Terminal 1: Press Ctrl+C)

# 6. Commit progress
git add .
git commit -m "Test: Verified job execution"
git push
```

**Expected**: Job should move from "pending" to "completed"

### Test 3: Configuration Management

```bash
# 1. Show current config
queuectl config show

# 2. Set max retries
queuectl config set max-retries 5

# 3. Set backoff base
queuectl config set backoff-base 3.0

# 4. Verify config
queuectl config show

# 5. Commit progress
git add .
git commit -m "Test: Verified configuration management"
git push
```

**Expected**: Configuration should persist and be displayed correctly

### Test 4: Retry Mechanism

```bash
# 1. Set retry config
queuectl config set max-retries 3
queuectl config set backoff-base 2.0

# 2. Enqueue a failing job
queuectl enqueue '{"id":"retry1","command":"invalid-command-xyz","max_retries":3}'

# 3. Start worker (Terminal 1)
queuectl worker start --count 1

# 4. In Terminal 2, monitor progress
queuectl list --state failed
queuectl status

# 5. Wait ~14 seconds (2 + 4 + 8), then check DLQ
queuectl dlq list

# 6. Stop worker (Terminal 1: Press Ctrl+C)

# 7. Commit progress
git add .
git commit -m "Test: Verified retry mechanism with exponential backoff"
git push
```

**Expected**: 
- Job fails immediately
- Retries after 2 seconds (2^1)
- Retries after 4 seconds (2^2)  
- Retries after 8 seconds (2^3)
- Moves to DLQ after max retries

### Test 5: Dead Letter Queue (DLQ)

```bash
# 1. Check DLQ (should have retry1 from Test 4)
queuectl dlq list

# 2. Retry a DLQ job
queuectl dlq retry retry1

# 3. Check status
queuectl status

# 4. Start worker (Terminal 1)
queuectl worker start --count 1

# 5. In Terminal 2, wait and check
queuectl status
queuectl list --state completed

# 6. Stop worker (Terminal 1: Press Ctrl+C)

# 7. Commit progress
git add .
git commit -m "Test: Verified DLQ functionality"
git push
```

**Expected**: DLQ job should be retried and can complete successfully

### Test 6: Multiple Workers

```bash
# 1. Enqueue multiple jobs
queuectl enqueue '{"id":"multi1","command":"sleep 1"}'
queuectl enqueue '{"id":"multi2","command":"sleep 1"}'
queuectl enqueue '{"id":"multi3","command":"sleep 1"}'
queuectl enqueue '{"id":"multi4","command":"sleep 1"}'
queuectl enqueue '{"id":"multi5","command":"sleep 1"}'

# 2. Check status
queuectl status

# 3. Start 3 workers (Terminal 1)
queuectl worker start --count 3

# 4. In Terminal 2, monitor
queuectl status

# 5. Wait and check again
queuectl status
queuectl list --state completed

# 6. Stop worker (Terminal 1: Press Ctrl+C)

# 7. Commit progress
git add .
git commit -m "Test: Verified multiple workers and parallel processing"
git push
```

**Expected**: 3 jobs should process in parallel, all 5 jobs complete faster than sequential

### Test 7: Persistence

```bash
# 1. Enqueue jobs
queuectl enqueue '{"id":"persist1","command":"echo test1"}'
queuectl enqueue '{"id":"persist2","command":"echo test2"}'

# 2. Check status
queuectl status

# 3. Verify jobs.json exists
type jobs.json

# 4. Stop workers (if running)
# (No workers running, so skip)

# 5. Restart and check status
queuectl status

# 6. Start worker (Terminal 1)
queuectl worker start --count 1

# 7. In Terminal 2, wait and check
queuectl status

# 8. Stop worker (Terminal 1: Press Ctrl+C)

# 9. Commit progress
git add .
git commit -m "Test: Verified persistence across restarts"
git push
```

**Expected**: Jobs should still be present after restart

### Test 8: Run Test Scripts

```bash
# 1. Run basic test suite
python test_queuectl.py

# 2. Run specific test scenarios
python test_scenarios.py --test basic
python test_scenarios.py --test retry
python test_scenarios.py --test workers
python test_scenarios.py --test persistence

# 3. Commit progress
git add .
git commit -m "Test: Verified all test scripts"
git push
```

---

## 📊 VALIDATION CHECKLIST

Before final submission, run through this checklist:

### Functionality Tests
- [ ] `queuectl enqueue` works
- [ ] `queuectl status` shows correct counts
- [ ] `queuectl list` displays jobs
- [ ] `queuectl list --state <state>` filters correctly
- [ ] `queuectl worker start` starts workers
- [ ] `queuectl worker start --count N` starts multiple workers
- [ ] Workers process jobs correctly
- [ ] Jobs complete successfully
- [ ] Failed jobs retry with exponential backoff
- [ ] Jobs move to DLQ after max retries
- [ ] `queuectl dlq list` shows DLQ jobs
- [ ] `queuectl dlq retry` retries DLQ jobs
- [ ] `queuectl config show` displays config
- [ ] `queuectl config set` updates config

### Data Persistence
- [ ] Jobs persist in `jobs.json`
- [ ] Config persists in `config.json`
- [ ] Jobs survive restart
- [ ] Config survives restart

### Edge Cases
- [ ] Invalid commands fail gracefully
- [ ] Duplicate job IDs are rejected
- [ ] Multiple workers don't process same job
- [ ] Graceful shutdown (Ctrl+C) works

### Documentation
- [ ] README.md is complete
- [ ] All commands documented
- [ ] Examples provided
- [ ] Architecture explained

---

## 🚀 FINAL SUBMISSION

### Final Commit and Push

```bash
# 1. Add all files
git add .

# 2. Final commit
git commit -m "Final: Complete QueueCTL implementation with all features and tests"

# 3. Push to GitHub
git push
```

### Verify Repository

1. Visit: https://github.com/shriyasanthosh/queuectl
2. Verify all files are present
3. Check README.md is visible
4. Verify commit history

---

## 🔧 TROUBLESHOOTING COMMANDS

### If Command Not Found
```bash
# Reinstall package
pip install -e .
```

### If Import Errors
```bash
# Check Python version
python --version

# Should be 3.7 or higher
```

### Clear All Data (for fresh start)
```bash
# Delete storage files
del jobs.json
del config.json
del worker.pid
```

### Check for Errors
```bash
# Test CLI directly
python -m queuectl.cli --help
```

---

## 📝 COMMIT MESSAGE TEMPLATES

Use these templates for regular commits:

```bash
git commit -m "Test: Verified basic job enqueue and execution"
git commit -m "Test: Verified retry mechanism with exponential backoff"
git commit -m "Test: Verified DLQ functionality"
git commit -m "Test: Verified multiple workers and parallel processing"
git commit -m "Test: Verified persistence across restarts"
git commit -m "Fix: [description of fix]"
git commit -m "Update: [description of update]"
```

---

## ✅ SUCCESS CRITERIA

Your project is ready for submission when:

1. ✅ All commands work without errors
2. ✅ Jobs persist after restart
3. ✅ Retry mechanism works correctly
4. ✅ DLQ functionality works
5. ✅ Multiple workers process jobs correctly
6. ✅ Configuration management works
7. ✅ Test scripts run successfully
8. ✅ README is complete and accurate
9. ✅ All code is committed and pushed
10. ✅ No plagiarism (all code is original)

---

**Good luck with your placement! 🎯**

