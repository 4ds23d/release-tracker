#!/usr/bin/env python3
"""
Generate a demo report with JIRA tickets for demonstration purposes.
This script creates mock data to showcase the JIRA integration feature.
"""

from datetime import datetime
from git_release_notifier.analyzer import ProjectAnalysis, EnvironmentCommits
from git_release_notifier.report_generator import HTMLReportGenerator
from git_release_notifier.config import ProjectConfig

def create_mock_analyses():
    """Create mock project analyses with JIRA tickets."""
    
    # Mock commits with JIRA tickets in messages
    dev_commits = [
        {
            "id": "a1b2c3d4e5f6",
            "short_id": "a1b2c3d",
            "message": "AUTH-123: Implement OAuth2 authentication flow",
            "summary": "AUTH-123: Implement OAuth2 authentication flow",
            "author": "John Developer",
            "date": "2024-01-15T14:30:00"
        },
        {
            "id": "b2c3d4e5f6g7",
            "short_id": "b2c3d4e",
            "message": "API-456: Add rate limiting middleware for USER-789",
            "summary": "API-456: Add rate limiting middleware for USER-789", 
            "author": "Jane Smith",
            "date": "2024-01-14T16:45:00"
        },
        {
            "id": "c3d4e5f6g7h8",
            "short_id": "c3d4e5f",
            "message": "PERF-101: Optimize database queries and caching",
            "summary": "PERF-101: Optimize database queries and caching",
            "author": "Mike Wilson",
            "date": "2024-01-14T10:20:00"
        }
    ]
    
    test_commits = [
        {
            "id": "d4e5f6g7h8i9",
            "short_id": "d4e5f6g", 
            "message": "BUGFIX-202: Fix null pointer exception in AUTH-123",
            "summary": "BUGFIX-202: Fix null pointer exception in AUTH-123",
            "author": "Sarah Johnson",
            "date": "2024-01-13T11:15:00"
        },
        {
            "id": "e5f6g7h8i9j0",
            "short_id": "e5f6g7h",
            "message": "FEAT-303: Add user profile management (REQ-404, REQ-405)",
            "summary": "FEAT-303: Add user profile management (REQ-404, REQ-405)",
            "author": "David Brown",
            "date": "2024-01-12T15:30:00"
        }
    ]
    
    pre_commits = [
        {
            "id": "f6g7h8i9j0k1",
            "short_id": "f6g7h8i",
            "message": "DEPLOY-501: Update configuration for production readiness",
            "summary": "DEPLOY-501: Update configuration for production readiness",
            "author": "Lisa Admin",
            "date": "2024-01-11T09:45:00"
        }
    ]
    
    # Create environment data with JIRA tickets
    user_service_envs = {
        "PROD": EnvironmentCommits(
            environment="PROD",
            version="2.1.0", 
            commit_id="9876543210abcdef",
            commits=[],
            jira_tickets=set()
        ),
        "PRE": EnvironmentCommits(
            environment="PRE",
            version="2.1.1",
            commit_id="f6g7h8i9j0k1",
            commits=pre_commits,
            jira_tickets={"DEPLOY-501"}
        ),
        "TEST": EnvironmentCommits(
            environment="TEST", 
            version="2.2.0",
            commit_id="e5f6g7h8i9j0",
            commits=test_commits,
            jira_tickets={"BUGFIX-202", "AUTH-123", "FEAT-303", "REQ-404", "REQ-405"}
        ),
        "DEV": EnvironmentCommits(
            environment="DEV",
            version="2.3.0-SNAPSHOT",
            commit_id="c3d4e5f6g7h8", 
            commits=dev_commits,
            jira_tickets={"AUTH-123", "API-456", "USER-789", "PERF-101"}
        )
    }
    
    # API Gateway commits
    gateway_dev_commits = [
        {
            "id": "x1y2z3a4b5c6",
            "short_id": "x1y2z3a",
            "message": "GATEWAY-111: Implement request routing and load balancing",
            "summary": "GATEWAY-111: Implement request routing and load balancing",
            "author": "Alex Router",
            "date": "2024-01-15T13:20:00"
        },
        {
            "id": "y2z3a4b5c6d7",
            "short_id": "y2z3a4b", 
            "message": "SEC-222: Add JWT token validation and CORS-333 support",
            "summary": "SEC-222: Add JWT token validation and CORS-333 support",
            "author": "Emma Security",
            "date": "2024-01-14T12:10:00"
        }
    ]
    
    gateway_test_commits = [
        {
            "id": "z3a4b5c6d7e8",
            "short_id": "z3a4b5c",
            "message": "MONITOR-444: Add health checks and metrics collection", 
            "summary": "MONITOR-444: Add health checks and metrics collection",
            "author": "Tom Monitor",
            "date": "2024-01-13T14:25:00"
        }
    ]
    
    gateway_envs = {
        "PROD": EnvironmentCommits(
            environment="PROD",
            version="1.5.0",
            commit_id="fedcba0987654321", 
            commits=[],
            jira_tickets=set()
        ),
        "PRE": EnvironmentCommits(
            environment="PRE",
            version="1.5.0",
            commit_id="fedcba0987654321",
            commits=[],
            jira_tickets=set()
        ),
        "TEST": EnvironmentCommits(
            environment="TEST",
            version="1.6.0",
            commit_id="z3a4b5c6d7e8",
            commits=gateway_test_commits,
            jira_tickets={"MONITOR-444"}
        ),
        "DEV": EnvironmentCommits(
            environment="DEV", 
            version="1.7.0-SNAPSHOT",
            commit_id="y2z3a4b5c6d7",
            commits=gateway_dev_commits,
            jira_tickets={"GATEWAY-111", "SEC-222", "CORS-333"}
        )
    }
    
    # Create project analyses
    analyses = [
        ProjectAnalysis(
            project_name="user-service",
            environments=user_service_envs
        ),
        ProjectAnalysis(
            project_name="api-gateway", 
            environments=gateway_envs
        )
    ]
    
    return analyses

def create_mock_project_configs():
    """Create mock project configurations with JIRA URLs."""
    return [
        ProjectConfig(
            name="user-service",
            repoUrl="https://github.com/company/user-service.git",
            env={
                "PROD": "https://users-prod.company.com",
                "PRE": "https://users-pre.company.com", 
                "TEST": "https://users-test.company.com",
                "DEV": "https://users-dev.company.com"
            },
            jira_base_url="https://company.atlassian.net"
        ),
        ProjectConfig(
            name="api-gateway",
            repoUrl="https://github.com/company/api-gateway.git",
            env={
                "PROD": "https://gateway-prod.company.com",
                "PRE": "https://gateway-pre.company.com",
                "TEST": "https://gateway-test.company.com", 
                "DEV": "https://gateway-dev.company.com"
            },
            jira_base_url="https://company.atlassian.net"
        )
    ]

def main():
    """Generate the demo report."""
    print("🎫 Generating demo report with JIRA tickets...")
    
    # Create mock data
    analyses = create_mock_analyses()
    project_configs = create_mock_project_configs()
    
    # Generate report
    report_generator = HTMLReportGenerator()
    output_file = "demo_jira_report.html"
    
    report_generator.generate_report(analyses, output_file, project_configs)
    
    print(f"✅ Demo report generated: {output_file}")
    print(f"📊 Included {len(analyses)} projects with JIRA integration")
    print("🎫 JIRA tickets included:")
    
    for analysis in analyses:
        print(f"\n  📦 {analysis.project_name}:")
        for env_name, env_data in analysis.environments.items():
            if env_data.jira_tickets:
                tickets = ", ".join(sorted(env_data.jira_tickets))
                print(f"    {env_name}: {tickets}")
    
    return output_file

if __name__ == "__main__":
    main()