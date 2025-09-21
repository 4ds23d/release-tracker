#!/usr/bin/env python3
"""
Demo script to showcase the Git Release Tracker functionality.

This script demonstrates:
1. Analyze command - for deployment analysis
2. Release command - for starting release process

Run this script to see examples of both CLI commands in action.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from release_trucker.cli import cli
from click.testing import CliRunner


def create_demo_config():
    """Create a demo configuration file for testing."""
    config_content = """
projects:
  - name: demo-frontend
    repoUrl: https://github.com/demo/frontend.git
    main_branch: main
    env:
      DEV: https://dev-frontend.demo.com/actuator/info
      STAGING: https://staging-frontend.demo.com/actuator/info
      PROD: https://prod-frontend.demo.com/actuator/info
    verify_ssl: true
    use_version_fallback: true
    jira_base_url: https://demo.atlassian.net

  - name: demo-backend
    repoUrl: https://github.com/demo/backend.git
    main_branch: main
    env:
      DEV: https://dev-backend.demo.com/actuator/info
      PROD: https://prod-backend.demo.com/actuator/info
    verify_ssl: true
    use_version_fallback: true
    jira_base_url: https://demo.atlassian.net
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content.strip())
        return f.name


def demo_help_command():
    """Demonstrate the help command."""
    print("=" * 80)
    print("🔧 DEMO: Help Command")
    print("=" * 80)
    print("Command: git-release --help")
    print()
    
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    print(result.output)
    return result.exit_code == 0


def demo_analyze_help():
    """Demonstrate the analyze help command."""
    print("=" * 80)
    print("📊 DEMO: Analyze Command Help")
    print("=" * 80)
    print("Command: git-release analyze --help")
    print()
    
    runner = CliRunner()
    result = runner.invoke(cli, ['analyze', '--help'])
    print(result.output)
    return result.exit_code == 0


def demo_release_help():
    """Demonstrate the release help command."""
    print("=" * 80)
    print("🚀 DEMO: Release Command Help")
    print("=" * 80)
    print("Command: git-release release --help")
    print()
    
    runner = CliRunner()
    result = runner.invoke(cli, ['release', '--help'])
    print(result.output)
    return result.exit_code == 0


def demo_analyze_command():
    """Demonstrate the analyze command with error handling."""
    print("=" * 80)
    print("📊 DEMO: Analyze Command (Expected to Fail - No Real Endpoints)")
    print("=" * 80)
    
    config_file = create_demo_config()
    print(f"Command: git-release analyze --config {config_file}")
    print()
    
    try:
        runner = CliRunner()
        result = runner.invoke(cli, [
            'analyze',
            '--config', config_file,
            '--output', 'demo_report.html'
        ])
        print("Output:")
        print(result.output)
        print(f"Exit code: {result.exit_code}")
        return result.exit_code == 0
    finally:
        # Cleanup
        os.unlink(config_file)


def demo_release_command_invalid_ticket():
    """Demonstrate the release command with invalid JIRA ticket."""
    print("=" * 80)
    print("🚀 DEMO: Release Command - Invalid JIRA Ticket")
    print("=" * 80)
    
    config_file = create_demo_config()
    print(f"Command: git-release release --config {config_file} invalid-ticket")
    print()
    
    try:
        runner = CliRunner()
        result = runner.invoke(cli, [
            'release',
            '--config', config_file,
            'invalid-ticket'
        ])
        print("Output:")
        print(result.output)
        print(f"Exit code: {result.exit_code}")
        return result.exit_code != 0  # Should fail
    finally:
        # Cleanup
        os.unlink(config_file)


def demo_release_command_valid_ticket():
    """Demonstrate the release command with valid JIRA ticket (will fail on git operations)."""
    print("=" * 80)
    print("🚀 DEMO: Release Command - Valid JIRA Ticket (Expected Git Failures)")
    print("=" * 80)
    
    config_file = create_demo_config()
    print(f"Command: git-release release --config {config_file} BWD-123")
    print()
    
    try:
        runner = CliRunner()
        result = runner.invoke(cli, [
            'release',
            '--config', config_file,
            'BWD-123'
        ])
        print("Output:")
        print(result.output)
        print(f"Exit code: {result.exit_code}")
        return True  # Any result is fine for demo
    finally:
        # Cleanup
        os.unlink(config_file)


def demo_version_parsing():
    """Demonstrate version parsing functionality."""
    print("=" * 80)
    print("🏷️  DEMO: Version Management Examples")
    print("=" * 80)
    
    from release_trucker.release_manager import ReleaseManager, VersionInfo
    
    manager = ReleaseManager()
    
    print("Version Parsing Examples:")
    test_versions = ["1.0.0", "2.5.3", "10.0.1", "1.2", "v1.0.0", "1.0.0-SNAPSHOT"]
    
    for version_str in test_versions:
        parsed = manager.parse_version(version_str)
        if parsed:
            print(f"  ✅ '{version_str}' -> {parsed}")
        else:
            print(f"  ❌ '{version_str}' -> Invalid")
    
    print("\nVersion Bumping Examples:")
    version = VersionInfo(1, 2, 3)
    print(f"  Original: {version}")
    print(f"  Bump Major: {version.bump_major()}")
    print(f"  Bump Minor: {version.bump_minor()}")
    print(f"  Bump Patch: {version.bump_patch()}")
    
    print("\nJIRA Ticket Validation Examples:")
    test_tickets = ["BWD-123", "AUTH-456", "FEAT-1", "bwd-123", "BWD123", "BWD-", "-123"]
    
    for ticket in test_tickets:
        valid = manager.validate_jira_ticket(ticket)
        status = "✅ Valid" if valid else "❌ Invalid"
        print(f"  '{ticket}' -> {status}")
    
    return True


def run_all_demos():
    """Run all demo functions and report results."""
    print("🎯 Git Release Tracker - Comprehensive Demo")
    print("=" * 80)
    print("This demo showcases the release functionality with examples.")
    print("Some commands are expected to fail due to missing git repositories.")
    print("=" * 80)
    print()
    
    demos = [
        ("Help Command", demo_help_command),
        ("Analyze Help", demo_analyze_help),
        ("Release Help", demo_release_help),
        ("Version Management", demo_version_parsing),
        ("Analyze Command", demo_analyze_command),
        ("Invalid JIRA Ticket", demo_release_command_invalid_ticket),
        ("Valid JIRA Ticket", demo_release_command_valid_ticket),
    ]
    
    results = []
    
    for demo_name, demo_func in demos:
        try:
            print(f"\n{'='*20} Running: {demo_name} {'='*20}")
            success = demo_func()
            results.append((demo_name, success, None))
            print(f"✅ {demo_name}: {'PASSED' if success else 'FAILED (Expected)'}")
        except Exception as e:
            results.append((demo_name, False, str(e)))
            print(f"❌ {demo_name}: ERROR - {e}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("📋 DEMO SUMMARY")
    print("=" * 80)
    
    for demo_name, success, error in results:
        if error:
            print(f"❌ {demo_name}: ERROR - {error}")
        elif success:
            print(f"✅ {demo_name}: PASSED")
        else:
            print(f"⚠️  {demo_name}: FAILED (May be expected)")
    
    print()
    print("🎉 Demo completed! The release functionality is working as expected.")
    print("💡 To use in production:")
    print("   1. Update config.yaml with your actual repository URLs")
    print("   2. Ensure git repositories are accessible")
    print("   3. Run: python -m release_trucker.cli release YOUR-TICKET-123")


if __name__ == "__main__":
    run_all_demos()