import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import responses

from git_release_notifier.cli import main
from git_release_notifier.analyzer import ReleaseAnalyzer
from git_release_notifier.config import load_config


@pytest.mark.integration
class TestIntegration:
    
    def setup_method(self):
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_config(self, config_data):
        config_file = self.temp_dir / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        return str(config_file)
    
    @responses.activate
    @patch('git_release_notifier.analyzer.GitManager')
    def test_end_to_end_analysis(self, mock_git_manager_class):
        # Setup test configuration
        config_data = {
            'projects': [
                {
                    'name': 'test-service',
                    'repoUrl': 'https://github.com/test/service.git',
                    'env': {
                        'PROD': 'https://prod-api.example.com',
                        'PRE': 'https://pre-api.example.com',
                        'TEST': 'https://test-api.example.com',
                        'DEV': 'https://dev-api.example.com'
                    }
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Setup API responses
        responses.add(
            responses.GET,
            'https://prod-api.example.com/actuator/info',
            json={'build': {'version': '1.0.0'}, 'git': {'commit': {'id': 'prod123'}}},
            status=200
        )
        responses.add(
            responses.GET,
            'https://pre-api.example.com/actuator/info',
            json={'build': {'version': '1.1.0'}, 'git': {'commit': {'id': 'pre456'}}},
            status=200
        )
        responses.add(
            responses.GET,
            'https://test-api.example.com/actuator/info',
            json={'build': {'version': '1.2.0'}, 'git': {'commit': {'id': 'test789'}}},
            status=200
        )
        responses.add(
            responses.GET,
            'https://dev-api.example.com/actuator/info',
            json={'build': {'version': '1.3.0'}, 'git': {'commit': {'id': 'dev000'}}},
            status=200
        )
        
        # Setup git manager mock
        mock_git_manager = Mock()
        mock_repo = Mock()
        mock_git_manager.get_or_update_repo.return_value = mock_repo
        
        def resolve_commit_side_effect(repo, reference):
            # Return the original reference to maintain test expectations
            return reference
        
        mock_git_manager.resolve_commit_reference.side_effect = resolve_commit_side_effect
        
        def get_commits_side_effect(repo, from_commit, to_commit):
            if from_commit == "prod123" and to_commit == "pre456":
                return [{'id': 'pre456', 'short_id': 'pre456ab', 'message': 'Pre commit', 
                        'summary': 'Pre commit', 'author': 'Author 1', 'date': '2023-01-01T12:00:00'}]
            elif from_commit == "pre456" and to_commit == "test789":
                return [{'id': 'test789', 'short_id': 'test789c', 'message': 'Test commit',
                        'summary': 'Test commit', 'author': 'Author 2', 'date': '2023-01-02T12:00:00'}]
            elif from_commit == "test789" and to_commit == "dev000":
                return [{'id': 'dev000', 'short_id': 'dev000de', 'message': 'Dev commit',
                        'summary': 'Dev commit', 'author': 'Author 3', 'date': '2023-01-03T12:00:00'}]
            return []
        
        mock_git_manager.get_commits_between.side_effect = get_commits_side_effect
        mock_git_manager_class.return_value = mock_git_manager
        
        # Create analyzer and run analysis
        analyzer = ReleaseAnalyzer()
        config = load_config(config_file)
        
        result = analyzer.analyze_project(config.projects[0])
        
        # Verify results
        assert result is not None
        assert result.project_name == 'test-service'
        assert len(result.environments) == 4
        
        # Verify environment data
        assert 'PROD' in result.environments
        assert result.environments['PROD'].version == '1.0.0'
        assert len(result.environments['PROD'].commits) == 0  # PROD is baseline
        
        assert 'PRE' in result.environments
        assert result.environments['PRE'].version == '1.1.0'
        assert len(result.environments['PRE'].commits) == 1
        
        assert 'TEST' in result.environments
        assert len(result.environments['TEST'].commits) == 1
        
        assert 'DEV' in result.environments
        assert len(result.environments['DEV'].commits) == 1
    
    @responses.activate
    @patch('git_release_notifier.analyzer.GitManager')
    def test_partial_environment_failure(self, mock_git_manager_class):
        config_data = {
            'projects': [
                {
                    'name': 'partial-service',
                    'repoUrl': 'https://github.com/test/partial.git',
                    'env': {
                        'PROD': 'https://prod-api.example.com',
                        'DEV': 'https://dev-api-broken.example.com'  # This will fail
                    }
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Setup only PROD response, DEV will fail
        responses.add(
            responses.GET,
            'https://prod-api.example.com/actuator/info',
            json={'build': {'version': '1.0.0'}, 'git': {'commit': {'id': 'prod123'}}},
            status=200
        )
        responses.add(
            responses.GET,
            'https://dev-api-broken.example.com/actuator/info',
            status=500
        )
        
        # Setup git manager mock
        mock_git_manager = Mock()
        mock_repo = Mock()
        mock_git_manager.get_or_update_repo.return_value = mock_repo
        mock_git_manager.commit_exists.return_value = True
        mock_git_manager.get_commits_between.return_value = []
        mock_git_manager_class.return_value = mock_git_manager
        
        analyzer = ReleaseAnalyzer()
        config = load_config(config_file)
        
        result = analyzer.analyze_project(config.projects[0])
        
        # Should still succeed with partial data
        assert result is not None
        assert len(result.environments) == 1  # Only PROD succeeded
        assert 'PROD' in result.environments
        assert 'DEV' not in result.environments
    
    @responses.activate
    def test_complete_failure_no_api_responses(self):
        config_data = {
            'projects': [
                {
                    'name': 'failing-service',
                    'repoUrl': 'https://github.com/test/failing.git',
                    'env': {
                        'PROD': 'https://broken-api.example.com'
                    }
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Setup failing API response
        responses.add(
            responses.GET,
            'https://broken-api.example.com/actuator/info',
            status=404
        )
        
        analyzer = ReleaseAnalyzer()
        config = load_config(config_file)
        
        result = analyzer.analyze_project(config.projects[0])
        
        # Should return None when no environments succeed
        assert result is None
    
    @responses.activate  
    @patch('git_release_notifier.analyzer.GitManager')
    def test_git_repository_failure(self, mock_git_manager_class):
        config_data = {
            'projects': [
                {
                    'name': 'git-fail-service',
                    'repoUrl': 'https://github.com/test/nonexistent.git',
                    'env': {
                        'PROD': 'https://prod-api.example.com'
                    }
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Setup successful API response
        responses.add(
            responses.GET,
            'https://prod-api.example.com/actuator/info',
            json={'build': {'version': '1.0.0'}, 'git': {'commit': {'id': 'prod123'}}},
            status=200
        )
        
        # Setup git manager to fail
        mock_git_manager = Mock()
        mock_git_manager.get_or_update_repo.return_value = None  # Simulate git failure
        mock_git_manager_class.return_value = mock_git_manager
        
        analyzer = ReleaseAnalyzer()
        config = load_config(config_file)
        
        result = analyzer.analyze_project(config.projects[0])
        
        # Should return None when git operations fail
        assert result is None
    
    @responses.activate
    @patch('git_release_notifier.analyzer.GitManager')
    def test_multiple_projects_analysis(self, mock_git_manager_class):
        config_data = {
            'projects': [
                {
                    'name': 'service-1',
                    'repoUrl': 'https://github.com/test/service1.git',
                    'env': {'PROD': 'https://service1-prod.example.com'}
                },
                {
                    'name': 'service-2', 
                    'repoUrl': 'https://github.com/test/service2.git',
                    'env': {'PROD': 'https://service2-prod.example.com'}
                }
            ]
        }
        config_file = self.create_test_config(config_data)
        
        # Setup API responses for both services
        responses.add(
            responses.GET,
            'https://service1-prod.example.com/actuator/info',
            json={'build': {'version': '1.0.0'}, 'git': {'commit': {'id': 'svc1_prod'}}},
            status=200
        )
        responses.add(
            responses.GET,
            'https://service2-prod.example.com/actuator/info',
            json={'build': {'version': '2.0.0'}, 'git': {'commit': {'id': 'svc2_prod'}}},
            status=200
        )
        
        # Setup git manager mock
        mock_git_manager = Mock()
        mock_repo = Mock()
        mock_git_manager.get_or_update_repo.return_value = mock_repo
        mock_git_manager.commit_exists.return_value = True
        mock_git_manager.get_commits_between.return_value = []
        mock_git_manager_class.return_value = mock_git_manager
        
        analyzer = ReleaseAnalyzer()
        config = load_config(config_file)
        
        results = []
        for project in config.projects:
            result = analyzer.analyze_project(project)
            if result:
                results.append(result)
        
        # Both projects should succeed
        assert len(results) == 2
        assert results[0].project_name == 'service-1'
        assert results[1].project_name == 'service-2'
        assert results[0].environments['PROD'].version == '1.0.0'
        assert results[1].environments['PROD'].version == '2.0.0'
    
    def test_config_validation(self):
        # Test valid empty config scenarios
        valid_empty_configs = [
            {},  # Empty config
            {'projects': []},  # No projects
        ]
        
        for empty_config in valid_empty_configs:
            config_file = self.create_test_config(empty_config)
            config = load_config(config_file)
            assert len(config.projects) == 0
        
        # Test invalid project configs (should raise KeyError)
        invalid_project_configs = [
            {'projects': [{'name': 'test'}]},  # Missing required fields
            {'projects': [{'name': 'test', 'repoUrl': 'url'}]}  # Missing env
        ]
        
        for invalid_config in invalid_project_configs:
            config_file = self.create_test_config(invalid_config)
            with pytest.raises(KeyError):
                load_config(config_file)


@pytest.mark.slow
class TestPerformanceIntegration:
    
    @responses.activate
    @patch('git_release_notifier.analyzer.GitManager')
    def test_large_commit_history(self, mock_git_manager_class):
        """Test handling of projects with large commit histories."""
        # Generate large number of mock commits
        large_commit_list = []
        for i in range(100):
            large_commit_list.append({
                'id': f'commit{i:03d}{"a" * 32}',
                'short_id': f'commit{i:03d}',
                'message': f'Commit message {i}',
                'summary': f'Commit {i}',
                'author': f'Author {i % 10}',
                'date': f'2023-01-{(i % 30) + 1:02d}T12:00:00'
            })
        
        mock_git_manager = Mock()
        mock_repo = Mock()
        mock_git_manager.get_or_update_repo.return_value = mock_repo
        mock_git_manager.commit_exists.return_value = True
        mock_git_manager.get_commits_between.return_value = large_commit_list
        mock_git_manager_class.return_value = mock_git_manager
        
        # Setup API response
        responses.add(
            responses.GET,
            'https://large-service.example.com/actuator/info',
            json={'build': {'version': '1.0.0'}, 'git': {'commit': {'id': 'large_commit'}}},
            status=200
        )
        
        from git_release_notifier.config import ProjectConfig
        project_config = ProjectConfig(
            name='large-service',
            repoUrl='https://github.com/test/large.git',
            env={'DEV': 'https://large-service.example.com'}
        )
        
        analyzer = ReleaseAnalyzer()
        result = analyzer.analyze_project(project_config)
        
        # Should handle large commit list without issues
        assert result is not None
        assert len(result.environments['DEV'].commits) == 100