import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from git import Repo, GitCommandError

from git_release_notifier.git_manager import GitManager


class TestGitManager:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.git_manager = GitManager(repos_dir=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('git_release_notifier.git_manager.Repo')
    def test_get_or_update_repo_clone_new(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.clone_from.return_value = mock_repo
        
        repo_url = "https://github.com/test/repo.git"
        project_name = "test-project"
        
        result = self.git_manager.get_or_update_repo(repo_url, project_name)
        
        assert result == mock_repo
        mock_repo_class.clone_from.assert_called_once_with(
            repo_url, 
            Path(self.temp_dir) / project_name
        )
    
    @patch('git_release_notifier.git_manager.Repo')
    def test_get_or_update_repo_update_existing_main(self, mock_repo_class):
        project_name = "test-project"
        repo_path = Path(self.temp_dir) / project_name
        repo_path.mkdir()
        
        mock_repo = Mock()
        mock_origin = Mock()
        mock_main_head = Mock()
        
        mock_repo.remotes.origin = mock_origin
        mock_repo.heads.main = mock_main_head
        mock_repo_class.return_value = mock_repo
        
        repo_url = "https://github.com/test/repo.git"
        
        result = self.git_manager.get_or_update_repo(repo_url, project_name)
        
        assert result == mock_repo
        mock_origin.fetch.assert_called_once()
        mock_main_head.checkout.assert_called_once()
        mock_main_head.reset.assert_called_once_with('origin/main', index=True, working_tree=True)
    
    @patch('git_release_notifier.git_manager.Repo')
    def test_get_or_update_repo_update_existing_master(self, mock_repo_class):
        project_name = "test-project"
        repo_path = Path(self.temp_dir) / project_name
        repo_path.mkdir()
        
        mock_repo = Mock()
        mock_origin = Mock()
        mock_master_head = Mock()
        
        mock_repo.remotes.origin = mock_origin
        # Mock main branch to raise exception on checkout, then on reset
        mock_main_head = Mock()
        mock_main_head.checkout.side_effect = Exception("No main branch")
        mock_repo.heads.main = mock_main_head
        mock_repo.heads.master = mock_master_head
        mock_repo_class.return_value = mock_repo
        
        repo_url = "https://github.com/test/repo.git"
        
        result = self.git_manager.get_or_update_repo(repo_url, project_name)
        
        assert result == mock_repo
        mock_origin.fetch.assert_called_once()
        mock_master_head.checkout.assert_called_once()
        mock_master_head.reset.assert_called_once_with('origin/master', index=True, working_tree=True)
    
    @patch('git_release_notifier.git_manager.Repo')
    def test_get_or_update_repo_git_error(self, mock_repo_class):
        mock_repo_class.clone_from.side_effect = GitCommandError("git clone", 1)
        
        repo_url = "https://github.com/test/repo.git"
        project_name = "test-project"
        
        result = self.git_manager.get_or_update_repo(repo_url, project_name)
        
        assert result is None
    
    def test_get_commits_between_success(self):
        mock_repo = Mock()
        mock_commit1 = Mock()
        mock_commit1.hexsha = "abc123def456"
        mock_commit1.message = "First commit\n"
        mock_commit1.summary = "First commit"
        mock_commit1.author = "John Doe"
        mock_commit1.committed_datetime.isoformat.return_value = "2023-01-01T12:00:00"
        
        mock_commit2 = Mock()
        mock_commit2.hexsha = "def456ghi789"
        mock_commit2.message = "Second commit\n"
        mock_commit2.summary = "Second commit"
        mock_commit2.author = "Jane Smith"
        mock_commit2.committed_datetime.isoformat.return_value = "2023-01-02T12:00:00"
        
        mock_repo.iter_commits.return_value = [mock_commit1, mock_commit2]
        
        result = self.git_manager.get_commits_between(mock_repo, "from_commit", "to_commit")
        
        assert len(result) == 2
        assert result[0]['id'] == "abc123def456"
        assert result[0]['short_id'] == "abc123de"
        assert result[0]['message'] == "First commit"
        assert result[0]['summary'] == "First commit"
        assert result[0]['author'] == "John Doe"
        assert result[0]['date'] == "2023-01-01T12:00:00"
        
        mock_repo.iter_commits.assert_called_once_with("from_commit..to_commit")
    
    def test_get_commits_between_git_error(self):
        mock_repo = Mock()
        mock_repo.iter_commits.side_effect = GitCommandError("git log", 1)
        
        result = self.git_manager.get_commits_between(mock_repo, "from_commit", "to_commit")
        
        assert result == []
    
    def test_commit_exists_true(self):
        mock_repo = Mock()
        mock_commit = Mock()
        mock_repo.commit.return_value = mock_commit
        
        result = self.git_manager.commit_exists(mock_repo, "abc123")
        
        assert result is True
        mock_repo.commit.assert_called_once_with("abc123")
    
    def test_commit_exists_false(self):
        mock_repo = Mock()
        mock_repo.commit.side_effect = Exception("Commit not found")
        
        result = self.git_manager.commit_exists(mock_repo, "abc123")
        
        assert result is False
    
    def test_cleanup_repos(self):
        # Create some test directories
        test_repo_dir = Path(self.temp_dir) / "test-repo"
        test_repo_dir.mkdir()
        
        # Verify directory exists
        assert test_repo_dir.exists()
        
        # Cleanup
        self.git_manager.cleanup_repos()
        
        # Verify directory is recreated empty
        repos_dir = Path(self.temp_dir)
        assert repos_dir.exists()
        assert list(repos_dir.iterdir()) == []
    
    def test_repos_dir_creation(self):
        # Test with non-existent directory
        new_temp_dir = Path(tempfile.mkdtemp())
        
        non_existent_repos_dir = new_temp_dir / "new_repos"
        git_manager = GitManager(repos_dir=str(non_existent_repos_dir))
        
        assert non_existent_repos_dir.exists()
        
        # Cleanup
        shutil.rmtree(new_temp_dir)
    
    @patch('git_release_notifier.git_manager.Repo')
    def test_get_or_update_repo_unexpected_error(self, mock_repo_class):
        mock_repo_class.clone_from.side_effect = Exception("Unexpected error")
        
        repo_url = "https://github.com/test/repo.git"
        project_name = "test-project"
        
        result = self.git_manager.get_or_update_repo(repo_url, project_name)
        
        assert result is None
    
    def test_get_commits_between_unexpected_error(self):
        mock_repo = Mock()
        mock_repo.iter_commits.side_effect = Exception("Unexpected error")
        
        result = self.git_manager.get_commits_between(mock_repo, "from_commit", "to_commit")
        
        assert result == []
    
    def test_resolve_commit_reference_with_commit_id(self):
        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.hexsha = "abc123def456"
        mock_repo.commit.return_value = mock_commit
        
        result = self.git_manager.resolve_commit_reference(mock_repo, "abc123")
        
        assert result == "abc123def456"
        mock_repo.commit.assert_called_once_with("abc123")
    
    def test_resolve_commit_reference_with_tag(self):
        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.hexsha = "tag123abc456"
        mock_repo.commit.return_value = mock_commit
        
        result = self.git_manager.resolve_commit_reference(mock_repo, "v1.2.0")
        
        assert result == "tag123abc456"
        mock_repo.commit.assert_called_once_with("v1.2.0")
    
    def test_resolve_commit_reference_invalid_reference(self):
        mock_repo = Mock()
        mock_repo.commit.side_effect = Exception("Invalid reference")
        
        result = self.git_manager.resolve_commit_reference(mock_repo, "invalid-ref")
        
        assert result is None
        mock_repo.commit.assert_called_once_with("invalid-ref")
    
    def test_tag_exists_true(self):
        mock_repo = Mock()
        mock_tag1 = Mock()
        mock_tag1.name = "v1.0.0"
        mock_tag2 = Mock()
        mock_tag2.name = "v2.0.0"
        mock_repo.tags = [mock_tag1, mock_tag2]
        
        result = self.git_manager.tag_exists(mock_repo, "v1.0.0")
        
        assert result is True
    
    def test_tag_exists_false(self):
        mock_repo = Mock()
        mock_tag1 = Mock()
        mock_tag1.name = "v1.0.0"
        mock_repo.tags = [mock_tag1]
        
        result = self.git_manager.tag_exists(mock_repo, "v2.0.0")
        
        assert result is False
    
    def test_tag_exists_exception(self):
        mock_repo = Mock()
        mock_repo.tags = Mock(side_effect=Exception("Git error"))
        
        result = self.git_manager.tag_exists(mock_repo, "v1.0.0")
        
        assert result is False