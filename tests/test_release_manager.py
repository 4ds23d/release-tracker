import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from release_trucker.release_manager import ReleaseManager, VersionInfo
from release_trucker.config import ProjectConfig


class TestVersionInfo:
    
    def test_version_string_representation(self):
        version = VersionInfo(1, 2, 3)
        assert str(version) == "1.2.3"
    
    def test_version_format_support(self):
        version = VersionInfo(1, 2, 3)
        # Test f-string formatting
        assert f"{version}" == "1.2.3"
        assert f"Version: {version}" == "Version: 1.2.3"
        # Test format() function
        assert format(version) == "1.2.3"
    
    def test_bump_major(self):
        version = VersionInfo(1, 2, 3)
        new_version = version.bump_major()
        assert new_version.major == 2
        assert new_version.minor == 0
        assert new_version.patch == 0
    
    def test_bump_minor(self):
        version = VersionInfo(1, 2, 3)
        new_version = version.bump_minor()
        assert new_version.major == 1
        assert new_version.minor == 3
        assert new_version.patch == 0
    
    def test_bump_patch(self):
        version = VersionInfo(1, 2, 3)
        new_version = version.bump_patch()
        assert new_version.major == 1
        assert new_version.minor == 2
        assert new_version.patch == 4


class TestReleaseManager:
    
    def setup_method(self):
        self.release_manager = ReleaseManager()
    
    def test_validate_jira_ticket_valid(self):
        valid_tickets = ["BWD-123", "AUTH-456", "FEAT-1", "PROJECT-9999"]
        for ticket in valid_tickets:
            assert self.release_manager.validate_jira_ticket(ticket)
    
    def test_validate_jira_ticket_invalid(self):
        invalid_tickets = ["bwd-123", "BWD123", "BWD-", "-123", "BWD-ABC", ""]
        for ticket in invalid_tickets:
            assert not self.release_manager.validate_jira_ticket(ticket)
    
    def test_parse_version_valid(self):
        version = self.release_manager.parse_version("1.2.3")
        assert version is not None
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
    
    def test_parse_version_invalid(self):
        invalid_versions = ["1.2", "1.2.3.4", "v1.2.3", "1.2.3-SNAPSHOT", ""]
        for version_str in invalid_versions:
            assert self.release_manager.parse_version(version_str) is None
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_all_tags_success(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock tag objects
        mock_tag1 = Mock()
        mock_tag1.name = "1.0.0"
        mock_tag2 = Mock()
        mock_tag2.name = "1.1.0"
        mock_tag3 = Mock()
        mock_tag3.name = "2.0.0"
        
        mock_repo.tags = [mock_tag1, mock_tag2, mock_tag3]
        
        tags = self.release_manager.get_all_tags(Path("/fake/path"))
        
        assert tags == ["1.0.0", "1.1.0", "2.0.0"]
        mock_repo_class.assert_called_once_with(Path("/fake/path"))
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_all_tags_no_tags(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.tags = []
        
        tags = self.release_manager.get_all_tags(Path("/fake/path"))
        
        assert tags == []
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_all_tags_git_error(self, mock_repo_class):
        from git import GitCommandError
        mock_repo_class.side_effect = GitCommandError("Failed to access repository")
        
        tags = self.release_manager.get_all_tags(Path("/fake/path"))
        
        assert tags == []
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_latest_version(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock tags with valid semantic versioning
        mock_tag1 = Mock()
        mock_tag1.name = "1.0.0"
        mock_tag2 = Mock()
        mock_tag2.name = "2.1.0"
        mock_tag3 = Mock()
        mock_tag3.name = "1.5.0"
        mock_tag4 = Mock()
        mock_tag4.name = "2.0.0"
        
        mock_repo.tags = [mock_tag1, mock_tag2, mock_tag3, mock_tag4]
        
        latest = self.release_manager.get_latest_version(Path("/fake/path"))
        
        assert latest is not None
        assert str(latest) == "2.1.0"
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_latest_version_no_valid_tags(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock tags with invalid semantic versioning patterns
        mock_tag1 = Mock()
        mock_tag1.name = "invalid"
        mock_tag2 = Mock()
        mock_tag2.name = "v1.0.0"
        mock_tag3 = Mock()
        mock_tag3.name = "1.0.0-SNAPSHOT"
        
        mock_repo.tags = [mock_tag1, mock_tag2, mock_tag3]
        
        latest = self.release_manager.get_latest_version(Path("/fake/path"))
        
        assert latest is None
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_latest_version_mixed_tags(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock tags with mix of valid and invalid semantic versioning patterns
        mock_tag1 = Mock()
        mock_tag1.name = "v1.0.0"  # Invalid (has 'v' prefix)
        mock_tag2 = Mock()
        mock_tag2.name = "2.1.0"   # Valid
        mock_tag3 = Mock()
        mock_tag3.name = "staging-release"  # Invalid
        mock_tag4 = Mock()
        mock_tag4.name = "1.5.0"   # Valid
        
        mock_repo.tags = [mock_tag1, mock_tag2, mock_tag3, mock_tag4]
        
        latest = self.release_manager.get_latest_version(Path("/fake/path"))
        
        # Should return the highest valid semantic version (2.1.0)
        assert latest is not None
        assert str(latest) == "2.1.0"
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_highest_major_version(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock tags with valid semantic versioning
        mock_tag1 = Mock()
        mock_tag1.name = "1.0.0"
        mock_tag2 = Mock()
        mock_tag2.name = "3.1.0"
        mock_tag3 = Mock()
        mock_tag3.name = "2.5.0"
        mock_tag4 = Mock()
        mock_tag4.name = "3.0.0"
        
        mock_repo.tags = [mock_tag1, mock_tag2, mock_tag3, mock_tag4]
        
        highest_major = self.release_manager.get_highest_major_version(Path("/fake/path"))
        
        assert highest_major == 3
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_highest_major_version_no_tags(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.tags = []
        
        highest_major = self.release_manager.get_highest_major_version(Path("/fake/path"))
        
        assert highest_major == 0
    
    @patch('release_trucker.release_manager.Repo')
    def test_branch_exists_local(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock local branch
        mock_head = Mock()
        mock_head.name = "release/BWD-123"
        mock_repo.heads = [mock_head]
        
        exists = self.release_manager.branch_exists(Path("/fake/path"), "release/BWD-123")
        
        assert exists is True
    
    @patch('release_trucker.release_manager.Repo')
    def test_branch_exists_remote(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # No local branches
        mock_repo.heads = []
        
        # Mock remote branch
        mock_remote_ref = Mock()
        mock_remote_ref.name = "origin/release/BWD-123"
        mock_repo.remotes.origin.refs = [mock_remote_ref]
        
        exists = self.release_manager.branch_exists(Path("/fake/path"), "release/BWD-123")
        
        assert exists is True
    
    @patch('release_trucker.release_manager.Repo')
    def test_branch_not_exists(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # No local or remote branches
        mock_repo.heads = []
        mock_repo.remotes.origin.refs = []
        
        exists = self.release_manager.branch_exists(Path("/fake/path"), "release/BWD-123")
        
        assert exists is False
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_commits_since_last_tag_with_tag(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock tag with commit and valid semantic version name
        mock_tag = Mock()
        mock_tag.name = "1.0.0"  # Valid semantic version
        mock_tag.commit.committed_date = 1000
        mock_tag.commit.hexsha = "abc123"
        mock_repo.tags = [mock_tag]
        
        # Mock commits since tag
        mock_commits = [Mock() for _ in range(5)]
        mock_repo.iter_commits.return_value = mock_commits
        
        count = self.release_manager.get_commits_since_last_tag(Path("/fake/path"))
        
        assert count == 5
        mock_repo.iter_commits.assert_called_once_with("abc123..HEAD")
    
    @patch('release_trucker.release_manager.Repo')
    def test_get_commits_since_last_tag_no_tags(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # No tags
        mock_repo.tags = []
        
        # Mock all commits
        mock_commits = [Mock() for _ in range(10)]
        mock_repo.iter_commits.return_value = mock_commits
        
        count = self.release_manager.get_commits_since_last_tag(Path("/fake/path"))
        
        assert count == 10
        mock_repo.iter_commits.assert_called_once_with("HEAD")
    
    @patch('release_trucker.release_manager.Repo')
    def test_checkout_branch_existing(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock existing local branch
        mock_head = Mock()
        mock_head.name = "main"
        mock_heads = Mock()
        mock_heads.__iter__ = Mock(return_value=iter([mock_head]))
        mock_heads.__getitem__ = Mock(return_value=mock_head)
        mock_repo.heads = mock_heads
        
        success = self.release_manager.checkout_branch(Path("/fake/path"), "main")
        
        assert success is True
        mock_head.checkout.assert_called_once()
    
    @patch('release_trucker.release_manager.Repo')
    def test_checkout_branch_create_new(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        # Mock creating new branch
        mock_new_branch = Mock()
        mock_repo.create_head.return_value = mock_new_branch
        
        success = self.release_manager.checkout_branch(Path("/fake/path"), "release/BWD-123", create=True)
        
        assert success is True
        mock_repo.create_head.assert_called_once_with("release/BWD-123")
        mock_new_branch.checkout.assert_called_once()
    
    @patch('release_trucker.release_manager.Repo')
    def test_create_annotated_tag(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        success = self.release_manager.create_annotated_tag(
            Path("/fake/path"), 
            "1.0.0", 
            "Release 1.0.0 for BWD-123"
        )
        
        assert success is True
        mock_repo.create_tag.assert_called_once_with("1.0.0", message="Release 1.0.0 for BWD-123")
    
    @patch.object(ReleaseManager, 'push_branch')
    @patch.object(ReleaseManager, 'push_tag')
    def test_push_operations(self, mock_push_tag, mock_push_branch):
        mock_push_branch.return_value = True
        mock_push_tag.return_value = True
        
        branch_success = self.release_manager.push_branch(Path("/fake/path"), "release/BWD-123")
        tag_success = self.release_manager.push_tag(Path("/fake/path"), "1.0.0")
        
        assert branch_success is True
        assert tag_success is True
    
    @patch('release_trucker.release_manager.Repo')
    def test_push_tag_with_refspec(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_origin = Mock()
        mock_repo.remotes.origin = mock_origin
        
        success = self.release_manager.push_tag(Path("/fake/path"), "1.0.0")
        
        assert success is True
        # Verify the correct refspec is used for tag pushing
        mock_origin.push.assert_called_once_with(refspec='refs/tags/1.0.0:refs/tags/1.0.0')
    
    @patch('release_trucker.release_manager.Repo')
    def test_push_branch_with_tracking(self, mock_repo_class):
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_origin = Mock()
        mock_repo.remotes.origin = mock_origin
        mock_local_branch = Mock()
        mock_remote_branch = Mock()
        mock_repo.heads.__getitem__ = Mock(return_value=mock_local_branch)
        mock_origin.refs.__getitem__ = Mock(return_value=mock_remote_branch)
        
        success = self.release_manager.push_branch(Path("/fake/path"), "release/BWD-123")
        
        assert success is True
        # Verify the correct refspec is used for branch pushing
        mock_origin.push.assert_called_once_with(refspec='release/BWD-123:release/BWD-123')
        # Verify tracking is set up
        mock_local_branch.set_tracking_branch.assert_called_once_with(mock_remote_branch)
    
    @patch.object(ReleaseManager, 'validate_jira_ticket')
    @patch.object(ReleaseManager, 'checkout_branch')
    @patch.object(ReleaseManager, 'branch_exists')
    @patch.object(ReleaseManager, 'get_highest_major_version')
    @patch.object(ReleaseManager, 'get_commits_since_last_tag')
    def test_prepare_release_new_branch(self, mock_commits, mock_highest_major, 
                                       mock_branch_exists, mock_checkout, mock_validate):
        # Setup mocks
        mock_validate.return_value = True
        mock_branch_exists.return_value = False
        mock_checkout.return_value = True
        mock_highest_major.return_value = 2
        mock_commits.return_value = 5
        
        # Mock git manager
        mock_repo = Mock()
        mock_repo.working_dir = "/fake/repo"
        self.release_manager.git_manager.get_or_update_repo = Mock(return_value=mock_repo)
        
        # Create project config
        project = ProjectConfig(
            name="test-project",
            repoUrl="https://github.com/test/repo.git",
            env={"PROD": "https://prod.example.com"},
            main_branch="main"
        )
        
        # Test prepare_release
        release_info = self.release_manager.prepare_release(project, "BWD-123")
        
        assert release_info is not None
        assert release_info.project_name == "test-project"
        assert release_info.jira_ticket == "BWD-123"
        assert release_info.release_branch == "release/BWD-123"
        assert str(release_info.new_version) == "3.0.0"  # highest_major + 1
        assert release_info.commits_count == 5
        assert release_info.changes_since_last_tag is True