import logging
import re
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path

from .config import ProjectConfig
from .git_manager import GitManager


@dataclass
class VersionInfo:
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def bump_major(self) -> 'VersionInfo':
        return VersionInfo(self.major + 1, 0, 0)
    
    def bump_minor(self) -> 'VersionInfo':
        return VersionInfo(self.major, self.minor + 1, 0)
    
    def bump_patch(self) -> 'VersionInfo':
        return VersionInfo(self.major, self.minor, self.patch + 1)


@dataclass
class ReleaseInfo:
    project_name: str
    jira_ticket: str
    release_branch: str
    current_branch: str
    new_version: VersionInfo
    commits_count: int
    changes_since_last_tag: bool


class ReleaseManager:
    """Manages git release operations."""
    
    def __init__(self):
        self.git_manager = GitManager()
        self.logger = logging.getLogger(__name__)
    
    def validate_jira_ticket(self, ticket: str) -> bool:
        """Validate JIRA ticket format (e.g., BWD-123)."""
        pattern = r'^[A-Z]{1,10}-\d+$'
        return bool(re.match(pattern, ticket))
    
    def get_all_tags(self, repo_path: Path) -> List[str]:
        """Get all tags from repository."""
        try:
            result = subprocess.run(
                ['git', 'tag', '-l'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            tags = [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
            return tags
        except subprocess.CalledProcessError:
            return []
    
    def parse_version(self, version_str: str) -> Optional[VersionInfo]:
        """Parse version string into VersionInfo."""
        pattern = r'^(\d+)\.(\d+)\.(\d+)$'
        match = re.match(pattern, version_str)
        if match:
            return VersionInfo(
                major=int(match.group(1)),
                minor=int(match.group(2)),
                patch=int(match.group(3))
            )
        return None
    
    def get_latest_version(self, repo_path: Path) -> Optional[VersionInfo]:
        """Get the latest version from repository tags."""
        tags = self.get_all_tags(repo_path)
        versions = []
        
        for tag in tags:
            version = self.parse_version(tag)
            if version:
                versions.append(version)
        
        if not versions:
            return None
        
        # Sort by major, minor, patch and return the latest
        versions.sort(key=lambda v: (v.major, v.minor, v.patch), reverse=True)
        return versions[0]
    
    def get_highest_major_version(self, repo_path: Path) -> int:
        """Get the highest major version from repository tags."""
        tags = self.get_all_tags(repo_path)
        major_versions = []
        
        for tag in tags:
            version = self.parse_version(tag)
            if version:
                major_versions.append(version.major)
        
        return max(major_versions) if major_versions else 0
    
    def branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        """Check if branch exists locally or remotely."""
        try:
            # Check local branches
            result = subprocess.run(
                ['git', 'branch', '--list', branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                return True
            
            # Check remote branches
            result = subprocess.run(
                ['git', 'branch', '-r', '--list', f'origin/{branch_name}'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            return bool(result.stdout.strip())
            
        except subprocess.CalledProcessError:
            return False
    
    def get_commits_since_last_tag(self, repo_path: Path) -> int:
        """Get number of commits since last tag."""
        try:
            # Get the latest tag
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            last_tag = result.stdout.strip()
            
            # Count commits since that tag
            result = subprocess.run(
                ['git', 'rev-list', f'{last_tag}..HEAD', '--count'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return int(result.stdout.strip())
            
        except subprocess.CalledProcessError:
            # No tags exist, count all commits
            try:
                result = subprocess.run(
                    ['git', 'rev-list', 'HEAD', '--count'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return int(result.stdout.strip())
            except subprocess.CalledProcessError:
                return 0
    
    def checkout_branch(self, repo_path: Path, branch_name: str, create: bool = False) -> bool:
        """Checkout to branch, optionally creating it."""
        try:
            if create:
                subprocess.run(
                    ['git', 'checkout', '-b', branch_name],
                    cwd=repo_path,
                    check=True,
                    capture_output=True
                )
            else:
                subprocess.run(
                    ['git', 'checkout', branch_name],
                    cwd=repo_path,
                    check=True,
                    capture_output=True
                )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False
    
    def create_annotated_tag(self, repo_path: Path, tag_name: str, message: str) -> bool:
        """Create an annotated tag."""
        try:
            subprocess.run(
                ['git', 'tag', '-a', tag_name, '-m', message],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create tag {tag_name}: {e}")
            return False
    
    def prepare_release(self, project: ProjectConfig, jira_ticket: str) -> Optional[ReleaseInfo]:
        """Prepare release for a project."""
        if not self.validate_jira_ticket(jira_ticket):
            self.logger.error(f"Invalid JIRA ticket format: {jira_ticket}")
            return None
        
        # Get or update repository
        repo = self.git_manager.get_or_update_repo(project.repoUrl, project.name)
        if not repo:
            self.logger.error(f"Failed to access repository for {project.name}")
            return None
        
        repo_path = Path(repo.working_dir)
        release_branch = f"release/{jira_ticket}"
        
        # Ensure we're on the main branch first
        if not self.checkout_branch(repo_path, project.main_branch):
            self.logger.error(f"Failed to checkout main branch {project.main_branch}")
            return None
        
        # Check if release branch already exists
        if self.branch_exists(repo_path, release_branch):
            self.logger.info(f"Release branch {release_branch} already exists, checking out...")
            if not self.checkout_branch(repo_path, release_branch):
                return None
            
            # Bump minor version
            latest_version = self.get_latest_version(repo_path)
            if latest_version:
                new_version = latest_version.bump_minor()
            else:
                highest_major = self.get_highest_major_version(repo_path)
                new_version = VersionInfo(highest_major + 1 if highest_major > 0 else 1, 0, 0)
        else:
            # Create new release branch from main
            self.logger.info(f"Creating new release branch {release_branch}")
            if not self.checkout_branch(repo_path, release_branch, create=True):
                return None
            
            # Set major version as highest + 1, minor and patch as 0
            highest_major = self.get_highest_major_version(repo_path)
            new_version = VersionInfo(highest_major + 1 if highest_major > 0 else 1, 0, 0)
        
        # Check if there are changes since last tag
        commits_count = self.get_commits_since_last_tag(repo_path)
        changes_since_last_tag = commits_count > 0
        
        if not changes_since_last_tag:
            self.logger.info(f"No changes since last tag for {project.name}, skipping...")
            return None
        
        return ReleaseInfo(
            project_name=project.name,
            jira_ticket=jira_ticket,
            release_branch=release_branch,
            current_branch=release_branch,
            new_version=new_version,
            commits_count=commits_count,
            changes_since_last_tag=changes_since_last_tag
        )
    
    def push_branch(self, repo_path: Path, branch_name: str) -> bool:
        """Push branch to remote repository."""
        try:
            subprocess.run(
                ['git', 'push', '-u', 'origin', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to push branch {branch_name}: {e}")
            return False
    
    def push_tag(self, repo_path: Path, tag_name: str) -> bool:
        """Push tag to remote repository."""
        try:
            subprocess.run(
                ['git', 'push', 'origin', tag_name],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to push tag {tag_name}: {e}")
            return False