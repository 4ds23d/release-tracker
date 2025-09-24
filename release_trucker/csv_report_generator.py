import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Any
from dataclasses import dataclass
from collections import defaultdict

from .analyzer import ProjectAnalysis


@dataclass
class JiraTicketSummary:
    """Summary information for a JIRA ticket across environments."""
    ticket_id: str
    project: str
    environments: Set[str]
    total_environments: int
    first_seen_version: str = ""
    latest_version: str = ""
    first_commit_date: str = ""
    latest_commit_date: str = ""


@dataclass
class JiraTicketDetail:
    """Detailed information for a JIRA ticket in a specific environment."""
    ticket_id: str
    project: str
    environment: str
    version: str
    commit_id: str
    commit_date: str
    commit_message: str


class CSVReportGenerator:
    """Generates CSV reports for JIRA ticket analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_csv_report(self, analyses: List[ProjectAnalysis], output_file: str, format_type: str = "summary"):
        """
        Generate CSV report from project analyses.
        
        Args:
            analyses: List of ProjectAnalysis objects
            output_file: Output CSV file path
            format_type: Type of CSV format ('summary' or 'detailed')
        """
        self.logger.info(f"Generating {format_type} CSV report: {output_file}")
        
        if format_type == "summary":
            self._generate_summary_report(analyses, output_file)
        elif format_type == "detailed":
            self._generate_detailed_report(analyses, output_file)
        else:
            raise ValueError(f"Unsupported CSV format: {format_type}")
        
        self.logger.info(f"CSV report generated successfully: {output_file}")
    
    def _generate_summary_report(self, analyses: List[ProjectAnalysis], output_file: str):
        """Generate summary CSV report showing tickets across environments."""
        # Collect all JIRA tickets and their environment information
        ticket_summaries = self._collect_ticket_summaries(analyses)
        
        # Define environment order for consistent columns
        env_order = ["DEV", "TEST", "PRE", "PROD"]
        
        # Write CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['JIRA_Ticket', 'Project'] + env_order + [
                'Total_Environments', 'First_Seen_Version', 'Latest_Version', 
                'First_Commit_Date', 'Latest_Commit_Date'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Sort tickets alphabetically for consistent output
            for summary in sorted(ticket_summaries, key=lambda x: (x.project, x.ticket_id)):
                row = {
                    'JIRA_Ticket': summary.ticket_id,
                    'Project': summary.project,
                    'Total_Environments': summary.total_environments,
                    'First_Seen_Version': summary.first_seen_version,
                    'Latest_Version': summary.latest_version,
                    'First_Commit_Date': summary.first_commit_date,
                    'Latest_Commit_Date': summary.latest_commit_date
                }
                
                # Add Yes/No for each environment
                for env in env_order:
                    row[env] = 'Yes' if env in summary.environments else 'No'
                
                writer.writerow(row)
        
        self.logger.info(f"Summary CSV report written with {len(ticket_summaries)} JIRA tickets")
    
    def _generate_detailed_report(self, analyses: List[ProjectAnalysis], output_file: str):
        """Generate detailed CSV report showing each ticket occurrence."""
        # Collect all JIRA ticket details
        ticket_details = self._collect_ticket_details(analyses)
        
        # Write CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'JIRA_Ticket', 'Project', 'Environment', 'Version', 
                'Commit_ID', 'Commit_Date', 'Commit_Message'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Sort by project, ticket, environment for consistent output
            for detail in sorted(ticket_details, key=lambda x: (x.project, x.ticket_id, x.environment)):
                writer.writerow({
                    'JIRA_Ticket': detail.ticket_id,
                    'Project': detail.project,
                    'Environment': detail.environment,
                    'Version': detail.version,
                    'Commit_ID': detail.commit_id[:8] if detail.commit_id else '',  # Short commit ID
                    'Commit_Date': detail.commit_date,
                    'Commit_Message': self._clean_commit_message(detail.commit_message)
                })
        
        self.logger.info(f"Detailed CSV report written with {len(ticket_details)} ticket entries")
    
    def _collect_ticket_summaries(self, analyses: List[ProjectAnalysis]) -> List[JiraTicketSummary]:
        """Collect and aggregate JIRA ticket information for summary report."""
        # Dictionary to track ticket information: (project, ticket_id) -> summary data
        ticket_data: Dict[tuple, Dict[str, Any]] = defaultdict(lambda: {
            'environments': set(),
            'versions': [],
            'commit_dates': []
        })
        
        # Process each project analysis
        for analysis in analyses:
            project_name = analysis.project_name
            
            # Process each environment in the project
            for env_name, env_commits in analysis.environments.items():
                # Add each JIRA ticket found in this environment
                for ticket_id in env_commits.jira_tickets:
                    key = (project_name, ticket_id)
                    ticket_data[key]['environments'].add(env_name)
                    ticket_data[key]['versions'].append(env_commits.version)
                    
                    # Extract commit dates from commits containing this ticket
                    for commit in env_commits.commits:
                        if ticket_id in commit.get('message', ''):
                            commit_date = commit.get('date', '')
                            if commit_date:
                                ticket_data[key]['commit_dates'].append(commit_date)
        
        # Convert to JiraTicketSummary objects
        summaries = []
        for (project_name, ticket_id), data in ticket_data.items():
            # Sort versions and dates to get first and latest
            versions = sorted(set(data['versions']))
            dates = sorted(data['commit_dates'])
            
            summary = JiraTicketSummary(
                ticket_id=ticket_id,
                project=project_name,
                environments=data['environments'],
                total_environments=len(data['environments']),
                first_seen_version=versions[0] if versions else '',
                latest_version=versions[-1] if versions else '',
                first_commit_date=dates[0][:10] if dates else '',  # Just date part
                latest_commit_date=dates[-1][:10] if dates else ''  # Just date part
            )
            summaries.append(summary)
        
        return summaries
    
    def _collect_ticket_details(self, analyses: List[ProjectAnalysis]) -> List[JiraTicketDetail]:
        """Collect detailed JIRA ticket information for detailed report."""
        details = []
        
        # Process each project analysis
        for analysis in analyses:
            project_name = analysis.project_name
            
            # Process each environment in the project
            for env_name, env_commits in analysis.environments.items():
                # Process each commit in this environment
                for commit in env_commits.commits:
                    commit_message = commit.get('message', '')
                    commit_date = commit.get('date', '')
                    commit_id = commit.get('id', '')
                    
                    # Extract JIRA tickets from this commit message
                    tickets_in_commit = self._extract_jira_tickets_from_message(commit_message)
                    
                    # Create detail entry for each ticket in this commit
                    for ticket_id in tickets_in_commit:
                        detail = JiraTicketDetail(
                            ticket_id=ticket_id,
                            project=project_name,
                            environment=env_name,
                            version=env_commits.version,
                            commit_id=commit_id,
                            commit_date=commit_date[:10] if commit_date else '',  # Just date part
                            commit_message=commit_message
                        )
                        details.append(detail)
        
        return details
    
    def _extract_jira_tickets_from_message(self, message: str) -> Set[str]:
        """Extract JIRA ticket IDs from a commit message."""
        import re
        jira_pattern = re.compile(r'\b([A-Z]{1,10}-\d+)\b')
        return set(jira_pattern.findall(message))
    
    def _clean_commit_message(self, message: str) -> str:
        """Clean commit message for CSV output."""
        if not message:
            return ''
        
        # Remove newlines and excessive whitespace
        cleaned = ' '.join(message.split())
        
        # Truncate if too long (for CSV readability)
        if len(cleaned) > 100:
            cleaned = cleaned[:97] + '...'
        
        # Escape quotes for CSV
        cleaned = cleaned.replace('"', '""')
        
        return cleaned
    
    def get_ticket_statistics(self, analyses: List[ProjectAnalysis]) -> Dict[str, Any]:
        """Get statistics about JIRA tickets across all projects."""
        ticket_summaries = self._collect_ticket_summaries(analyses)
        
        # Calculate statistics
        total_tickets = len(ticket_summaries)
        tickets_by_env = defaultdict(int)
        tickets_by_project = defaultdict(int)
        multi_env_tickets = 0
        
        for summary in ticket_summaries:
            tickets_by_project[summary.project] += 1
            if summary.total_environments > 1:
                multi_env_tickets += 1
            
            for env in summary.environments:
                tickets_by_env[env] += 1
        
        return {
            'total_tickets': total_tickets,
            'tickets_by_environment': dict(tickets_by_env),
            'tickets_by_project': dict(tickets_by_project),
            'multi_environment_tickets': multi_env_tickets,
            'single_environment_tickets': total_tickets - multi_env_tickets
        }