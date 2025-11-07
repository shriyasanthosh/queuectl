# QueueCTL

QueueCTL is a small command line based background job queue system.  
It can enqueue jobs, run multiple workers to process them, automatically retry failed jobs, and move permanently failed ones to a Dead Letter Queue (DLQ).  
I built this as part of the **Flam Backend Developer Internship Assignment**.

---

## Overview

The main idea was to build a CLI tool that behaves like a simplified job queue used in production systems.  
Everything runs locally and uses JSON files to store jobs so that the data stays even after restarts.  
I've also made it configurable so that retry counts, backoff time, etc., can be changed easily.

---

## Features

- Add and manage jobs using commands  
- Run multiple workers at once  
- Automatic retries with exponential backoff  
- Dead Letter Queue for failed jobs  
- JSON file based persistent storage  
- Graceful shutdown for workers  
- Configurable options for retries, delays, etc.  
- Simple web dashboard for monitoring

---

## Tech Stack

- Python 3  
- Click (for CLI commands)  
- Flask (for web dashboard)
- Threading (for parallel job processing)  
- JSON for data storage  

---

## How to Run

1. Clone the repo:
   ```bash
   git clone https://github.com/shriyasanthosh/queuectl.git
   cd queuectl
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Mac/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package:
   ```bash
   pip install -e .
   ```

Now you can use the `queuectl` command directly.

## Example Commands

**Enqueue a job:**
```bash
queuectl enqueue '{"id":"job1","command":"echo Hello World"}'
```

**Start workers:**
```bash
queuectl worker start --count 2
```

**Check status:**
```bash
queuectl status
```

**View jobs in DLQ:**
```bash
queuectl dlq list
```

**Retry a DLQ job:**
```bash
queuectl dlq retry job1
```

**Start web dashboard:**
```bash
queuectl web
```
Then open http://127.0.0.1:5000 in your browser.

## Job Lifecycle

1. **pending** – waiting to be picked
2. **processing** – currently being executed
3. **completed** – finished successfully
4. **failed** – retried with exponential backoff
5. **dead** – moved to DLQ after all retries

**Example:**  
If backoff base = 2, retries will happen after 2s, 4s, 8s, and so on.

## Folder Structure

```
queuectl/
│
├── cli.py          # command definitions
├── worker.py       # worker logic
├── storage.py      # json storage
├── executor.py     # handles job execution
├── config.py       # configuration handling
├── models.py       # job model and states
├── web.py          # web dashboard
├── templates/      # html templates
├── static/         # css and js files
├── setup.py
└── requirements.txt
```

## Testing

To test basic functionality:
```bash
python test_queuectl.py
```

Or you can enqueue some jobs manually and start multiple workers to see how they run in parallel.

## Design Notes

- Workers run as threads in the same process
- Each worker picks available jobs and executes them
- File locking is used to prevent data corruption
- The tool is meant to run locally on a single machine

## Future Improvements

Some ideas that can be added later:
- Priority queue support
- Scheduled jobs
- SQLite or Redis based storage
- More detailed job output logging

---

**Author**  
Shriya Santhosh  
Final Year AIML Student  
Submitted for Flam Backend Developer Internship Assignment

This project was mainly done to understand how background job systems work internally and to practice designing concurrent systems in Python.
