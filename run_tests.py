#!/usr/bin/env python3
"""
Test runner script for Git Release Tracker
Runs all tests and provides a summary of the results.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print(f"   ✅ {description} - PASSED")
            return True, result.stdout
        else:
            print(f"   ❌ {description} - FAILED")
            print(f"   Error: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"   ❌ {description} - ERROR: {e}")
        return False, str(e)

def main():
    print("🚀 Git Release Tracker - Test Suite")
    print("=" * 50)
    
    tests = [
        ("python3 -m pytest tests/test_release_manager.py -v", "Release Manager Tests"),
        ("python3 -m pytest tests/test_config.py -v", "Configuration Tests"),
        ("python3 -m pytest tests/test_git_manager.py -v", "Git Manager Tests"),
        ("python3 -m pytest tests/test_cli.py -v", "CLI Tests"),
        ("python3 -m pytest tests/test_csv_report_generator.py -v", "CSV Report Generator Tests"),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    print(f"\n📋 Running {total_tests} test suites...\n")
    
    for cmd, description in tests:
        success, output = run_command(cmd, description)
        if success:
            passed_tests += 1
            # Extract test count from output
            lines = output.split('\n')
            for line in lines:
                if 'passed' in line and '=====' in line:
                    print(f"   📊 {line.strip()}")
                    break
        print()
    
    print("=" * 50)
    print(f"📊 Test Summary:")
    print(f"   ✅ Passed: {passed_tests}/{total_tests} test suites")
    print(f"   {'🎉 ALL TESTS PASSED!' if passed_tests == total_tests else '❌ Some tests failed'}")
    
    # Test CLI functionality
    print(f"\n🔧 Testing CLI functionality...")
    
    cli_tests = [
        ("python3 -m release_trucker.cli --help", "CLI Help"),
        ("python3 -m release_trucker.cli analyze --help", "Analyze Command Help"),
        ("python3 -m release_trucker.cli release --help", "Release Command Help"),
        ("python3 -c 'import release_trucker.csv_report_generator; print(\"CSV module imports successfully\")'", "CSV Module Import"),
    ]
    
    cli_passed = 0
    for cmd, description in cli_tests:
        success, output = run_command(cmd, description)
        if success:
            cli_passed += 1
    
    print(f"\n📊 CLI Test Summary:")
    print(f"   ✅ Passed: {cli_passed}/{len(cli_tests)} CLI tests")
    
    # Overall summary
    all_passed = passed_tests == total_tests and cli_passed == len(cli_tests)
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED!' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🚀 Features tested and working:")
        print("   ✅ Release Management (GitPython-based)")
        print("   ✅ Deployment Analysis")
        print("   ✅ HTML Report Generation")
        print("   ✅ CSV Report Generation (Summary & Detailed formats)")
        print("   ✅ JIRA Ticket Tracking")
        print("   ✅ CLI Interface with CSV options")
        print("   ✅ Configuration Management")
        print("   ✅ Git Operations")
        print("   ✅ Remote Change Detection")
        
        print("\n📊 CSV Report Features:")
        print("   ✅ Summary format: Ticket environment matrix")
        print("   ✅ Detailed format: Individual ticket occurrences")
        print("   ✅ JIRA ticket statistics")
        print("   ✅ Environment progression tracking")
        print("   ✅ Version and commit information")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())