import pytest
from unittest.mock import Mock, patch, MagicMock
from git import Repo

from git_release_notifier.analyzer import ReleaseAnalyzer, ProjectAnalysis, EnvironmentCommits
from git_release_notifier.api_client import VersionInfo
from git_release_notifier.config import ProjectConfig


class TestReleaseAnalyzer:
    
    def setup_method(self):
        self.analyzer = ReleaseAnalyzer()
    
    @patch('git_release_notifier.analyzer.ActuatorClient')
    @patch('git_release_notifier.analyzer.GitManager')
    def test_analyze_project_success(self, mock_git_manager_class, mock_api_client_class):
        # Setup mocks
        mock_api_client = Mock()
        mock_git_manager = Mock()
        mock_api_client_class.return_value = mock_api_client
        mock_git_manager_class.return_value = mock_git_manager
        
        # Setup project config
        project_config = ProjectConfig(
            name="test-project",
            repoUrl="https://github.com/test/repo.git",
            env={
                "PROD": "https://prod.example.com",
                "PRE": "https://pre.example.com",
                "TEST": "https://test.example.com",
                "DEV": "https://dev.example.com"
            }
        )
        
        # Setup version info responses
        version_infos = {
            "PROD": VersionInfo("1.0.0", "prod123", "PROD"),
            "PRE": VersionInfo("1.1.0", "pre456", "PRE"),
            "TEST": VersionInfo("1.2.0", "test789", "TEST"),
            "DEV": VersionInfo("1.3.0", "dev000", "DEV")
        }
        
        def get_version_info_side_effect(url, env):
            return version_infos.get(env)
        
        mock_api_client.get_version_info.side_effect = get_version_info_side_effect
        
        # Setup git manager
        mock_repo = Mock()
        mock_git_manager.get_or_update_repo.return_value = mock_repo
        mock_git_manager.commit_exists.return_value = True
        
        # Setup commit responses
        def get_commits_side_effect(repo, from_commit, to_commit):
            if from_commit == "prod123" and to_commit == "pre456":
                return [{"id": "pre456", "message": "Pre commit"}]
            elif from_commit == "pre456" and to_commit == "test789":
                return [{"id": "test789", "message": "Test commit"}]
            elif from_commit == "test789" and to_commit == "dev000":
                return [{"id": "dev000", "message": "Dev commit"}]
            return []
        
        mock_git_manager.get_commits_between.side_effect = get_commits_side_effect
        
        # Execute
        self.analyzer.api_client = mock_api_client
        self.analyzer.git_manager = mock_git_manager
        
        result = self.analyzer.analyze_project(project_config)
        
        # Verify
        assert result is not None
        assert isinstance(result, ProjectAnalysis)
        assert result.project_name == "test-project"
        assert len(result.environments) == 4
        
        # Check PROD environment (baseline, no commits)
        assert "PROD" in result.environments
        prod_env = result.environments["PROD"]
        assert prod_env.version == "1.0.0"
        assert prod_env.commit_id == "prod123"
        assert len(prod_env.commits) == 0
        
        # Check PRE environment
        assert "PRE" in result.environments
        pre_env = result.environments["PRE"]
        assert pre_env.version == "1.1.0"
        assert len(pre_env.commits) == 1
    
    @patch('git_release_notifier.analyzer.ActuatorClient')
    @patch('git_release_notifier.analyzer.GitManager')
    def test_analyze_project_no_version_info(self, mock_git_manager_class, mock_api_client_class):
        mock_api_client = Mock()
        mock_git_manager = Mock()
        mock_api_client_class.return_value = mock_api_client
        mock_git_manager_class.return_value = mock_git_manager
        
        project_config = ProjectConfig(
            name="test-project",
            repoUrl="https://github.com/test/repo.git",
            env={"PROD": "https://prod.example.com"}
        )
        
        mock_api_client.get_version_info.return_value = None
        
        self.analyzer.api_client = mock_api_client
        self.analyzer.git_manager = mock_git_manager
        
        result = self.analyzer.analyze_project(project_config)
        
        assert result is None
    
    @patch('git_release_notifier.analyzer.ActuatorClient')
    @patch('git_release_notifier.analyzer.GitManager')
    def test_analyze_project_no_repo(self, mock_git_manager_class, mock_api_client_class):
        mock_api_client = Mock()
        mock_git_manager = Mock()
        mock_api_client_class.return_value = mock_api_client
        mock_git_manager_class.return_value = mock_git_manager
        
        project_config = ProjectConfig(
            name="test-project",
            repoUrl="https://github.com/test/repo.git",
            env={"PROD": "https://prod.example.com"}
        )
        
        mock_api_client.get_version_info.return_value = VersionInfo("1.0.0", "abc123", "PROD")
        mock_git_manager.get_or_update_repo.return_value = None
        
        self.analyzer.api_client = mock_api_client
        self.analyzer.git_manager = mock_git_manager
        
        result = self.analyzer.analyze_project(project_config)
        
        assert result is None
    
    @patch('git_release_notifier.analyzer.ActuatorClient')
    @patch('git_release_notifier.analyzer.GitManager')
    def test_analyze_project_commit_not_found(self, mock_git_manager_class, mock_api_client_class):
        mock_api_client = Mock()
        mock_git_manager = Mock()
        mock_api_client_class.return_value = mock_api_client
        mock_git_manager_class.return_value = mock_git_manager
        
        project_config = ProjectConfig(
            name="test-project",
            repoUrl="https://github.com/test/repo.git",
            env={"PROD": "https://prod.example.com"}
        )
        
        mock_api_client.get_version_info.return_value = VersionInfo("1.0.0", "abc123", "PROD")
        mock_repo = Mock()
        mock_git_manager.get_or_update_repo.return_value = mock_repo
        mock_git_manager.commit_exists.return_value = False
        
        self.analyzer.api_client = mock_api_client
        self.analyzer.git_manager = mock_git_manager
        
        result = self.analyzer.analyze_project(project_config)
        
        assert result is None
    
    def test_get_environment_specific_commits_prod_baseline(self):
        mock_repo = Mock()
        version_infos = {
            "PROD": VersionInfo("1.0.0", "prod123", "PROD")
        }
        env_order = ["DEV", "TEST", "PRE", "PROD"]
        
        result = self.analyzer._get_environment_specific_commits(
            mock_repo, "PROD", "prod123", version_infos, env_order
        )
        
        assert result == []
    
    def test_get_environment_specific_commits_pre_vs_prod(self):
        mock_repo = Mock()
        version_infos = {
            "PROD": VersionInfo("1.0.0", "prod123", "PROD"),
            "PRE": VersionInfo("1.1.0", "pre456", "PRE")
        }
        env_order = ["DEV", "TEST", "PRE", "PROD"]
        
        expected_commits = [{"id": "pre456", "message": "Pre commit"}]
        self.analyzer.git_manager = Mock()
        self.analyzer.git_manager.get_commits_between.return_value = expected_commits
        
        result = self.analyzer._get_environment_specific_commits(
            mock_repo, "PRE", "pre456", version_infos, env_order
        )
        
        assert result == expected_commits
        self.analyzer.git_manager.get_commits_between.assert_called_once_with(
            mock_repo, "prod123", "pre456"
        )
    
    def test_get_environment_specific_commits_no_baseline(self):
        mock_repo = Mock()
        version_infos = {
            "DEV": VersionInfo("1.3.0", "dev000", "DEV")
        }
        env_order = ["DEV", "TEST", "PRE", "PROD"]
        
        expected_commits = [{"id": "dev000", "message": "Dev commit"}]
        self.analyzer.git_manager = Mock()
        self.analyzer.git_manager.get_commits_between.return_value = expected_commits
        
        result = self.analyzer._get_environment_specific_commits(
            mock_repo, "DEV", "dev000", version_infos, env_order
        )
        
        assert result == expected_commits
        self.analyzer.git_manager.get_commits_between.assert_called_once_with(
            mock_repo, "HEAD~100", "dev000"
        )
    
    def test_get_environment_specific_commits_invalid_env(self):
        mock_repo = Mock()
        version_infos = {}
        env_order = ["DEV", "TEST", "PRE", "PROD"]
        
        result = self.analyzer._get_environment_specific_commits(
            mock_repo, "INVALID", "commit123", version_infos, env_order
        )
        
        assert result == []


class TestProjectAnalysis:
    
    def test_project_analysis_creation(self):
        environments = {
            "PROD": EnvironmentCommits("PROD", "1.0.0", "prod123", []),
            "DEV": EnvironmentCommits("DEV", "1.1.0", "dev456", [{"id": "dev456"}])
        }
        
        analysis = ProjectAnalysis(
            project_name="test-project",
            environments=environments
        )
        
        assert analysis.project_name == "test-project"
        assert len(analysis.environments) == 2
        assert analysis.environment_order == ["DEV", "TEST", "PRE", "PROD"]
    
    def test_project_analysis_custom_env_order(self):
        environments = {}
        custom_order = ["PROD", "STAGE", "DEV"]
        
        analysis = ProjectAnalysis(
            project_name="test-project",
            environments=environments,
            environment_order=custom_order
        )
        
        assert analysis.environment_order == custom_order


class TestEnvironmentCommits:
    
    def test_environment_commits_creation(self):
        commits = [
            {"id": "abc123", "message": "Test commit"},
            {"id": "def456", "message": "Another commit"}
        ]
        
        env_commits = EnvironmentCommits(
            environment="TEST",
            version="1.2.0",
            commit_id="abc123",
            commits=commits
        )
        
        assert env_commits.environment == "TEST"
        assert env_commits.version == "1.2.0"
        assert env_commits.commit_id == "abc123"
        assert len(env_commits.commits) == 2
        assert env_commits.commits[0]["id"] == "abc123"