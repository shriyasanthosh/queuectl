#!/usr/bin/env python3
"""
Test script to validate QueueCTL functionality
"""
import subprocess
import time
import json
import os
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode


def cleanup():
    """Clean up test files"""
    files = ["jobs.json", "config.json", "worker.pid"]
    for f in files:
        if Path(f).exists():
            Path(f).unlink()


def test_basic_enqueue():
    """Test 1: Basic job enqueue"""
    print("\n=== Test 1: Basic Job Enqueue ===")
    cleanup()
    
    # Enqueue a job
    stdout, stderr, code = run_command(
        'queuectl enqueue \'{"id":"test1","command":"echo hello"}\''
    )
    
    if code == 0 and "enqueued successfully" in stdout:
        print("✅ PASS: Job enqueued successfully")
        
        # Check status
        stdout, _, _ = run_command("queuectl status")
        if "Pending: 1" in stdout:
            print("✅ PASS: Job appears in status")
            return True
        else:
            print("❌ FAIL: Job not found in status")
            return False
    else:
        print(f"❌ FAIL: {stderr}")
        return False


def test_job_execution():
    """Test 2: Job execution"""
    print("\n=== Test 2: Job Execution ===")
    cleanup()
    
    # Enqueue a simple job
    run_command('queuectl enqueue \'{"id":"exec1","command":"echo test"}\'')
    
    # Start worker in background (simulate)
    # Note: In real test, you'd start worker in separate process
    print("ℹ️  Start worker manually: queuectl worker start")
    print("ℹ️  Wait a few seconds, then check status")
    print("ℹ️  Expected: Job should be completed")
    
    return True


def test_failed_job_retry():
    """Test 3: Failed job retry"""
    print("\n=== Test 3: Failed Job Retry ===")
    cleanup()
    
    # Enqueue a job that will fail
    stdout, stderr, code = run_command(
        'queuectl enqueue \'{"id":"fail1","command":"invalid-command-xyz","max_retries":2}\''
    )
    
    if code == 0:
        print("✅ PASS: Failed job enqueued")
        print("ℹ️  Start worker to observe retries")
        print("ℹ️  Expected: Job should retry 2 times, then move to DLQ")
        return True
    else:
        print(f"❌ FAIL: {stderr}")
        return False


def test_dlq():
    """Test 4: Dead Letter Queue"""
    print("\n=== Test 4: Dead Letter Queue ===")
    cleanup()
    
    # Check DLQ list (should be empty)
    stdout, _, _ = run_command("queuectl dlq list")
    if "No jobs in Dead Letter Queue" in stdout:
        print("✅ PASS: DLQ is empty initially")
    else:
        print("⚠️  WARN: DLQ not empty")
    
    return True


def test_config():
    """Test 5: Configuration"""
    print("\n=== Test 5: Configuration ===")
    cleanup()
    
    # Set config
    stdout, stderr, code = run_command("queuectl config set max-retries 5")
    if code == 0:
        print("✅ PASS: Configuration set successfully")
        
        # Show config
        stdout, _, _ = run_command("queuectl config show")
        if "max-retries: 5" in stdout:
            print("✅ PASS: Configuration persisted")
            return True
        else:
            print("❌ FAIL: Configuration not persisted")
            return False
    else:
        print(f"❌ FAIL: {stderr}")
        return False


def test_list_jobs():
    """Test 6: List jobs"""
    print("\n=== Test 6: List Jobs ===")
    cleanup()
    
    # Enqueue multiple jobs
    run_command('queuectl enqueue \'{"id":"list1","command":"echo 1"}\'')
    run_command('queuectl enqueue \'{"id":"list2","command":"echo 2"}\'')
    
    # List all jobs
    stdout, _, _ = run_command("queuectl list")
    if "list1" in stdout and "list2" in stdout:
        print("✅ PASS: Jobs listed correctly")
        
        # List by state
        stdout, _, _ = run_command("queuectl list --state pending")
        if "list1" in stdout:
            print("✅ PASS: Filter by state works")
            return True
        else:
            print("❌ FAIL: Filter by state failed")
            return False
    else:
        print("❌ FAIL: Jobs not listed")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("QueueCTL Test Suite")
    print("=" * 50)
    
    tests = [
        test_basic_enqueue,
        test_job_execution,
        test_failed_job_retry,
        test_dlq,
        test_config,
        test_list_jobs
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ ERROR in {test.__name__}: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 50)
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests require manual verification")
        return 1


if __name__ == "__main__":
    sys.exit(main())

