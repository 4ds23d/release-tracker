import pytest
import tempfile
import csv
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime

from release_trucker.csv_report_generator import CSVReportGenerator, JiraTicketSummary, JiraTicketDetail
from release_trucker.analyzer import ProjectAnalysis, EnvironmentCommits


class TestCSVReportGenerator:
    
    def setup_method(self):
        self.generator = CSVReportGenerator()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_mock_analysis(self, project_name: str, environments_data: dict) -> ProjectAnalysis:
        """Create a mock ProjectAnalysis with test data."""
        environments = {}
        for env_name, env_data in environments_data.items():
            # Create mock commits with JIRA tickets
            commits = []
            for ticket_id in env_data.get('tickets', []):
                commits.append({
                    'id': f'commit_{ticket_id}',
                    'message': f'{ticket_id}: Test commit message for {ticket_id}',
                    'date': env_data.get('date', '2024-01-15T10:00:00'),
                    'author': 'test@example.com',
                    'summary': f'{ticket_id}: Test commit'
                })
            
            # Create EnvironmentCommits
            env_commits = EnvironmentCommits(
                environment=env_name,
                version=env_data.get('version', '1.0.0'),
                commit_id=f'commit_{env_name}',
                commits=commits,
                jira_tickets=set(env_data.get('tickets', []))
            )
            environments[env_name] = env_commits
        
        return ProjectAnalysis(
            project_name=project_name,
            environments=environments,
            environment_order=["DEV", "TEST", "PRE", "PROD"]
        )
    
    def test_generate_summary_csv_report(self):
        """Test generating summary CSV report."""
        # Create mock analyses
        analyses = [
            self.create_mock_analysis('frontend-app', {
                'DEV': {'version': '2.1.0', 'tickets': ['BWD-123', 'AUTH-456'], 'date': '2024-01-15T10:00:00'},
                'TEST': {'version': '2.0.0', 'tickets': ['BWD-123'], 'date': '2024-01-10T10:00:00'},
            }),
            self.create_mock_analysis('backend-api', {
                'DEV': {'version': '1.5.0', 'tickets': ['AUTH-456', 'FEAT-789'], 'date': '2024-01-12T10:00:00'},
                'PROD': {'version': '1.0.0', 'tickets': ['FEAT-789'], 'date': '2024-01-05T10:00:00'},
            })
        ]
        
        # Generate CSV report
        csv_file = self.temp_dir / "summary_test.csv"
        self.generator.generate_csv_report(analyses, str(csv_file), "summary")
        
        # Verify file was created
        assert csv_file.exists()
        
        # Read and verify CSV content
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check that we have the expected number of rows
        assert len(rows) == 4  # BWD-123, AUTH-456 (frontend), AUTH-456, FEAT-789 (backend)
        
        # Verify column headers
        expected_headers = ['JIRA_Ticket', 'Project', 'DEV', 'TEST', 'PRE', 'PROD', 
                          'Total_Environments', 'First_Seen_Version', 'Latest_Version',
                          'First_Commit_Date', 'Latest_Commit_Date']
        assert list(rows[0].keys()) == expected_headers
        
        # Find and verify specific ticket
        bwd_123_row = next((row for row in rows if row['JIRA_Ticket'] == 'BWD-123'), None)
        assert bwd_123_row is not None
        assert bwd_123_row['Project'] == 'frontend-app'
        assert bwd_123_row['DEV'] == 'Yes'
        assert bwd_123_row['TEST'] == 'Yes'
        assert bwd_123_row['PRE'] == 'No'
        assert bwd_123_row['PROD'] == 'No'
        assert bwd_123_row['Total_Environments'] == '2'
    
    def test_generate_detailed_csv_report(self):
        """Test generating detailed CSV report."""
        # Create mock analysis
        analyses = [
            self.create_mock_analysis('test-project', {
                'DEV': {'version': '2.0.0', 'tickets': ['BWD-123'], 'date': '2024-01-15T10:00:00'},
                'TEST': {'version': '1.5.0', 'tickets': ['BWD-123'], 'date': '2024-01-10T10:00:00'},
            })
        ]
        
        # Generate CSV report
        csv_file = self.temp_dir / "detailed_test.csv"
        self.generator.generate_csv_report(analyses, str(csv_file), "detailed")
        
        # Verify file was created
        assert csv_file.exists()
        
        # Read and verify CSV content
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Check that we have the expected number of rows (BWD-123 in DEV and TEST)
        assert len(rows) == 2
        
        # Verify column headers
        expected_headers = ['JIRA_Ticket', 'Project', 'Environment', 'Version', 
                          'Commit_ID', 'Commit_Date', 'Commit_Message']
        assert list(rows[0].keys()) == expected_headers
        
        # Verify first row
        first_row = rows[0]
        assert first_row['JIRA_Ticket'] == 'BWD-123'
        assert first_row['Project'] == 'test-project'
        assert first_row['Environment'] in ['DEV', 'TEST']
        assert first_row['Version'] in ['2.0.0', '1.5.0']
        assert first_row['Commit_Message'].startswith('BWD-123: Test commit message')
    
    def test_invalid_format_raises_error(self):
        """Test that invalid format raises ValueError."""
        analyses = []
        csv_file = self.temp_dir / "invalid_test.csv"
        
        with pytest.raises(ValueError, match="Unsupported CSV format: invalid"):
            self.generator.generate_csv_report(analyses, str(csv_file), "invalid")
    
    def test_get_ticket_statistics(self):
        """Test ticket statistics calculation."""
        # Create mock analyses with various ticket distributions
        analyses = [
            self.create_mock_analysis('frontend-app', {
                'DEV': {'tickets': ['BWD-123', 'AUTH-456']},
                'TEST': {'tickets': ['BWD-123']},
                'PROD': {'tickets': ['OLD-999']},
            }),
            self.create_mock_analysis('backend-api', {
                'DEV': {'tickets': ['AUTH-456', 'FEAT-789']},
                'PROD': {'tickets': ['FEAT-789']},
            })
        ]
        
        # Get statistics
        stats = self.generator.get_ticket_statistics(analyses)
        
        # Verify statistics
        assert stats['total_tickets'] == 5  # BWD-123, AUTH-456, OLD-999, AUTH-456, FEAT-789
        assert stats['tickets_by_environment']['DEV'] == 4  # BWD-123, AUTH-456, AUTH-456, FEAT-789
        assert stats['tickets_by_environment']['TEST'] == 1  # BWD-123
        assert stats['tickets_by_environment']['PROD'] == 2  # OLD-999, FEAT-789
        assert stats['tickets_by_project']['frontend-app'] == 3  # BWD-123, AUTH-456, OLD-999
        assert stats['tickets_by_project']['backend-api'] == 2  # AUTH-456, FEAT-789
        
        # Check multi-environment tickets
        assert stats['multi_environment_tickets'] >= 1  # At least AUTH-456 is in multiple envs
    
    def test_extract_jira_tickets_from_message(self):
        """Test JIRA ticket extraction from commit messages."""
        # Test valid ticket patterns
        assert self.generator._extract_jira_tickets_from_message("BWD-123: Fix bug") == {'BWD-123'}
        assert self.generator._extract_jira_tickets_from_message("AUTH-456 and FEAT-789: Multiple tickets") == {'AUTH-456', 'FEAT-789'}
        assert self.generator._extract_jira_tickets_from_message("Merge PR with ABC-1, DEF-22, GHI-333") == {'ABC-1', 'DEF-22', 'GHI-333'}
        
        # Test invalid patterns
        assert self.generator._extract_jira_tickets_from_message("bwd-123: lowercase") == set()
        assert self.generator._extract_jira_tickets_from_message("123-BWD: wrong order") == set()
        assert self.generator._extract_jira_tickets_from_message("TOOLONGPROJECTNAME-123: too long") == set()
        
        # Test edge cases
        assert self.generator._extract_jira_tickets_from_message("") == set()
        assert self.generator._extract_jira_tickets_from_message("No tickets here") == set()
    
    def test_clean_commit_message(self):
        """Test commit message cleaning for CSV output."""
        # Test normal message
        clean_msg = self.generator._clean_commit_message("BWD-123: Fix authentication bug")
        assert clean_msg == "BWD-123: Fix authentication bug"
        
        # Test message with newlines and extra whitespace
        messy_msg = "BWD-123: Fix bug\n\nThis fixes the issue\n   with extra spaces"
        clean_msg = self.generator._clean_commit_message(messy_msg)
        assert clean_msg == "BWD-123: Fix bug This fixes the issue with extra spaces"
        
        # Test very long message (should be truncated)
        long_msg = "BWD-123: " + "a" * 100
        clean_msg = self.generator._clean_commit_message(long_msg)
        assert len(clean_msg) <= 100
        assert clean_msg.endswith("...")
        
        # Test message with quotes (should be escaped)
        quote_msg = 'BWD-123: Fix "quoted" issue'
        clean_msg = self.generator._clean_commit_message(quote_msg)
        assert clean_msg == 'BWD-123: Fix ""quoted"" issue'
        
        # Test empty message
        assert self.generator._clean_commit_message("") == ""
        assert self.generator._clean_commit_message(None) == ""
    
    def test_collect_ticket_summaries(self):
        """Test ticket summary collection."""
        # Create mock analysis with overlapping tickets
        analyses = [
            self.create_mock_analysis('frontend-app', {
                'DEV': {'version': '2.1.0', 'tickets': ['BWD-123'], 'date': '2024-01-15T10:00:00'},
                'TEST': {'version': '2.0.0', 'tickets': ['BWD-123'], 'date': '2024-01-10T10:00:00'},
            })
        ]
        
        # Collect summaries
        summaries = self.generator._collect_ticket_summaries(analyses)
        
        # Verify we get one summary for BWD-123
        assert len(summaries) == 1
        
        summary = summaries[0]
        assert isinstance(summary, JiraTicketSummary)
        assert summary.ticket_id == 'BWD-123'
        assert summary.project == 'frontend-app'
        assert summary.environments == {'DEV', 'TEST'}
        assert summary.total_environments == 2
        assert summary.first_seen_version == '2.0.0'  # Alphabetically first
        assert summary.latest_version == '2.1.0'  # Alphabetically last
    
    def test_collect_ticket_details(self):
        """Test ticket detail collection."""
        # Create mock analysis
        analyses = [
            self.create_mock_analysis('test-project', {
                'DEV': {'version': '1.1.0', 'tickets': ['BWD-123'], 'date': '2024-01-15T10:00:00'},
            })
        ]
        
        # Collect details
        details = self.generator._collect_ticket_details(analyses)
        
        # Verify we get one detail for BWD-123 in DEV
        assert len(details) == 1
        
        detail = details[0]
        assert isinstance(detail, JiraTicketDetail)
        assert detail.ticket_id == 'BWD-123'
        assert detail.project == 'test-project'
        assert detail.environment == 'DEV'
        assert detail.version == '1.1.0'
        assert detail.commit_date == '2024-01-15'  # Just date part
        assert 'BWD-123: Test commit message' in detail.commit_message
    
    def test_empty_analyses_list(self):
        """Test handling of empty analyses list."""
        # Generate reports with empty list
        csv_file = self.temp_dir / "empty_test.csv"
        self.generator.generate_csv_report([], str(csv_file), "summary")
        
        # Verify file was created but only has headers
        assert csv_file.exists()
        
        with open(csv_file, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 0  # No data rows, only headers