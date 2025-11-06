# QueueCTL - Complete Testing Guide

## ✅ Status: Basic Functionality Verified!

Your QueueCTL is working! The job you enqueued has been processed and completed successfully.

## 🧪 Next: Comprehensive Testing

### Test 1: Verify Job Details ✅ (Already Done)
```bash
queuectl list
queuectl list --state completed
```

### Test 2: Test Retry Mechanism

**Terminal 1:**
```bash
venv\Scripts\activate
queuectl config set max-retries 3
queuectl config set backoff-base 2.0
queuectl enqueue "{\"id\":\"retry-test\",\"command\":\"invalid-command-xyz\",\"max_retries\":3}"
queuectl worker start --count 1
```

**Terminal 2:**
```bash
venv\Scripts\activate
# Wait 2 seconds, then check
queuectl list --state failed
queuectl status

# Wait 4 more seconds (total 6), check again
queuectl status

# Wait 8 more seconds (total 14), check DLQ
queuectl dlq list
```

**Expected:**
- Job fails immediately
- Retries after 2 seconds (2^1)
- Retries after 4 seconds (2^2)
- Retries after 8 seconds (2^3)
- Moves to DLQ after 3 retries

### Test 3: Test DLQ Retry

**Terminal 1:**
```bash
venv\Scripts\activate
# Stop worker (Ctrl+C) if still running
```

**Terminal 2:**
```bash
venv\Scripts\activate
# Check DLQ
queuectl dlq list

# Retry the DLQ job
queuectl dlq retry retry-test

# Check status
queuectl status

# Start worker again (Terminal 1)
queuectl worker start --count 1
```

### Test 4: Multiple Workers

**Terminal 1:**
```bash
venv\Scripts\activate
# Enqueue multiple jobs
queuectl enqueue "{\"id\":\"multi1\",\"command\":\"sleep 1\"}"
queuectl enqueue "{\"id\":\"multi2\",\"command\":\"sleep 1\"}"
queuectl enqueue "{\"id\":\"multi3\",\"command\":\"sleep 1\"}"
queuectl enqueue "{\"id\":\"multi4\",\"command\":\"sleep 1\"}"
queuectl enqueue "{\"id\":\"multi5\",\"command\":\"sleep 1\"}"

# Start 3 workers
queuectl worker start --count 3
```

**Terminal 2:**
```bash
venv\Scripts\activate
queuectl status
# Wait 2-3 seconds
queuectl status
queuectl list --state completed
```

**Expected:** 3 jobs should process in parallel, all 5 complete faster than sequential

### Test 5: Persistence

**Terminal 1:**
```bash
venv\Scripts\activate
# Enqueue jobs
queuectl enqueue "{\"id\":\"persist1\",\"command\":\"echo test1\"}"
queuectl enqueue "{\"id\":\"persist2\",\"command\":\"echo test2\"}"

# Check status
queuectl status

# Stop worker (Ctrl+C if running)
```

**Terminal 2:**
```bash
# Verify jobs.json exists
type jobs.json

# Restart and check
venv\Scripts\activate
queuectl status
```

**Expected:** Jobs should still be present after restart

### Test 6: Configuration Management

```bash
venv\Scripts\activate
# Show config
queuectl config show

# Set config
queuectl config set max-retries 5
queuectl config set backoff-base 3.0

# Verify
queuectl config show
```

### Test 7: Run Test Scripts

```bash
venv\Scripts\activate
python test_queuectl.py
python test_scenarios.py --test basic
python test_scenarios.py --test retry
python test_scenarios.py --test workers
python test_scenarios.py --test persistence
```

## 📊 Validation Checklist

Before final submission, verify:

- [x] Basic job enqueue and execution ✅
- [ ] Failed job retries with exponential backoff
- [ ] Jobs move to DLQ after max retries
- [ ] DLQ retry functionality
- [ ] Multiple workers process jobs in parallel
- [ ] Jobs persist across restarts
- [ ] Configuration management works
- [ ] All CLI commands work

## 📝 Commit Progress

After each test, commit your progress:

```bash
git add .
git commit -m "Test: Verified [feature name]"
git push origin master
```

## 🎯 Final Steps

1. Complete all tests above
2. Verify all features work
3. Update README if needed
4. Make final commit
5. Push to GitHub
6. Verify repository is complete

## ✅ Success Criteria

Your project is ready when:
- All commands work without errors
- Jobs persist after restart
- Retry mechanism works correctly
- DLQ functionality works
- Multiple workers work correctly
- Configuration management works
- Test scripts run successfully
- All code committed and pushed

Good luck! 🚀

