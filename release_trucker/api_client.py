import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging


@dataclass
class VersionInfo:
    version: str
    commit_id: str
    environment: str
    commit_source: str = "git"  # "git" or "version_fallback"


class ActuatorClient:
    """Client for fetching version information from Spring Boot actuator endpoints."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def get_version_info(self, base_url: str, environment: str, verify_ssl: bool = True, 
                        use_version_fallback: bool = True) -> Optional[VersionInfo]:
        """
        Fetch version and commit information from /actuator/info endpoint.
        
        Args:
            base_url: Base URL of the service
            environment: Environment name (PROD, PRE, TEST, DEV)
            verify_ssl: Whether to verify SSL certificates (default: True)
            use_version_fallback: Use version as commit ID if git commit not found (default: True)
            
        Returns:
            VersionInfo object or None if request fails
        """
        url = f"{base_url.rstrip('/')}/actuator/info"
        
        try:
            # Suppress SSL warnings when verification is disabled
            if not verify_ssl:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(url, timeout=self.timeout, verify=verify_ssl)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract version and commit info from typical Spring Boot actuator response
            version = self._extract_version(data)
            commit_id = self._extract_commit_id(data)
            
            # Implement fallback strategy
            commit_source = "git"
            if version and commit_id:
                # Both version and commit available - use commit
                final_commit_id = commit_id
            elif version and use_version_fallback:
                # Only version available - use version as commit reference
                final_commit_id = version
                commit_source = "version_fallback"
                self.logger.info(f"Using version '{version}' as commit reference for {environment} (no git commit found)")
            elif version:
                # Version available but fallback disabled
                self.logger.warning(f"No git commit found for {environment} and version fallback is disabled")
                return None
            else:
                # No version or commit available
                self.logger.warning(f"Could not extract version/commit info from {url}")
                return None
            
            return VersionInfo(
                version=version,
                commit_id=final_commit_id,
                environment=environment,
                commit_source=commit_source
            )
                
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch info from {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing response from {url}: {e}")
            return None
    
    def _extract_version(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract version from actuator info response."""
        # Common paths for version information
        version_paths = [
            ['build', 'version'],
            ['app', 'version'],
            ['version'],
            ['git', 'build', 'version']
        ]
        
        for path in version_paths:
            value = self._get_nested_value(data, path)
            if value:
                return str(value)
        
        return None
    
    def _extract_commit_id(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract commit ID from actuator info response."""
        # Common paths for commit information
        commit_paths = [
            ['git', 'commit', 'id'],
            ['git', 'commit', 'id', 'abbrev'],
            ['build', 'commit'],
            ['commit'],
            ['git', 'commit']
        ]
        
        for path in commit_paths:
            value = self._get_nested_value(data, path)
            if value:
                # If value is a string, return it directly
                if isinstance(value, str):
                    return value
                # If value is a dict (like git.commit object), try to extract from it
                elif isinstance(value, dict):
                    # Try to get 'id' first, then 'abbrev'
                    if 'id' in value:
                        return str(value['id'])
                    elif 'abbrev' in value:
                        return str(value['abbrev'])
                # Otherwise convert to string
                else:
                    return str(value)
        
        return None
    
    def _get_nested_value(self, data: Dict[str, Any], path: list) -> Optional[Any]:
        """Get nested value from dictionary using path."""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current