import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner

from release_trucker.cli import cli


class TestCLI:
    
    def setup_method(self):
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_config(self, config_data):
        config_file = self.temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        return str(config_file)
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_analyze_command_success(self, mock_report_gen_class, mock_analyzer_class):
        # Setup mocks
        mock_analyzer = Mock()
        mock_report_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_report_gen_class.return_value = mock_report_gen
        
        # Create mock analysis result
        mock_analysis = Mock()
        mock_analysis.project_name = 'test-project'
        mock_analyzer.analyze_project.return_value = mock_analysis
        
        # Create test config
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        output_file = str(self.temp_dir / "test_report.html")
        
        # Run CLI
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file,
            '--output', output_file
        ])
        
        # Verify success
        assert result.exit_code == 0
        assert 'Reports generated successfully' in result.output
        assert 'Analyzed 1 projects' in result.output
        
        # Verify mocks were called
        mock_analyzer.analyze_project.assert_called_once()
        mock_report_gen.generate_report.assert_called_once()
    
    def test_analyze_config_not_found(self):
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', 'nonexistent.yaml'
        ])
        
        assert result.exit_code != 0
        assert 'Configuration file not found' in result.output
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    def test_analyze_no_successful_analyses(self, mock_analyzer_class):
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_project.return_value = None  # All analyses fail
        
        config_data = {
            'projects': [
                {
                    'name': 'failing-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file
        ])
        
        assert result.exit_code != 0
        assert 'No projects could be analyzed successfully' in result.output
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_analyze_with_verbose_logging(self, mock_report_gen_class, mock_analyzer_class):
        mock_analyzer = Mock()
        mock_report_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_report_gen_class.return_value = mock_report_gen
        
        mock_analysis = Mock()
        mock_analyzer.analyze_project.return_value = mock_analysis
        
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        result = self.runner.invoke(cli, [
            '--verbose',
            'analyze',
            '--config', config_file
        ])
        
        assert result.exit_code == 0
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_analyze_with_cleanup(self, mock_report_gen_class, mock_analyzer_class):
        mock_analyzer = Mock()
        mock_report_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_report_gen_class.return_value = mock_report_gen
        
        mock_analysis = Mock()
        mock_analyzer.analyze_project.return_value = mock_analysis
        
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file,
            '--cleanup'
        ])
        
        assert result.exit_code == 0
        # Verify cleanup was called
        mock_analyzer.git_manager.cleanup_repos.assert_called_once()
    
    def test_analyze_default_config_file(self):
        # Test behavior when default config file doesn't exist
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['analyze'])
            
            assert result.exit_code != 0
            assert 'Configuration file not found' in result.output
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_analyze_multiple_projects(self, mock_report_gen_class, mock_analyzer_class):
        mock_analyzer = Mock()
        mock_report_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_report_gen_class.return_value = mock_report_gen
        
        # Return successful analysis for first project, failed for second
        mock_analysis1 = Mock()
        mock_analysis1.project_name = 'project1'
        
        def analyze_side_effect(project):
            if project.name == 'project1':
                return mock_analysis1
            return None
        
        mock_analyzer.analyze_project.side_effect = analyze_side_effect
        
        config_data = {
            'projects': [
                {
                    'name': 'project1',
                    'repoUrl': 'https://github.com/test/repo1.git',
                    'env': {'PROD': 'https://prod1.example.com'}
                },
                {
                    'name': 'project2',
                    'repoUrl': 'https://github.com/test/repo2.git',
                    'env': {'PROD': 'https://prod2.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file
        ])
        
        assert result.exit_code == 0
        assert 'Analyzed 1 projects' in result.output
        
        # Verify both projects were attempted
        assert mock_analyzer.analyze_project.call_count == 2
        # Verify report was generated with 1 successful analysis
        mock_report_gen.generate_report.assert_called_once()
        args = mock_report_gen.generate_report.call_args[0]
        assert len(args[0]) == 1  # Only one successful analysis
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_analyze_report_generation_error(self, mock_report_gen_class, mock_analyzer_class):
        mock_analyzer = Mock()
        mock_report_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_report_gen_class.return_value = mock_report_gen
        
        mock_analysis = Mock()
        mock_analyzer.analyze_project.return_value = mock_analysis
        mock_report_gen.generate_report.side_effect = Exception("Report generation failed")
        
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file
        ])
        
        assert result.exit_code != 0
        assert 'Report generation failed' in result.output
    
    def test_help_message(self):
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Git Release Tracker' in result.output
        assert 'analyze' in result.output
        assert 'release' in result.output
    
    @patch('release_trucker.cli.setup_logging')
    def test_logging_setup_verbose(self, mock_setup_logging):
        # Test that verbose flag affects logging setup
        config_data = {'projects': []}
        config_file = self.create_test_config(config_data)
        
        # This will fail due to no projects, but we're testing logging setup
        self.runner.invoke(cli, [
            '--verbose',
            'analyze',
            '--config', config_file
        ])
        
        mock_setup_logging.assert_called_once_with(True)
    
    @patch('release_trucker.cli.setup_logging')
    def test_logging_setup_normal(self, mock_setup_logging):
        config_data = {'projects': []}
        config_file = self.create_test_config(config_data)
        
        self.runner.invoke(cli, [
            'analyze',
            '--config', config_file
        ])
        
        mock_setup_logging.assert_called_once_with(False)
    
    @patch('release_trucker.cli.ReleaseManager')
    def test_release_command_success(self, mock_release_manager_class):
        mock_release_manager = Mock()
        mock_release_manager_class.return_value = mock_release_manager
        
        # Mock successful release preparation
        mock_release_info = Mock()
        mock_release_info.project_name = 'test-project'
        mock_release_info.release_branch = 'release/BWD-123'
        mock_release_info.new_version = '1.0.0'  # Use string directly instead of Mock
        mock_release_info.commits_count = 5
        mock_release_info.jira_ticket = 'BWD-123'
        
        mock_release_manager.prepare_release.return_value = mock_release_info
        mock_release_manager.git_manager.get_or_update_repo.return_value = Mock(working_dir='/fake/repo')
        mock_release_manager.push_branch.return_value = True
        mock_release_manager.create_annotated_tag.return_value = True
        mock_release_manager.push_tag.return_value = True
        
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Mock user confirmations
        with patch('click.confirm', side_effect=[True, True]):  # Confirm branch and tag push
            result = self.runner.invoke(cli, [
                'release',
                '--config', config_file,
                'BWD-123'
            ])
        
        assert result.exit_code == 0
        assert '🚀 Starting release process for JIRA ticket: BWD-123' in result.output
        assert '✅ Release prepared: release/BWD-123' in result.output
        assert '🏷️  New version: 1.0.0' in result.output
        mock_release_manager.prepare_release.assert_called_once()
    
    def test_release_command_invalid_jira_ticket(self):
        config_data = {'projects': []}
        config_file = self.create_test_config(config_data)
        
        result = self.runner.invoke(cli, [
            'release',
            '--config', config_file,
            'invalid-ticket'
        ])
        
        assert result.exit_code != 0
        assert 'Invalid JIRA ticket format' in result.output
    
    def test_release_command_config_not_found(self):
        result = self.runner.invoke(cli, [
            'release',
            '--config', 'nonexistent.yaml',
            'BWD-123'
        ])
        
        assert result.exit_code != 0
        assert 'Configuration file not found' in result.output
    
    @patch('release_trucker.cli.ReleaseManager')
    def test_release_command_no_releases_prepared(self, mock_release_manager_class):
        mock_release_manager = Mock()
        mock_release_manager_class.return_value = mock_release_manager
        mock_release_manager.prepare_release.return_value = None  # No release prepared
        
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        result = self.runner.invoke(cli, [
            'release',
            '--config', config_file,
            'BWD-123'
        ])
        
        assert result.exit_code == 0
        assert '❌ No releases were prepared' in result.output
    
    @patch('release_trucker.cli.ReleaseManager')
    def test_release_command_push_failures(self, mock_release_manager_class):
        mock_release_manager = Mock()
        mock_release_manager_class.return_value = mock_release_manager
        
        # Mock release info
        mock_release_info = Mock()
        mock_release_info.project_name = 'test-project'
        mock_release_info.release_branch = 'release/BWD-123'
        mock_release_info.new_version = '1.0.0'  # Use string directly instead of Mock
        mock_release_info.commits_count = 5
        mock_release_info.jira_ticket = 'BWD-123'
        
        mock_release_manager.prepare_release.return_value = mock_release_info
        mock_release_manager.git_manager.get_or_update_repo.return_value = Mock(working_dir='/fake/repo')
        mock_release_manager.push_branch.return_value = False  # Push fails
        mock_release_manager.create_annotated_tag.return_value = False  # Tag creation fails
        
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Mock user confirmations
        with patch('click.confirm', return_value=True):
            result = self.runner.invoke(cli, [
                'release',
                '--config', config_file,
                'BWD-123'
            ])
        
        assert result.exit_code == 0
        assert '❌ Failed to push branch' in result.output
        # Tag creation is skipped when branch push fails due to 'continue' statement
        assert '❌ Failed to create tag' not in result.output
    
    @patch('release_trucker.cli.ReleaseManager')
    def test_release_command_tag_creation_failure(self, mock_release_manager_class):
        mock_release_manager = Mock()
        mock_release_manager_class.return_value = mock_release_manager
        
        # Mock release info
        mock_release_info = Mock()
        mock_release_info.project_name = 'test-project'
        mock_release_info.release_branch = 'release/BWD-123'
        mock_release_info.new_version = '1.0.0'
        mock_release_info.commits_count = 5
        mock_release_info.jira_ticket = 'BWD-123'
        
        mock_release_manager.prepare_release.return_value = mock_release_info
        mock_release_manager.git_manager.get_or_update_repo.return_value = Mock(working_dir='/fake/repo')
        mock_release_manager.push_branch.return_value = True  # Push succeeds
        mock_release_manager.create_annotated_tag.return_value = False  # Tag creation fails
        
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Mock user confirmations
        with patch('click.confirm', return_value=True):
            result = self.runner.invoke(cli, [
                'release',
                '--config', config_file,
                'BWD-123'
            ])
        
        assert result.exit_code == 0
        assert '✅ Branch pushed successfully' in result.output
        assert '❌ Failed to create tag' in result.output

    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    @patch('release_trucker.cli.CSVReportGenerator')
    def test_analyze_with_csv_output(self, mock_csv_gen_class, mock_html_gen_class, mock_analyzer_class):
        """Test analyze command with CSV output."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_html_gen = Mock()
        mock_csv_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_html_gen_class.return_value = mock_html_gen
        mock_csv_gen_class.return_value = mock_csv_gen
        
        # Create mock analysis result
        mock_analysis = Mock()
        mock_analysis.project_name = 'test-project'
        mock_analyzer.analyze_project.return_value = mock_analysis
        
        # Mock CSV statistics
        mock_csv_gen.get_ticket_statistics.return_value = {
            'total_tickets': 5,
            'multi_environment_tickets': 2,
            'single_environment_tickets': 3,
            'tickets_by_environment': {'DEV': 3, 'PROD': 2}
        }
        
        # Create test config
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'PROD': 'https://prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        html_file = str(self.temp_dir / "test_report.html")
        csv_file = str(self.temp_dir / "test_tickets.csv")

        # Run CLI with CSV output
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file,
            '--output', html_file,
            '--csv-output', csv_file
        ])

        # Verify success
        assert result.exit_code == 0
        assert 'Reports generated successfully' in result.output
        assert 'HTML:' in result.output
        assert 'CSV (summary):' in result.output
        assert 'Total tickets: 5' in result.output
        assert 'Multi-environment tickets: 2' in result.output

        # Verify both generators were called
        mock_html_gen.generate_report.assert_called_once()
        mock_csv_gen.generate_csv_report.assert_called_once()
        mock_csv_gen.get_ticket_statistics.assert_called_once()

    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.CSVReportGenerator')
    def test_analyze_csv_only(self, mock_csv_gen_class, mock_analyzer_class):
        """Test analyze command with CSV only (no HTML)."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_csv_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_csv_gen_class.return_value = mock_csv_gen
        
        # Create mock analysis result
        mock_analysis = Mock()
        mock_analysis.project_name = 'test-project'
        mock_analyzer.analyze_project.return_value = mock_analysis
        
        # Mock CSV statistics
        mock_csv_gen.get_ticket_statistics.return_value = {
            'total_tickets': 3,
            'multi_environment_tickets': 1,
            'single_environment_tickets': 2,
            'tickets_by_environment': {'DEV': 2, 'TEST': 1}
        }
        
        # Create test config
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'DEV': 'https://dev.example.com', 'TEST': 'https://test.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        csv_file = str(self.temp_dir / "test_tickets.csv")

        # Run CLI with CSV only
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file,
            '--csv-output', csv_file,
            '--csv-only'
        ])

        # Verify success
        assert result.exit_code == 0
        assert 'Reports generated successfully' in result.output
        assert 'CSV (summary):' in result.output
        assert 'HTML:' not in result.output
        assert 'Total tickets: 3' in result.output

        # Verify only CSV generator was called
        mock_csv_gen.generate_csv_report.assert_called_once()
        mock_csv_gen.get_ticket_statistics.assert_called_once()

    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.CSVReportGenerator')
    def test_analyze_csv_detailed_format(self, mock_csv_gen_class, mock_analyzer_class):
        """Test analyze command with detailed CSV format."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_csv_gen = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_csv_gen_class.return_value = mock_csv_gen
        
        # Create mock analysis result
        mock_analysis = Mock()
        mock_analysis.project_name = 'test-project'
        mock_analyzer.analyze_project.return_value = mock_analysis
        
        # Mock CSV statistics
        mock_csv_gen.get_ticket_statistics.return_value = {
            'total_tickets': 2,
            'multi_environment_tickets': 1,
            'single_environment_tickets': 1,
            'tickets_by_environment': {'DEV': 2}
        }
        
        # Create test config
        config_data = {
            'projects': [
                {
                    'name': 'test-project',
                    'repoUrl': 'https://github.com/test/repo.git',
                    'env': {'DEV': 'https://dev.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        csv_file = str(self.temp_dir / "detailed_tickets.csv")

        # Run CLI with detailed CSV format
        result = self.runner.invoke(cli, [
            'analyze',
            '--config', config_file,
            '--csv-output', csv_file,
            '--csv-format', 'detailed',
            '--csv-only'
        ])

        # Verify success
        assert result.exit_code == 0
        assert 'Reports generated successfully' in result.output
        assert 'CSV (detailed):' in result.output

        # Verify CSV generator was called with detailed format
        mock_csv_gen.generate_csv_report.assert_called_once_with(
            [mock_analysis], csv_file, 'detailed'
        )