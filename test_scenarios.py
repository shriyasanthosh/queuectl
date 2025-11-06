#!/usr/bin/env python3
"""
Detailed test scenarios for QueueCTL
"""
import subprocess
import time
import argparse
import sys
from pathlib import Path


def run_cmd(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def cleanup():
    """Clean up test files"""
    for f in ["jobs.json", "config.json", "worker.pid"]:
        if Path(f).exists():
            Path(f).unlink()


def test_basic():
    """Test basic job completion"""
    print("\n" + "=" * 60)
    print("TEST SCENARIO: Basic Job Completion")
    print("=" * 60)
    cleanup()
    
    print("\n1. Enqueue a simple job:")
    stdout, stderr, code = run_cmd('queuectl enqueue \'{"id":"basic1","command":"echo Hello World"}\'')
    print(f"   Command: queuectl enqueue '{{\"id\":\"basic1\",\"command\":\"echo Hello World\"}}'")
    print(f"   Output: {stdout}")
    
    print("\n2. Check status:")
    stdout, _, _ = run_cmd("queuectl status")
    print(stdout)
    
    print("\n3. Start worker (run in separate terminal):")
    print("   queuectl worker start --count 1")
    print("\n   Wait 2-3 seconds, then check status again:")
    print("   queuectl status")
    print("\n   Expected: Job should be in 'completed' state")
    
    print("\n4. List completed jobs:")
    print("   queuectl list --state completed")
    
    return True


def test_retry():
    """Test retry and DLQ"""
    print("\n" + "=" * 60)
    print("TEST SCENARIO: Retry and Dead Letter Queue")
    print("=" * 60)
    cleanup()
    
    print("\n1. Set retry configuration:")
    run_cmd("queuectl config set max-retries 3")
    run_cmd("queuectl config set backoff-base 2.0")
    print("   Configuration set: max-retries=3, backoff-base=2.0")
    
    print("\n2. Enqueue a job that will fail:")
    stdout, _, _ = run_cmd('queuectl enqueue \'{"id":"retry1","command":"invalid-command-xyz","max_retries":3}\'')
    print(f"   Output: {stdout}")
    
    print("\n3. Start worker (run in separate terminal):")
    print("   queuectl worker start --count 1")
    print("\n   Expected behavior:")
    print("   - Job fails immediately")
    print("   - Retries after 2 seconds (2^1)")
    print("   - Retries after 4 seconds (2^2)")
    print("   - Retries after 8 seconds (2^3)")
    print("   - After 3 retries, moves to DLQ")
    
    print("\n4. Monitor progress:")
    print("   queuectl list --state failed  # Check retries")
    print("   queuectl dlq list            # Check DLQ after max retries")
    
    print("\n5. Retry from DLQ:")
    print("   queuectl dlq retry retry1")
    print("   queuectl status")
    
    return True


def test_workers():
    """Test multiple workers"""
    print("\n" + "=" * 60)
    print("TEST SCENARIO: Multiple Workers")
    print("=" * 60)
    cleanup()
    
    print("\n1. Enqueue multiple jobs:")
    for i in range(1, 6):
        run_cmd(f'queuectl enqueue \'{{"id":"worker{i}","command":"sleep 1"}}\'')
    print("   Enqueued 5 jobs with 'sleep 1' command")
    
    print("\n2. Check status:")
    stdout, _, _ = run_cmd("queuectl status")
    print(stdout)
    
    print("\n3. Start 3 workers (run in separate terminal):")
    print("   queuectl worker start --count 3")
    print("\n   Expected: 3 jobs should process in parallel")
    print("   All 5 jobs should complete faster than sequential processing")
    
    print("\n4. Monitor progress:")
    print("   queuectl status  # Check processing/completed counts")
    print("   queuectl list   # See job states")
    
    return True


def test_persistence():
    """Test persistence across restarts"""
    print("\n" + "=" * 60)
    print("TEST SCENARIO: Persistence Across Restarts")
    print("=" * 60)
    cleanup()
    
    print("\n1. Enqueue jobs:")
    run_cmd('queuectl enqueue \'{"id":"persist1","command":"echo test1"}\'')
    run_cmd('queuectl enqueue \'{"id":"persist2","command":"echo test2"}\'')
    print("   Enqueued 2 jobs")
    
    print("\n2. Check status:")
    stdout, _, _ = run_cmd("queuectl status")
    print(stdout)
    
    print("\n3. Stop workers (if running):")
    print("   queuectl worker stop")
    
    print("\n4. Verify jobs.json exists:")
    if Path("jobs.json").exists():
        print("   ✅ jobs.json file exists")
        with open("jobs.json") as f:
            import json
            data = json.load(f)
            print(f"   Contains {len(data)} jobs")
    
    print("\n5. Restart and check status:")
    print("   queuectl status")
    print("   Expected: Jobs should still be present")
    
    print("\n6. Start worker again:")
    print("   queuectl worker start --count 1")
    print("   Expected: Jobs should be processed")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="QueueCTL Test Scenarios")
    parser.add_argument(
        "--test",
        choices=["basic", "retry", "workers", "persistence", "all"],
        default="all",
        help="Test scenario to run"
    )
    
    args = parser.parse_args()
    
    scenarios = {
        "basic": test_basic,
        "retry": test_retry,
        "workers": test_workers,
        "persistence": test_persistence
    }
    
    if args.test == "all":
        for name, test_func in scenarios.items():
            test_func()
            print("\n" + "=" * 60 + "\n")
    else:
        scenarios[args.test]()
    
    print("\n✅ Test scenario completed!")
    print("Follow the instructions above to verify functionality.")


if __name__ == "__main__":
    main()

