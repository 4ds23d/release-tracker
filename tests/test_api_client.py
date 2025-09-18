import pytest
import responses
import requests
from unittest.mock import Mock, patch

from git_release_notifier.api_client import ActuatorClient, VersionInfo


class TestActuatorClient:
    
    def setup_method(self):
        self.client = ActuatorClient(timeout=10)
    
    @responses.activate
    def test_get_version_info_success(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            json={
                "build": {"version": "2.1.0"},
                "git": {"commit": {"id": "abc123def456"}}
            },
            status=200
        )
        
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is not None
        assert isinstance(result, VersionInfo)
        assert result.version == "2.1.0"
        assert result.commit_id == "abc123def456"
        assert result.environment == "PROD"
    
    @responses.activate
    def test_get_version_info_alternative_structure(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            json={
                "app": {"version": "1.5.2"},
                "git": {"commit": "xyz789abc123"}
            },
            status=200
        )
        
        result = self.client.get_version_info(base_url, "TEST")
        
        assert result is not None
        assert result.version == "1.5.2"
        assert result.commit_id == "xyz789abc123"
        assert result.environment == "TEST"
    
    @responses.activate
    def test_get_version_info_git_build_version(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            json={
                "git": {
                    "build": {"version": "3.0.0"},
                    "commit": {"id": "full123abc456def789", "abbrev": "short123"}
                }
            },
            status=200
        )
        
        result = self.client.get_version_info(base_url, "DEV")
        
        assert result is not None
        assert result.version == "3.0.0"
        assert result.commit_id == "full123abc456def789"
    
    @responses.activate
    def test_get_version_info_http_error(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            status=404
        )
        
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is None
    
    @responses.activate
    def test_get_version_info_connection_error(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            body=requests.ConnectionError("Connection failed")
        )
        
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is None
    
    @responses.activate
    def test_get_version_info_invalid_json(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            body="invalid json",
            status=200
        )
        
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is None
    
    @responses.activate
    def test_get_version_info_missing_version(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            json={
                "git": {"commit": {"id": "abc123"}}
            },
            status=200
        )
        
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is None
    
    @responses.activate
    def test_get_version_info_missing_commit(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            json={
                "build": {"version": "1.0.0"}
            },
            status=200
        )
        
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is None
    
    @responses.activate 
    def test_get_version_info_url_with_trailing_slash(self):
        base_url = "https://api.example.com/"
        responses.add(
            responses.GET,
            "https://api.example.com/actuator/info",
            json={
                "build": {"version": "1.0.0"},
                "git": {"commit": {"id": "abc123"}}
            },
            status=200
        )
        
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is not None
        assert result.version == "1.0.0"
    
    @responses.activate
    def test_get_version_info_ssl_verification_disabled(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            json={
                "build": {"version": "1.0.0"},
                "git": {"commit": {"id": "abc123"}}
            },
            status=200
        )
        
        result = self.client.get_version_info(base_url, "PROD", verify_ssl=False)
        
        assert result is not None
        assert result.version == "1.0.0"
        assert result.commit_id == "abc123"
        assert result.environment == "PROD"
    
    @responses.activate
    def test_get_version_info_ssl_verification_enabled_default(self):
        base_url = "https://api.example.com"
        responses.add(
            responses.GET,
            f"{base_url}/actuator/info",
            json={
                "build": {"version": "1.0.0"},
                "git": {"commit": {"id": "abc123"}}
            },
            status=200
        )
        
        # Test that SSL verification is enabled by default
        result = self.client.get_version_info(base_url, "PROD")
        
        assert result is not None
        assert result.version == "1.0.0"
    
    def test_extract_version_various_paths(self):
        client = ActuatorClient()
        
        # Test build.version path
        data1 = {"build": {"version": "1.0.0"}}
        assert client._extract_version(data1) == "1.0.0"
        
        # Test app.version path
        data2 = {"app": {"version": "2.0.0"}}
        assert client._extract_version(data2) == "2.0.0"
        
        # Test direct version path
        data3 = {"version": "3.0.0"}
        assert client._extract_version(data3) == "3.0.0"
        
        # Test git.build.version path
        data4 = {"git": {"build": {"version": "4.0.0"}}}
        assert client._extract_version(data4) == "4.0.0"
        
        # Test no version found
        data5 = {"other": "data"}
        assert client._extract_version(data5) is None
    
    def test_extract_commit_id_various_paths(self):
        client = ActuatorClient()
        
        # Test git.commit.id path
        data1 = {"git": {"commit": {"id": "abc123"}}}
        assert client._extract_commit_id(data1) == "abc123"
        
        # Test git.commit.id.abbrev path (should prefer full id over abbrev)
        data2 = {"git": {"commit": {"id": "full123abc456", "abbrev": "short123"}}}
        assert client._extract_commit_id(data2) == "full123abc456"
        
        # Test build.commit path
        data3 = {"build": {"commit": "xyz789"}}
        assert client._extract_commit_id(data3) == "xyz789"
        
        # Test direct commit path
        data4 = {"commit": "direct123"}
        assert client._extract_commit_id(data4) == "direct123"
        
        # Test git.commit path (string value)
        data5 = {"git": {"commit": "gitcommit123"}}
        assert client._extract_commit_id(data5) == "gitcommit123"
        
        # Test abbrev only when no full id
        data6 = {"git": {"commit": {"abbrev": "short123"}}}
        assert client._extract_commit_id(data6) == "short123"
        
        # Test no commit found
        data7 = {"other": "data"}
        assert client._extract_commit_id(data7) is None
    
    def test_get_nested_value(self):
        client = ActuatorClient()
        data = {
            "level1": {
                "level2": {
                    "level3": "value"
                }
            }
        }
        
        assert client._get_nested_value(data, ["level1", "level2", "level3"]) == "value"
        assert client._get_nested_value(data, ["level1", "level2"]) == {"level3": "value"}
        assert client._get_nested_value(data, ["nonexistent"]) is None
        assert client._get_nested_value(data, ["level1", "nonexistent"]) is None


class TestVersionInfo:
    
    def test_version_info_creation(self):
        version_info = VersionInfo(
            version="1.0.0",
            commit_id="abc123",
            environment="PROD"
        )
        
        assert version_info.version == "1.0.0"
        assert version_info.commit_id == "abc123"
        assert version_info.environment == "PROD"