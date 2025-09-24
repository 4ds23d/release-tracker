#!/usr/bin/env python3
"""
Demo script showing CSV report generation capabilities.

This script demonstrates how to use the CSV report generator
to create JIRA ticket reports in different formats.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("📊 CSV Report Generation Demo")
print("=" * 50)

print("\n🎯 Purpose:")
print("   Generate CSV reports showing JIRA ticket deployment status across environments")

print("\n📋 Available Formats:")
print("   • Summary Format (default): Shows tickets and their environment presence")
print("   • Detailed Format: Shows each ticket occurrence in each environment")

print("\n🔧 CLI Usage Examples:")
print("\n1. Generate HTML + Summary CSV:")
print("   python -m release_trucker.cli analyze --config config.yaml \\")
print("     --output report.html --csv-output jira-tickets.csv")

print("\n2. Generate Only Detailed CSV:")
print("   python -m release_trucker.cli analyze --config config.yaml \\")
print("     --csv-output detailed-tickets.csv --csv-format detailed --csv-only")

print("\n3. Generate Both Formats:")
print("   python -m release_trucker.cli analyze --config config.yaml \\")
print("     --csv-output summary.csv")
print("   python -m release_trucker.cli analyze --config config.yaml \\")
print("     --csv-output detailed.csv --csv-format detailed --csv-only")

print("\n📄 Sample Output Files:")
print("   • examples/sample_jira_tickets_summary.csv - Summary format example")
print("   • examples/sample_jira_tickets_detailed.csv - Detailed format example")

print("\n📊 CSV Report Benefits:")
print("   ✅ Track JIRA ticket progression through environments")
print("   ✅ Import into Excel/Google Sheets for analysis")
print("   ✅ Verify deployment status across projects")
print("   ✅ Share status with stakeholders")
print("   ✅ Identify tickets ready for promotion")

print("\n🗂️  Summary CSV Columns:")
print("   • JIRA_Ticket - Ticket identifier (e.g., BWD-123)")
print("   • Project - Project name")
print("   • DEV/TEST/PRE/PROD - Yes/No for each environment")
print("   • Total_Environments - Count of environments")
print("   • First_Seen_Version - Earliest version containing ticket")
print("   • Latest_Version - Most recent version containing ticket")
print("   • First_Commit_Date - Date of first commit")
print("   • Latest_Commit_Date - Date of latest commit")

print("\n📄 Detailed CSV Columns:")
print("   • JIRA_Ticket - Ticket identifier")
print("   • Project - Project name")
print("   • Environment - Environment name")
print("   • Version - Version deployed in that environment")
print("   • Commit_ID - Short commit hash")
print("   • Commit_Date - Date of the commit")
print("   • Commit_Message - Commit message (cleaned/truncated)")

print("\n🚀 Integration Options:")
print("   • Jenkins pipelines can archive CSV reports as artifacts")
print("   • Automated generation on deployment schedules")
print("   • Import into BI tools for dashboard creation")
print("   • Email reports to stakeholders")

print("\n💡 Tips:")
print("   • Use summary format for overview and tracking")
print("   • Use detailed format for audit trails and investigation")
print("   • Combine with HTML reports for comprehensive analysis")
print("   • Archive historical CSV files to track trends over time")

print(f"\n✅ Demo complete! Check the sample files in {project_root}/examples/")