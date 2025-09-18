from dataclasses import dataclass
from typing import List, Dict, Optional
from git import Repo
import logging

from .api_client import VersionInfo, ActuatorClient
from .git_manager import GitManager


@dataclass
class EnvironmentCommits:
    environment: str
    version: str
    commit_id: str
    commits: List[dict]


@dataclass
class ProjectAnalysis:
    project_name: str
    environments: Dict[str, EnvironmentCommits]
    environment_order: List[str] = None
    
    def __post_init__(self):
        if self.environment_order is None:
            self.environment_order = ["DEV", "TEST", "PRE", "PROD"]


class ReleaseAnalyzer:
    """Analyzes release differences between environments."""
    
    def __init__(self):
        self.api_client = ActuatorClient()
        self.git_manager = GitManager()
        self.logger = logging.getLogger(__name__)
    
    def analyze_project(self, project_config) -> Optional[ProjectAnalysis]:
        """
        Analyze a single project across all environments.
        
        Args:
            project_config: ProjectConfig object
            
        Returns:
            ProjectAnalysis object or None if analysis fails
        """
        # Fetch version info from all environments
        version_infos = {}
        for env_name, env_url in project_config.env.items():
            self.logger.info(f"Fetching version info for {project_config.name} - {env_name}")
            version_info = self.api_client.get_version_info(
                env_url, env_name, project_config.verify_ssl, project_config.use_version_fallback
            )
            if version_info:
                version_infos[env_name] = version_info
            else:
                self.logger.warning(f"Could not fetch version info for {env_name}")
        
        if not version_infos:
            self.logger.error(f"No version information available for {project_config.name}")
            return None
        
        # Get or update repository
        repo = self.git_manager.get_or_update_repo(project_config.repoUrl, project_config.name)
        if not repo:
            self.logger.error(f"Could not access repository for {project_config.name}")
            return None
        
        # Analyze commits for each environment
        environments = {}
        env_order = ["DEV", "TEST", "PRE", "PROD"]
        
        for env in env_order:
            if env in version_infos:
                version_info = version_infos[env]
                
                # Resolve commit reference (handle both commit IDs and tags/versions)
                resolved_commit_id = self.git_manager.resolve_commit_reference(repo, version_info.commit_id)
                if not resolved_commit_id:
                    if version_info.commit_source == "version_fallback":
                        self.logger.warning(f"Version '{version_info.commit_id}' could not be resolved to a commit/tag in repository for {env}")
                    else:
                        self.logger.warning(f"Commit '{version_info.commit_id}' not found in repository for {env}")
                    continue
                
                # Log successful resolution if using fallback
                if version_info.commit_source == "version_fallback":
                    self.logger.info(f"Resolved version '{version_info.commit_id}' to commit {resolved_commit_id[:8]} for {env}")
                
                # Update version_info with resolved commit ID
                version_info.commit_id = resolved_commit_id
                
                # Calculate commits specific to this environment
                commits = self._get_environment_specific_commits(
                    repo, env, version_info.commit_id, version_infos, env_order
                )
                
                environments[env] = EnvironmentCommits(
                    environment=env,
                    version=version_info.version,
                    commit_id=version_info.commit_id,
                    commits=commits
                )
        
        if not environments:
            self.logger.error(f"No valid environment data for {project_config.name}")
            return None
        
        return ProjectAnalysis(
            project_name=project_config.name,
            environments=environments,
            environment_order=env_order
        )
    
    def _get_environment_specific_commits(self, repo: Repo, current_env: str, 
                                        current_commit: str, version_infos: Dict[str, VersionInfo],
                                        env_order: List[str]) -> List[dict]:
        """
        Get commits that are specific to the current environment compared to the baseline.
        
        PROD is the baseline.
        PRE shows commits not in PROD.
        TEST shows commits not in PRE.
        DEV shows commits not in TEST.
        """
        current_idx = env_order.index(current_env) if current_env in env_order else -1
        
        if current_idx == -1:
            return []
        
        # PROD is the baseline - no comparison needed
        if current_env == "PROD":
            return []
        
        # Find the baseline environment (next environment in the promotion chain)
        baseline_env = None
        for i in range(current_idx + 1, len(env_order)):
            if env_order[i] in version_infos:
                baseline_env = env_order[i]
                break
        
        if not baseline_env:
            # If no baseline found, show all commits up to current
            self.logger.info(f"No baseline found for {current_env}, showing all commits")
            return self.git_manager.get_commits_between(repo, "HEAD~100", current_commit)
        
        baseline_commit = version_infos[baseline_env].commit_id
        
        self.logger.info(f"Comparing {current_env} ({current_commit[:8]}) with {baseline_env} ({baseline_commit[:8]})")
        
        # Get commits that are in current environment but not in baseline
        return self.git_manager.get_commits_between(repo, baseline_commit, current_commit)