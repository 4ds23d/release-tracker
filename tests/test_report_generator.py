import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from release_trucker.report_generator import HTMLReportGenerator
from release_trucker.analyzer import ProjectAnalysis, EnvironmentCommits


class TestHTMLReportGenerator:
    
    def setup_method(self):
        self.generator = HTMLReportGenerator()
    
    def test_generate_report_success(self):
        # Create mock analysis data
        commits = [
            {
                'id': 'abc123def456',
                'short_id': 'abc123de',
                'message': 'Test commit message',
                'summary': 'Test commit',
                'author': 'John Doe',
                'date': '2023-01-01T12:00:00'
            }
        ]
        
        environments = {
            'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', []),
            'DEV': EnvironmentCommits('DEV', '1.1.0', 'dev456', commits)
        }
        
        analysis = ProjectAnalysis(
            project_name='test-project',
            environments=environments
        )
        
        analyses = [analysis]
        
        # Generate report to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report(analyses, output_file)
            
            # Verify file was created
            output_path = Path(output_file)
            assert output_path.exists()
            
            # Verify content
            content = output_path.read_text(encoding='utf-8')
            assert '<!DOCTYPE html>' in content
            assert 'Release Tracker' in content
            assert 'test-project' in content
            assert '1.0.0' in content
            assert '1.1.0' in content
            assert 'Test commit' in content
            assert 'John Doe' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_generate_report_multiple_projects(self):
        # Create multiple mock projects - one with changes, one up-to-date
        commits = [{'id': 'abc123', 'short_id': 'abc123ab', 'message': 'Test', 'summary': 'Test', 'author': 'Author', 'date': '2023-01-01T12:00:00'}]
        analysis1 = ProjectAnalysis(
            project_name='project1',
            environments={
                'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', []),
                'DEV': EnvironmentCommits('DEV', '1.1.0', 'dev456', commits)
            }
        )
        
        analysis2 = ProjectAnalysis(
            project_name='project2',
            environments={
                'PROD': EnvironmentCommits('PROD', '2.0.0', 'prod456', [])
            }
        )
        
        analyses = [analysis1, analysis2]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report(analyses, output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            assert 'project1' in content
            assert 'project2' in content
            # project1 has changes so versions will be in detailed section
            assert '1.0.0' in content
            assert '1.1.0' in content
            # project2 is up-to-date so should be in up-to-date section
            assert 'Projects Up to Date' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_generate_report_empty_analyses(self):
        analyses = []
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report(analyses, output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            assert '<!DOCTYPE html>' in content
            assert 'Release Tracker' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_generate_report_all_environments(self):
        # Test with all environment types
        commits_dev = [
            {
                'id': 'dev123',
                'short_id': 'dev123ab',
                'message': 'Dev commit',
                'summary': 'Dev commit',
                'author': 'Dev Author',
                'date': '2023-01-01T12:00:00'
            }
        ]
        
        commits_test = [
            {
                'id': 'test456',
                'short_id': 'test456c',
                'message': 'Test commit',
                'summary': 'Test commit',
                'author': 'Test Author',
                'date': '2023-01-02T12:00:00'
            }
        ]
        
        environments = {
            'DEV': EnvironmentCommits('DEV', '1.3.0', 'dev123', commits_dev),
            'TEST': EnvironmentCommits('TEST', '1.2.0', 'test456', commits_test),
            'PRE': EnvironmentCommits('PRE', '1.1.0', 'pre789', []),
            'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod000', [])
        }
        
        analysis = ProjectAnalysis(
            project_name='full-project',
            environments=environments
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report([analysis], output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            
            # Check environment sections exist
            assert 'env-dev' in content
            assert 'env-test' in content
            assert 'env-pre' in content
            assert 'env-prod' in content
            
            # Check versions are displayed
            assert '1.3.0' in content
            assert '1.2.0' in content
            assert '1.1.0' in content
            assert '1.0.0' in content
            
            # Check commit details
            assert 'Dev commit' in content
            assert 'Test commit' in content
            assert 'Dev Author' in content
            assert 'Test Author' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_get_template_returns_valid_template(self):
        template = self.generator._get_template()
        
        # Test that template can render with basic data
        rendered = template.render(
            generated_at='2023-01-01T12:00:00',
            projects_with_changes=[],
            projects_up_to_date=[],
            environment_order=['DEV', 'TEST', 'PRE', 'PROD']
        )
        
        assert '<!DOCTYPE html>' in rendered
        assert 'Release Tracker' in rendered
        assert '2023-01-01T12:00:00' in rendered
    
    def test_template_javascript_functionality(self):
        template = self.generator._get_template()
        rendered = template.render(
            generated_at='2023-01-01T12:00:00',
            projects_with_changes=[],
            projects_up_to_date=[],
            environment_order=['DEV', 'TEST', 'PRE', 'PROD']
        )
        
        # Check that JavaScript functions exist
        assert 'function toggleCommits' in rendered
        assert 'function toggleJiraTickets' in rendered
        assert 'expanded' in rendered
        assert 'rotated' in rendered
    
    def test_template_css_styles(self):
        template = self.generator._get_template()
        rendered = template.render(
            generated_at='2023-01-01T12:00:00',
            projects_with_changes=[],
            projects_up_to_date=[],
            environment_order=['DEV', 'TEST', 'PRE', 'PROD']
        )
        
        # Check that CSS styles exist
        assert '.env-dev' in rendered
        assert '.env-test' in rendered
        assert '.env-pre' in rendered
        assert '.env-prod' in rendered
        assert '.commit-item' in rendered
        assert '.version-commit-badge' in rendered
        assert '.commits-count' in rendered
        assert '.jira-count' in rendered
        # Check new up-to-date styles
        assert '.up-to-date-section' in rendered
        assert '.up-to-date-item' in rendered
        assert '.changes-section' in rendered
        # Check inline no-commits style
        assert '.no-commits-inline' in rendered
    
    @patch('release_trucker.report_generator.Path')
    def test_generate_report_file_write_error(self, mock_path):
        mock_path_instance = Mock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.write_text.side_effect = IOError("Cannot write file")
        
        analysis = ProjectAnalysis(
            project_name='test-project',
            environments={}
        )
        
        with pytest.raises(IOError):
            self.generator.generate_report([analysis], 'test.html')
    
    def test_template_handles_missing_commits(self):
        # Test template with environments that have no commits (up-to-date project)
        environments = {
            'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', []),
            'PRE': EnvironmentCommits('PRE', '1.0.0', 'prod123', [])  # Same as PROD, no new commits
        }
        
        analysis = ProjectAnalysis(
            project_name='no-commits-project',
            environments=environments
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report([analysis], output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            assert 'no-commits-project' in content
            # This project should be in the up-to-date section since it has no changes
            assert 'Projects Up to Date' in content
            assert 'All environments are synchronized with PROD' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_template_commit_formatting(self):
        # Test that commits are properly formatted in the template
        commits = [
            {
                'id': 'abcdef123456',
                'short_id': 'abcdef12',
                'message': 'Multi-line commit message\n\nWith details',
                'summary': 'Multi-line commit message',
                'author': 'John Doe <john@example.com>',
                'date': '2023-01-01T12:00:00+00:00'
            }
        ]
        
        environments = {
            'DEV': EnvironmentCommits('DEV', '1.1.0', 'abcdef123456', commits)
        }
        
        analysis = ProjectAnalysis(
            project_name='format-test',
            environments=environments
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report([analysis], output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            assert 'abcdef12' in content  # Short ID
            assert 'Multi-line commit message' in content  # Summary
            assert 'John Doe <john@example.com>' in content  # Author
            assert '2023-01-01T12:00:00' in content  # Date (truncated to 19 chars)
            
        finally:
            Path(output_file).unlink()
    
    def test_project_has_changes_with_commits(self):
        # Test project with commits in non-PROD environment
        commits = [{'id': 'abc123', 'message': 'Test commit'}]
        environments = {
            'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', []),
            'DEV': EnvironmentCommits('DEV', '1.1.0', 'dev456', commits)
        }
        
        analysis = ProjectAnalysis('test-project', environments)
        assert self.generator._project_has_changes(analysis) is True
    
    def test_project_has_changes_with_jira_tickets(self):
        # Test project with JIRA tickets in non-PROD environment
        environments = {
            'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', [], set()),
            'DEV': EnvironmentCommits('DEV', '1.1.0', 'dev456', [], {'ABC-123'})
        }
        
        analysis = ProjectAnalysis('test-project', environments)
        assert self.generator._project_has_changes(analysis) is True
    
    def test_project_has_changes_no_changes(self):
        # Test project with no changes (up to date)
        environments = {
            'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', [], set()),
            'PRE': EnvironmentCommits('PRE', '1.0.0', 'prod123', [], set()),
            'TEST': EnvironmentCommits('TEST', '1.0.0', 'prod123', [], set()),
            'DEV': EnvironmentCommits('DEV', '1.0.0', 'prod123', [], set())
        }
        
        analysis = ProjectAnalysis('test-project', environments)
        assert self.generator._project_has_changes(analysis) is False
    
    def test_project_has_changes_prod_only(self):
        # Test project with only PROD environment
        environments = {
            'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', [{'id': 'abc'}], {'ABC-123'})
        }
        
        analysis = ProjectAnalysis('test-project', environments)
        assert self.generator._project_has_changes(analysis) is False
    
    def test_generate_report_mixed_projects(self):
        # Test report with both up-to-date and projects with changes
        # Project with changes
        commits = [{'id': 'abc123', 'short_id': 'abc123ab', 'message': 'Test', 'summary': 'Test', 'author': 'Author', 'date': '2023-01-01T12:00:00'}]
        project_with_changes = ProjectAnalysis(
            'project-with-changes',
            {
                'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', []),
                'DEV': EnvironmentCommits('DEV', '1.1.0', 'dev456', commits)
            }
        )
        
        # Project up to date
        project_up_to_date = ProjectAnalysis(
            'project-up-to-date',
            {
                'PROD': EnvironmentCommits('PROD', '2.0.0', 'sync123', []),
                'DEV': EnvironmentCommits('DEV', '2.0.0', 'sync123', [])
            }
        )
        
        analyses = [project_with_changes, project_up_to_date]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report(analyses, output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            
            # Check both sections exist
            assert 'Projects Up to Date' in content
            assert 'Projects with Changes to Deploy' in content
            
            # Check project names appear in correct sections
            assert 'project-with-changes' in content
            assert 'project-up-to-date' in content
            
            # Check up-to-date styling
            assert 'up-to-date-section' in content
            assert 'All environments are synchronized with PROD' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_generate_report_only_up_to_date_projects(self):
        # Test report with only up-to-date projects
        project1 = ProjectAnalysis(
            'sync-project-1',
            {
                'PROD': EnvironmentCommits('PROD', '1.0.0', 'sync123', []),
                'DEV': EnvironmentCommits('DEV', '1.0.0', 'sync123', [])
            }
        )
        
        project2 = ProjectAnalysis(
            'sync-project-2',
            {
                'PROD': EnvironmentCommits('PROD', '2.0.0', 'sync456', []),
                'DEV': EnvironmentCommits('DEV', '2.0.0', 'sync456', [])
            }
        )
        
        analyses = [project1, project2]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report(analyses, output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            
            # Should only have up-to-date section
            assert 'Projects Up to Date' in content
            assert 'Projects with Changes to Deploy' not in content
            assert 'sync-project-1' in content
            assert 'sync-project-2' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_generate_report_only_projects_with_changes(self):
        # Test report with only projects that have changes
        commits = [{'id': 'abc123', 'short_id': 'abc123ab', 'message': 'Test', 'summary': 'Test', 'author': 'Author', 'date': '2023-01-01T12:00:00'}]
        project1 = ProjectAnalysis(
            'changed-project-1',
            {
                'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', []),
                'DEV': EnvironmentCommits('DEV', '1.1.0', 'dev456', commits)
            }
        )
        
        project2 = ProjectAnalysis(
            'changed-project-2',
            {
                'PROD': EnvironmentCommits('PROD', '2.0.0', 'prod789', []),
                'TEST': EnvironmentCommits('TEST', '2.1.0', 'test123', commits)
            }
        )
        
        analyses = [project1, project2]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report(analyses, output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            
            # Should only have changes section
            assert 'Projects with Changes to Deploy' in content
            assert 'Projects Up to Date' not in content
            assert 'changed-project-1' in content
            assert 'changed-project-2' in content
            
        finally:
            Path(output_file).unlink()
    
    def test_inline_no_commits_message(self):
        # Test that "No new commits" appears inline when environment has no commits
        commits = [{'id': 'abc123', 'short_id': 'abc123ab', 'message': 'Test', 'summary': 'Test', 'author': 'Author', 'date': '2023-01-01T12:00:00'}]
        project = ProjectAnalysis(
            'test-project',
            {
                'PROD': EnvironmentCommits('PROD', '1.0.0', 'prod123', []),
                'PRE': EnvironmentCommits('PRE', '1.0.0', 'prod123', []),  # No commits
                'DEV': EnvironmentCommits('DEV', '1.1.0', 'dev456', commits)  # Has commits
            }
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_file = f.name
        
        try:
            self.generator.generate_report([project], output_file)
            
            content = Path(output_file).read_text(encoding='utf-8')
            
            # Check that inline no-commits message appears for PRE environment
            assert 'no-commits-inline' in content
            assert 'No new commits compared to baseline' in content
            
            # The message should be inline, not in a separate div
            assert '<span class="no-commits-inline">No new commits compared to baseline</span>' in content
            
        finally:
            Path(output_file).unlink()