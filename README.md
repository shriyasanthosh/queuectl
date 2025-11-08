# QueueCTL

A simple command-line job queue system I built for the Flam Backend Developer Internship Assignment. You can enqueue jobs, run workers to process them, and it automatically retries failed jobs with exponential backoff. Jobs that fail too many times get moved to a Dead Letter Queue.

---

## What It Does

Think of it like a simplified version of Celery or Sidekiq, but running locally. Jobs are stored in JSON files so they persist across restarts. You can configure retry counts, backoff times, and other settings.

Key features:
- Enqueue jobs via CLI
- Run multiple workers in parallel
- Automatic retries with exponential backoff
- Dead Letter Queue for permanently failed jobs
- Priority queues (higher priority jobs run first)
- Scheduled jobs (run at a specific time)
- Job output logging (stdout/stderr)
- Execution metrics
- Web dashboard for monitoring

---

## Setup

You'll need Python 3.7 or higher.

```bash
git clone https://github.com/shriyasanthosh/queuectl.git
cd queuectl
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
pip install -e .
```

That's it. Now you can use `queuectl` from anywhere.

---

## Usage

### Basic Commands

Enqueue a job:
```bash
queuectl enqueue '{"id":"job1","command":"echo Hello World"}'
```

Start 2 workers:
```bash
queuectl worker start --count 2
```

Check status:
```bash
queuectl status
```

List all jobs:
```bash
queuectl list
```

### Advanced Features

Job with priority (higher number = higher priority):
```bash
queuectl enqueue '{"id":"important","command":"process.sh","priority":8}'
```

Scheduled job:
```bash
queuectl enqueue '{"id":"backup","command":"backup.sh","run_at":"2024-12-01T10:00:00Z"}'
```

View job output:
```bash
queuectl job output job1
```

View metrics:
```bash
queuectl metrics
```

### Dead Letter Queue

Jobs that fail after all retries end up in the DLQ:
```bash
queuectl dlq list
queuectl dlq retry job5  # Move job back to queue
```

### Configuration

```bash
queuectl config show
queuectl config set max-retries 5
queuectl config set backoff-base 3.0
```

### Web Dashboard

```bash
queuectl web
```

Then open http://127.0.0.1:5000 in your browser. You can create jobs, start/stop workers, view metrics, and manage the DLQ from there.

---

## How It Works

### Job States

Jobs go through these states:
- `pending` - waiting to be picked up
- `processing` - currently running
- `completed` - finished successfully
- `failed` - failed but will retry (if retries left)
- `dead` - moved to DLQ after max retries

Flow: `pending → processing → completed` (or `failed → retry → processing → completed`, or `failed → dead`)

### Retry Logic

If a job fails, it waits before retrying. The wait time doubles each time (exponential backoff). With `backoff_base = 2`:
- First retry: wait 2 seconds
- Second retry: wait 4 seconds
- Third retry: wait 8 seconds
- After max retries: move to DLQ

### Data Storage

Everything is stored in JSON files:
- `jobs.json` - all job data (state, attempts, output, etc.)
- `config.json` - configuration settings

This means jobs survive restarts. If you stop the workers and start them again, pending jobs will still be there.

### Workers

Workers run as threads in the same process. Each worker:
1. Polls for available jobs
2. Claims a job (atomically, to prevent race conditions)
3. Executes it
4. Saves the result
5. Repeats

Multiple workers can run in parallel. They use file locking to prevent data corruption when reading/writing jobs.

### Priority

Jobs with higher priority values are processed first. Default is 5 (range 1-10). If two jobs have the same priority, the older one goes first.

### Scheduled Jobs

Set a `run_at` field (ISO 8601 format) and the job won't be picked up until that time. Useful for scheduling backups or maintenance tasks.

---

## Design Decisions

I made a few choices to keep things simple:

**JSON files instead of a database:** Easier to debug, no external dependencies, but not great for very high throughput.

**Threads instead of processes:** Simpler shared state, easier to debug, but limited by Python's GIL for CPU-bound tasks.

**File locking instead of transactions:** Works fine for single-machine use, but wouldn't scale to distributed systems.

**Persistent storage:** Jobs need to survive restarts, so everything goes to disk. Slightly slower than in-memory, but worth it.

**Simple retry strategy:** Exponential backoff with fixed max retries. No fancy scheduling or job dependencies, but covers most use cases.

**Both CLI and web dashboard:** CLI is faster for automation, web dashboard is better for monitoring. Both use the same backend.

What's missing:
- No job dependencies (can't say "run job B after job A completes")
- No job cancellation (once it starts, it runs to completion)
- No resource limits (jobs can use unlimited CPU/memory)
- No automatic cleanup (old jobs stay until you delete them)
- No authentication on web dashboard (assumes local/trusted network)

---

## Testing

Run the automated tests:
```bash
python test_queuectl.py
```

Or test manually:

```bash
# Basic test
queuectl enqueue '{"id":"test1","command":"echo Test"}'
queuectl worker start --count 1
# Wait a bit, then check
queuectl status
queuectl worker stop

# Test retries
queuectl enqueue '{"id":"fail1","command":"exit 1","max_retries":2}'
queuectl worker start --count 1
# Watch it retry a few times, then move to DLQ

# Test DLQ
queuectl dlq list
queuectl dlq retry fail1

# Test priority
queuectl enqueue '{"id":"low","command":"echo Low","priority":1}'
queuectl enqueue '{"id":"high","command":"echo High","priority":10}'
queuectl worker start --count 1
# High priority should run first
```

---

## Project Structure

```
queuectl/
├── queuectl/
│   ├── cli.py          # CLI commands
│   ├── worker.py       # Worker logic
│   ├── storage.py      # JSON storage
│   ├── executor.py     # Job execution
│   ├── config.py       # Configuration
│   ├── models.py       # Job model
│   ├── web.py          # Web dashboard
│   └── templates/      # HTML templates
├── test_queuectl.py    # Tests
├── setup.py
└── requirements.txt
```

Each file has a clear purpose. CLI handles commands, worker handles processing, storage handles persistence, etc.

---

## Author

Shriya Santhosh  
Final Year AIML Student  
Submitted for Flam Backend Developer Internship Assignment

I built this to understand how job queue systems work internally and to practice building concurrent systems in Python.
