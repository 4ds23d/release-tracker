import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from release_trucker.release_manager import ReleaseManager, VersionInfo
from release_trucker.config import ProjectConfig


class TestVersionInfo:
    
    def test_version_string_representation(self):
        version = VersionInfo(1, 2, 3)
        assert str(version) == "1.2.3"
    
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
    
    @patch('subprocess.run')
    def test_get_all_tags_success(self, mock_run):
        mock_run.return_value.stdout = "1.0.0\n1.1.0\n2.0.0\n"
        mock_run.return_value.returncode = 0
        
        tags = self.release_manager.get_all_tags(Path("/fake/path"))
        
        assert tags == ["1.0.0", "1.1.0", "2.0.0"]
        mock_run.assert_called_once_with(
            ['git', 'tag', '-l'],
            cwd=Path("/fake/path"),
            capture_output=True,
            text=True,
            check=True
        )
    
    @patch('subprocess.run')
    def test_get_all_tags_no_tags(self, mock_run):
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        
        tags = self.release_manager.get_all_tags(Path("/fake/path"))
        
        assert tags == []
    
    @patch('subprocess.run')
    def test_get_all_tags_git_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, ['git', 'tag', '-l'])
        
        tags = self.release_manager.get_all_tags(Path("/fake/path"))
        
        assert tags == []
    
    @patch.object(ReleaseManager, 'get_all_tags')
    def test_get_latest_version(self, mock_get_tags):
        mock_get_tags.return_value = ["1.0.0", "2.1.0", "1.5.0", "2.0.0"]
        
        latest = self.release_manager.get_latest_version(Path("/fake/path"))
        
        assert latest is not None
        assert str(latest) == "2.1.0"
    
    @patch.object(ReleaseManager, 'get_all_tags')
    def test_get_latest_version_no_valid_tags(self, mock_get_tags):
        mock_get_tags.return_value = ["invalid", "v1.0.0", "1.0.0-SNAPSHOT"]
        
        latest = self.release_manager.get_latest_version(Path("/fake/path"))
        
        assert latest is None
    
    @patch.object(ReleaseManager, 'get_all_tags')
    def test_get_highest_major_version(self, mock_get_tags):
        mock_get_tags.return_value = ["1.0.0", "3.1.0", "2.5.0", "3.0.0"]
        
        highest_major = self.release_manager.get_highest_major_version(Path("/fake/path"))
        
        assert highest_major == 3
    
    @patch.object(ReleaseManager, 'get_all_tags')
    def test_get_highest_major_version_no_tags(self, mock_get_tags):
        mock_get_tags.return_value = []
        
        highest_major = self.release_manager.get_highest_major_version(Path("/fake/path"))
        
        assert highest_major == 0
    
    @patch('subprocess.run')
    def test_branch_exists_local(self, mock_run):
        # First call (local branches) returns the branch
        mock_run.return_value.stdout = "  release/BWD-123\n"
        mock_run.return_value.returncode = 0
        
        exists = self.release_manager.branch_exists(Path("/fake/path"), "release/BWD-123")
        
        assert exists is True
    
    @patch('subprocess.run')
    def test_branch_exists_remote(self, mock_run):
        # First call (local branches) returns empty, second call (remote) returns the branch
        mock_run.side_effect = [
            Mock(stdout="", returncode=0),  # Local check
            Mock(stdout="  origin/release/BWD-123\n", returncode=0)  # Remote check
        ]
        
        exists = self.release_manager.branch_exists(Path("/fake/path"), "release/BWD-123")
        
        assert exists is True
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_branch_not_exists(self, mock_run):
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        
        exists = self.release_manager.branch_exists(Path("/fake/path"), "release/BWD-123")
        
        assert exists is False
    
    @patch('subprocess.run')
    def test_get_commits_since_last_tag_with_tag(self, mock_run):
        # First call gets the latest tag
        # Second call counts commits since that tag
        mock_run.side_effect = [
            Mock(stdout="1.0.0\n", returncode=0),
            Mock(stdout="5\n", returncode=0)
        ]
        
        count = self.release_manager.get_commits_since_last_tag(Path("/fake/path"))
        
        assert count == 5
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_get_commits_since_last_tag_no_tags(self, mock_run):
        # First call fails (no tags), second call counts all commits
        mock_run.side_effect = [
            subprocess.CalledProcessError(128, ['git', 'describe']),
            Mock(stdout="10\n", returncode=0)
        ]
        
        count = self.release_manager.get_commits_since_last_tag(Path("/fake/path"))
        
        assert count == 10
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_checkout_branch_existing(self, mock_run):
        mock_run.return_value.returncode = 0
        
        success = self.release_manager.checkout_branch(Path("/fake/path"), "main")
        
        assert success is True
        mock_run.assert_called_once_with(
            ['git', 'checkout', 'main'],
            cwd=Path("/fake/path"),
            check=True,
            capture_output=True
        )
    
    @patch('subprocess.run')
    def test_checkout_branch_create_new(self, mock_run):
        mock_run.return_value.returncode = 0
        
        success = self.release_manager.checkout_branch(Path("/fake/path"), "release/BWD-123", create=True)
        
        assert success is True
        mock_run.assert_called_once_with(
            ['git', 'checkout', '-b', 'release/BWD-123'],
            cwd=Path("/fake/path"),
            check=True,
            capture_output=True
        )
    
    @patch('subprocess.run')
    def test_create_annotated_tag(self, mock_run):
        mock_run.return_value.returncode = 0
        
        success = self.release_manager.create_annotated_tag(
            Path("/fake/path"), 
            "1.0.0", 
            "Release 1.0.0 for BWD-123"
        )
        
        assert success is True
        mock_run.assert_called_once_with(
            ['git', 'tag', '-a', '1.0.0', '-m', 'Release 1.0.0 for BWD-123'],
            cwd=Path("/fake/path"),
            check=True,
            capture_output=True
        )
    
    @patch.object(ReleaseManager, 'push_branch')
    @patch.object(ReleaseManager, 'push_tag')
    def test_push_operations(self, mock_push_tag, mock_push_branch):
        mock_push_branch.return_value = True
        mock_push_tag.return_value = True
        
        branch_success = self.release_manager.push_branch(Path("/fake/path"), "release/BWD-123")
        tag_success = self.release_manager.push_tag(Path("/fake/path"), "1.0.0")
        
        assert branch_success is True
        assert tag_success is True
    
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