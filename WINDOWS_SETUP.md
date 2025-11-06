# QueueCTL - Windows Setup Guide

## ⚠️ Important: Windows-Specific Commands

On Windows, you need to use `py` instead of `python` for most commands.

## Step-by-Step Setup for Windows

### Step 1: Check Python Installation

```bash
py --version
```

**Expected Output**: Python 3.7 or higher (e.g., `Python 3.13.7`)

If this doesn't work, install Python from https://www.python.org/downloads/

### Step 2: Navigate to Project Directory

```bash
cd C:\Users\shriy\queuectl
```

### Step 3: Create Virtual Environment

```bash
py -m venv venv
```

**Note**: You may see a warning "Could not find platform independent libraries <prefix>" - this is usually safe to ignore.

### Step 4: Activate Virtual Environment

```bash
venv\Scripts\activate
```

**Expected**: You should see `(venv)` at the start of your command prompt.

### Step 5: Install Dependencies

```bash
py -m pip install -r requirements.txt
```

### Step 6: Install QueueCTL Package

```bash
py -m pip install -e .
```

### Step 7: Verify Installation

```bash
queuectl --help
```

**Expected**: Should show help menu with all available commands.

## Alternative: If `queuectl` command doesn't work

If the `queuectl` command is not found, you can run it directly:

```bash
python -m queuectl.cli --help
python -m queuectl.cli enqueue '{"id":"test1","command":"echo hello"}'
python -m queuectl.cli status
```

Or create an alias (optional):

```bash
# In PowerShell
Set-Alias queuectl "python -m queuectl.cli"

# In CMD (add to your PATH or create a batch file)
```

## Common Windows Issues and Solutions

### Issue 1: "Python was not found"

**Solution**: Use `py` instead of `python`:
```bash
py -m venv venv
py -m pip install -r requirements.txt
```

### Issue 2: "pip: Fatal error in launcher"

**Solution**: Use `py -m pip` instead of `pip`:
```bash
py -m pip install -r requirements.txt
```

### Issue 3: JSON Quotes in Windows CMD

If single quotes don't work for JSON, use double quotes with escaped quotes:

```bash
# Instead of:
queuectl enqueue '{"id":"test1","command":"echo hello"}'

# Use:
queuectl enqueue "{\"id\":\"test1\",\"command\":\"echo hello\"}"
```

Or use PowerShell which handles single quotes better.

### Issue 4: Virtual Environment Not Activating

Make sure you're in the correct directory:
```bash
cd C:\Users\shriy\queuectl
venv\Scripts\activate
```

## All Commands Using `py` (Windows)

```bash
# Setup
py -m venv venv
venv\Scripts\activate
py -m pip install -r requirements.txt
py -m pip install -e .

# Usage (after installation)
queuectl enqueue '{"id":"test1","command":"echo hello"}'
queuectl status
queuectl worker start --count 1

# Or use direct module execution
python -m queuectl.cli enqueue '{"id":"test1","command":"echo hello"}'
python -m queuectl.cli status
```

## Testing on Windows

### Test 1: Basic Enqueue

```bash
# Activate venv first
venv\Scripts\activate

# Enqueue job
queuectl enqueue "{\"id\":\"test1\",\"command\":\"echo Hello World\"}"

# Check status
queuectl status
```

### Test 2: Start Worker

**Terminal 1:**
```bash
venv\Scripts\activate
queuectl worker start --count 1
```

**Terminal 2:**
```bash
cd C:\Users\shriy\queuectl
venv\Scripts\activate
queuectl status
```

## PowerShell Alternative

If you prefer PowerShell, it handles JSON quotes better:

```powershell
# PowerShell
cd C:\Users\shriy\queuectl
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m pip install -e .

# Usage (single quotes work in PowerShell)
queuectl enqueue '{"id":"test1","command":"echo hello"}'
```

## Quick Reference

| Task | Windows Command |
|------|----------------|
| Create venv | `py -m venv venv` |
| Activate venv | `venv\Scripts\activate` |
| Install deps | `py -m pip install -r requirements.txt` |
| Install package | `py -m pip install -e .` |
| Run command | `queuectl <command>` or `python -m queuectl.cli <command>` |

## Need Help?

If you encounter issues:
1. Make sure Python is installed: `py --version`
2. Make sure you're in the project directory: `cd C:\Users\shriy\queuectl`
3. Make sure venv is activated: You should see `(venv)` in prompt
4. Try using `python -m queuectl.cli` instead of `queuectl`

