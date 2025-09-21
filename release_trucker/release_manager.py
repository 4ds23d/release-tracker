import logging
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path
from git import Repo, GitCommandError

from .config import ProjectConfig
from .git_manager import GitManager


@dataclass
class VersionInfo:
    major: int
    minor: int
    patch: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __format__(self, format_spec: str) -> str:
        """Support for f-string formatting."""
        return str(self).__format__(format_spec)
    
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
            repo = Repo(repo_path)
            tags = [tag.name for tag in repo.tags]
            return tags
        except (GitCommandError, Exception) as e:
            self.logger.debug(f"Failed to get tags from {repo_path}: {e}")
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
        """Get the latest version from repository tags that match semantic versioning pattern."""
        try:
            repo = Repo(repo_path)
            versions = []
            
            # Filter tags to only include those matching semantic versioning pattern
            for tag in repo.tags:
                version = self.parse_version(tag.name)
                if version:  # Only include tags that match major.minor.patch pattern
                    versions.append(version)
            
            if not versions:
                return None
            
            # Sort by major, minor, patch and return the latest
            versions.sort(key=lambda v: (v.major, v.minor, v.patch), reverse=True)
            return versions[0]
            
        except (GitCommandError, Exception) as e:
            self.logger.debug(f"Failed to get latest version from {repo_path}: {e}")
            return None
    
    def get_highest_major_version(self, repo_path: Path) -> int:
        """Get the highest major version from repository tags that match semantic versioning pattern."""
        try:
            repo = Repo(repo_path)
            major_versions = []
            
            # Filter tags to only include those matching semantic versioning pattern
            for tag in repo.tags:
                version = self.parse_version(tag.name)
                if version:  # Only include tags that match major.minor.patch pattern
                    major_versions.append(version.major)
            
            return max(major_versions) if major_versions else 0
            
        except (GitCommandError, Exception) as e:
            self.logger.debug(f"Failed to get highest major version from {repo_path}: {e}")
            return 0
    
    def branch_exists(self, repo_path: Path, branch_name: str) -> bool:
        """Check if branch exists locally or remotely."""
        try:
            repo = Repo(repo_path)
            
            # Check local branches
            for head in repo.heads:
                if head.name == branch_name:
                    return True
            
            # Check remote branches
            try:
                for remote_ref in repo.remotes.origin.refs:
                    if remote_ref.name == f'origin/{branch_name}':
                        return True
            except (AttributeError, GitCommandError):
                # No origin remote or error accessing remote refs
                pass
            
            return False
            
        except (GitCommandError, Exception) as e:
            self.logger.debug(f"Failed to check branch existence for {branch_name}: {e}")
            return False
    
    def get_commits_since_last_tag(self, repo_path: Path, reference: str = "HEAD") -> int:
        """Get number of commits since last semantic versioning tag.
        
        Args:
            repo_path: Path to the repository
            reference: Git reference to count commits from (default: HEAD)
                      Use 'origin/main' or 'origin/master' to count from remote branch
        """
        try:
            repo = Repo(repo_path)
            
            # Get the latest semantic versioning tag by commit date
            latest_semantic_tag = None
            latest_tag_commit = None
            
            if repo.tags:
                # Filter to only semantic versioning tags and sort by commit date
                semantic_tags = []
                for tag in repo.tags:
                    if self.parse_version(tag.name):  # Only include tags that match major.minor.patch pattern
                        semantic_tags.append(tag)
                
                if semantic_tags:
                    sorted_tags = sorted(semantic_tags, key=lambda t: t.commit.committed_date, reverse=True)
                    latest_semantic_tag = sorted_tags[0]
                    latest_tag_commit = latest_semantic_tag.commit
            
            if latest_tag_commit:
                # Count commits since that semantic versioning tag
                commits = list(repo.iter_commits(f'{latest_tag_commit.hexsha}..{reference}'))
                return len(commits)
            else:
                # No semantic versioning tags exist, count all commits
                commits = list(repo.iter_commits(reference))
                return len(commits)
                
        except (GitCommandError, Exception) as e:
            self.logger.debug(f"Failed to count commits since last tag: {e}")
            return 0
    
    def checkout_branch(self, repo_path: Path, branch_name: str, create: bool = False) -> bool:
        """Checkout to branch, optionally creating it."""
        try:
            repo = Repo(repo_path)
            
            if create:
                # Create new branch from current HEAD
                new_branch = repo.create_head(branch_name)
                new_branch.checkout()
            else:
                # Checkout existing branch
                # First check if it's a local branch
                if branch_name in [head.name for head in repo.heads]:
                    repo.heads[branch_name].checkout()
                else:
                    # Try to checkout from remote
                    try:
                        remote_branch = repo.remotes.origin.refs[branch_name]
                        local_branch = repo.create_head(branch_name, remote_branch)
                        local_branch.set_tracking_branch(remote_branch)
                        local_branch.checkout()
                    except (AttributeError, IndexError):
                        self.logger.error(f"Branch {branch_name} not found locally or remotely")
                        return False
            
            return True
        except (GitCommandError, Exception) as e:
            self.logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False
    
    def create_annotated_tag(self, repo_path: Path, tag_name: str, message: str) -> bool:
        """Create an annotated tag."""
        try:
            repo = Repo(repo_path)
            # Create annotated tag at current HEAD
            repo.create_tag(tag_name, message=message)
            return True
        except (GitCommandError, Exception) as e:
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
        
        # Check if there are changes since last tag (use remote main branch for accurate detection)
        remote_main_ref = f"origin/{project.main_branch}"
        commits_count = self.get_commits_since_last_tag(repo_path, remote_main_ref)
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
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            
            # Push branch and set upstream tracking
            origin.push(refspec=f'{branch_name}:{branch_name}')
            
            # Set up tracking
            local_branch = repo.heads[branch_name]
            remote_branch = origin.refs[branch_name]
            local_branch.set_tracking_branch(remote_branch)
            
            return True
        except (GitCommandError, Exception) as e:
            self.logger.error(f"Failed to push branch {branch_name}: {e}")
            return False
    
    def push_tag(self, repo_path: Path, tag_name: str) -> bool:
        """Push tag to remote repository."""
        try:
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            
            # Push the specific tag using refspec
            origin.push(refspec=f'refs/tags/{tag_name}:refs/tags/{tag_name}')
            
            return True
        except (GitCommandError, Exception) as e:
            self.logger.error(f"Failed to push tag {tag_name}: {e}")
            return False