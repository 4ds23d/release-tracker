import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from git import Repo, GitCommandError

from release_trucker.git_manager import GitManager


class TestGitManager:
    
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.git_manager = GitManager(repos_dir=self.temp_dir)
    
    def teardown_method(self):
        shutil.rmtree(self.temp_dir)
    
    @patch('release_trucker.git_manager.Repo')
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
    
    @patch('release_trucker.git_manager.Repo')
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
    
    @patch('release_trucker.git_manager.Repo')
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
    
    @patch('release_trucker.git_manager.Repo')
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
    
    @patch('release_trucker.git_manager.Repo')
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

    def test_get_commits_between_with_merge_expansion_disabled(self):
        """Test get_commits_between with merge expansion disabled"""
        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.hexsha = "abc123def456"
        mock_commit.message = "Merge pull request #123"
        mock_commit.summary = "Merge pull request #123"
        mock_commit.author = "GitHub"
        mock_commit.committed_datetime.isoformat.return_value = "2023-01-01T12:00:00"
        
        mock_repo.iter_commits.return_value = [mock_commit]
        
        result = self.git_manager.get_commits_between(mock_repo, "from_commit", "to_commit", expand_merges=False)
        
        assert len(result) == 1
        assert result[0]['id'] == "abc123def456"
        assert result[0]['message'] == "Merge pull request #123"
        # Should not call _expand_merge_commits
        assert 'is_merged_commit' not in result[0]

    def test_expand_merge_commits_simple_merge(self):
        """Test expansion of a simple merge commit"""
        mock_repo = Mock()
        
        # Mock merge commit
        merge_commit = Mock()
        merge_commit.hexsha = "merge123"
        merge_commit.summary = "Merge pull request #123"
        merge_commit.parents = [Mock(), Mock()]  # Two parents = merge commit
        
        # Mock feature commits
        feature_commit1 = Mock()
        feature_commit1.hexsha = "feature1"
        feature_commit1.message = "Add new feature"
        feature_commit1.summary = "Add new feature"
        feature_commit1.author = "Developer"
        feature_commit1.committed_datetime.isoformat.return_value = "2023-01-01T10:00:00"
        
        feature_commit2 = Mock()
        feature_commit2.hexsha = "feature2"
        feature_commit2.message = "Fix feature bug"
        feature_commit2.summary = "Fix feature bug"
        feature_commit2.author = "Developer"
        feature_commit2.committed_datetime.isoformat.return_value = "2023-01-01T11:00:00"
        
        # Setup mocks
        mock_repo.commit.return_value = merge_commit
        mock_repo.iter_commits.return_value = [feature_commit1, feature_commit2]
        
        commits_input = [{
            'id': 'merge123',
            'short_id': 'merge12',
            'message': 'Merge pull request #123',
            'author': 'GitHub',
            'date': '2023-01-01T12:00:00',
            'summary': 'Merge pull request #123'
        }]
        
        result = self.git_manager._expand_merge_commits(mock_repo, commits_input, "baseline123")
        
        # Should have merge commit + 2 feature commits
        assert len(result) >= 3
        
        # Check that feature commits are marked as merged commits
        merged_commits = [c for c in result if c.get('is_merged_commit')]
        assert len(merged_commits) >= 2

    def test_expand_merge_commits_no_merge_commits(self):
        """Test expansion when there are no merge commits"""
        mock_repo = Mock()
        
        # Mock regular commit (single parent)
        regular_commit = Mock()
        regular_commit.hexsha = "regular123"
        regular_commit.parents = [Mock()]  # Single parent = regular commit
        
        mock_repo.commit.return_value = regular_commit
        
        commits_input = [{
            'id': 'regular123',
            'short_id': 'regular1',
            'message': 'Regular commit',
            'author': 'Developer',
            'date': '2023-01-01T12:00:00',
            'summary': 'Regular commit'
        }]
        
        result = self.git_manager._expand_merge_commits(mock_repo, commits_input, "baseline123")
        
        # Should only have the original commit
        assert len(result) == 1
        assert result[0]['id'] == 'regular123'
        assert 'is_merged_commit' not in result[0]

    def test_expand_merge_commits_git_error(self):
        """Test expansion when git operations fail"""
        mock_repo = Mock()
        
        # Mock merge commit
        merge_commit = Mock()
        merge_commit.hexsha = "merge123"
        merge_commit.parents = [Mock(), Mock()]  # Two parents = merge commit
        
        # Setup to fail on iter_commits
        mock_repo.commit.return_value = merge_commit
        mock_repo.iter_commits.side_effect = GitCommandError("git log failed", 1)
        
        commits_input = [{
            'id': 'merge123',
            'short_id': 'merge12',
            'message': 'Merge pull request #123',
            'author': 'GitHub',
            'date': '2023-01-01T12:00:00',
            'summary': 'Merge pull request #123'
        }]
        
        result = self.git_manager._expand_merge_commits(mock_repo, commits_input, "baseline123")
        
        # Should still have original commit even if expansion fails
        assert len(result) == 1
        assert result[0]['id'] == 'merge123'

    def test_expand_merge_commits_duplicate_prevention(self):
        """Test that duplicate commits are prevented during expansion"""
        mock_repo = Mock()
        
        # Mock merge commit
        merge_commit = Mock()
        merge_commit.hexsha = "merge123"
        merge_commit.parents = [Mock(), Mock()]
        
        # Mock feature commit that's already in the original list
        feature_commit = Mock()
        feature_commit.hexsha = "feature1"  # Same as one in commits_input
        feature_commit.message = "Feature commit"
        feature_commit.summary = "Feature commit"
        feature_commit.author = "Developer"
        feature_commit.committed_datetime.isoformat.return_value = "2023-01-01T10:00:00"
        
        mock_repo.commit.return_value = merge_commit
        mock_repo.iter_commits.return_value = [feature_commit]
        
        commits_input = [
            {
                'id': 'merge123',
                'short_id': 'merge12',
                'message': 'Merge pull request #123',
                'author': 'GitHub',
                'date': '2023-01-01T12:00:00',
                'summary': 'Merge pull request #123'
            },
            {
                'id': 'feature1',  # Already in commits
                'short_id': 'feature',
                'message': 'Feature commit',
                'author': 'Developer',
                'date': '2023-01-01T10:00:00',
                'summary': 'Feature commit'
            }
        ]
        
        result = self.git_manager._expand_merge_commits(mock_repo, commits_input, "baseline123")
        
        # Should not duplicate the feature commit
        feature_commits = [c for c in result if c['id'] == 'feature1']
        assert len(feature_commits) == 1