import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner

from release_trucker.cli import main


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
    def test_main_success(self, mock_report_gen_class, mock_analyzer_class):
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
        result = self.runner.invoke(main, [
            '--config', config_file,
            '--output', output_file
        ])
        
        # Verify success
        assert result.exit_code == 0
        assert 'Report generated successfully' in result.output
        assert 'Analyzed 1 projects' in result.output
        
        # Verify mocks were called
        mock_analyzer.analyze_project.assert_called_once()
        mock_report_gen.generate_report.assert_called_once()
    
    def test_main_config_not_found(self):
        result = self.runner.invoke(main, [
            '--config', 'nonexistent.yaml'
        ])
        
        assert result.exit_code != 0
        assert 'Configuration file not found' in result.output
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    def test_main_no_successful_analyses(self, mock_analyzer_class):
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
        
        result = self.runner.invoke(main, [
            '--config', config_file
        ])
        
        assert result.exit_code != 0
        assert 'No projects could be analyzed successfully' in result.output
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_main_with_verbose_logging(self, mock_report_gen_class, mock_analyzer_class):
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
        
        result = self.runner.invoke(main, [
            '--config', config_file,
            '--verbose'
        ])
        
        assert result.exit_code == 0
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_main_with_cleanup(self, mock_report_gen_class, mock_analyzer_class):
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
        
        result = self.runner.invoke(main, [
            '--config', config_file,
            '--cleanup'
        ])
        
        assert result.exit_code == 0
        # Verify cleanup was called
        mock_analyzer.git_manager.cleanup_repos.assert_called_once()
    
    def test_main_default_config_file(self):
        # Test behavior when default config file doesn't exist
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(main)
            
            assert result.exit_code != 0
            assert 'Configuration file not found' in result.output
    
    @patch('release_trucker.cli.ReleaseAnalyzer')
    @patch('release_trucker.cli.HTMLReportGenerator')
    def test_main_multiple_projects(self, mock_report_gen_class, mock_analyzer_class):
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
        
        result = self.runner.invoke(main, [
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
    def test_main_report_generation_error(self, mock_report_gen_class, mock_analyzer_class):
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
        
        result = self.runner.invoke(main, [
            '--config', config_file
        ])
        
        assert result.exit_code != 0
        assert 'Report generation failed' in result.output
    
    def test_help_message(self):
        result = self.runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'Git Release Notifier' in result.output
        assert '--config' in result.output
        assert '--output' in result.output
        assert '--verbose' in result.output
        assert '--cleanup' in result.output
    
    @patch('release_trucker.cli.setup_logging')
    def test_logging_setup_verbose(self, mock_setup_logging):
        # Test that verbose flag affects logging setup
        config_data = {'projects': []}
        config_file = self.create_test_config(config_data)
        
        # This will fail due to no projects, but we're testing logging setup
        self.runner.invoke(main, [
            '--config', config_file,
            '--verbose'
        ])
        
        mock_setup_logging.assert_called_once_with(True)
    
    @patch('release_trucker.cli.setup_logging')
    def test_logging_setup_normal(self, mock_setup_logging):
        config_data = {'projects': []}
        config_file = self.create_test_config(config_data)
        
        self.runner.invoke(main, [
            '--config', config_file
        ])
        
        mock_setup_logging.assert_called_once_with(False)