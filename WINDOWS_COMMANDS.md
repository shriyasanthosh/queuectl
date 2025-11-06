# QueueCTL - Windows Command Reference

## ✅ Setup is Complete!

Your QueueCTL is now installed and working. Here are all the commands you need.

## 🚀 Quick Start Commands

### Activate Virtual Environment (Always do this first)
```bash
cd C:\Users\shriy\queuectl
venv\Scripts\activate
```

### Basic Usage

```bash
# Enqueue a job (use double quotes with escaped quotes on Windows CMD)
queuectl enqueue "{\"id\":\"test1\",\"command\":\"echo hello\"}"

# Check status
queuectl status

# List jobs
queuectl list

# Start worker (Terminal 1)
queuectl worker start --count 1

# In Terminal 2, check status again
queuectl status
```

## 📋 Complete Command List

### Job Management

```bash
# Enqueue job
queuectl enqueue "{\"id\":\"job1\",\"command\":\"echo Hello World\"}"

# List all jobs
queuectl list

# List by state
queuectl list --state pending
queuectl list --state completed
queuectl list --state failed
queuectl list --state dead

# Check status
queuectl status
```

### Worker Management

```bash
# Start 1 worker
queuectl worker start

# Start multiple workers
queuectl worker start --count 3

# Stop workers (Press Ctrl+C in the terminal where worker is running)
```

### Dead Letter Queue

```bash
# List DLQ jobs
queuectl dlq list

# Retry a DLQ job
queuectl dlq retry job1
```

### Configuration

```bash
# Show config
queuectl config show

# Set config
queuectl config set max-retries 5
queuectl config set backoff-base 3.0
queuectl config set worker-poll-interval 0.5
queuectl config set job-timeout 600
```

## 🧪 Testing Workflow

### Test 1: Basic Job Execution

**Terminal 1:**
```bash
venv\Scripts\activate
queuectl enqueue "{\"id\":\"basic1\",\"command\":\"echo Success\"}"
queuectl worker start --count 1
```

**Terminal 2:**
```bash
cd C:\Users\shriy\queuectl
venv\Scripts\activate
queuectl status
# Wait 2-3 seconds
queuectl status
queuectl list --state completed
```

### Test 2: Retry and DLQ

**Terminal 1:**
```bash
venv\Scripts\activate
queuectl config set max-retries 3
queuectl config set backoff-base 2.0
queuectl enqueue "{\"id\":\"retry1\",\"command\":\"invalid-command-xyz\",\"max_retries\":3}"
queuectl worker start --count 1
```

**Terminal 2:**
```bash
venv\Scripts\activate
queuectl list --state failed
queuectl status
# Wait ~14 seconds (2+4+8), then:
queuectl dlq list
```

### Test 3: Multiple Workers

**Terminal 1:**
```bash
venv\Scripts\activate
queuectl enqueue "{\"id\":\"w1\",\"command\":\"sleep 1\"}"
queuectl enqueue "{\"id\":\"w2\",\"command\":\"sleep 1\"}"
queuectl enqueue "{\"id\":\"w3\",\"command\":\"sleep 1\"}"
queuectl worker start --count 3
```

**Terminal 2:**
```bash
venv\Scripts\activate
queuectl status
```

## ⚠️ Important Notes

1. **Always activate venv first**: `venv\Scripts\activate`
2. **Use double quotes for JSON on Windows CMD**: `"{\"id\":\"test\",\"command\":\"echo hello\"}"`
3. **Workers run in foreground**: Use separate terminals for other commands
4. **Warning message**: The "Could not find platform independent libraries" warning is safe to ignore

## 🔧 Troubleshooting

### If `queuectl` command not found:
```bash
# Make sure venv is activated
venv\Scripts\activate

# Or use direct module execution
python -m queuectl.cli --help
```

### If JSON parsing fails:
```bash
# Use PowerShell instead of CMD (handles single quotes better)
# Or use double quotes with escaped quotes in CMD
```

### Clear all data for fresh start:
```bash
del jobs.json
del config.json
del worker.pid
```

## 📝 Git Commands

```bash
# After testing each feature
git add .
git commit -m "Test: Verified [feature name]"
git push origin master
```

## ✅ Success!

Your QueueCTL is working! You can now:
- Enqueue jobs ✅
- Start workers ✅
- Monitor status ✅
- Test retry mechanism ✅
- Test DLQ ✅

Good luck with your placement! 🎯

