#!/usr/bin/env python3
"""
Demo script to showcase the improved semantic versioning tag handling.

This script demonstrates how the release manager now properly handles
repositories with mixed tag types, filtering only semantic versioning tags.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from release_trucker.release_manager import ReleaseManager


def demo_version_parsing():
    """Demonstrate version parsing with various tag formats."""
    print("🏷️  Semantic Versioning Tag Filtering Demo")
    print("=" * 50)
    
    manager = ReleaseManager()
    
    print("\n📋 Version Parsing Examples:")
    test_tags = [
        "1.0.0",           # ✅ Valid semantic version
        "2.1.3",           # ✅ Valid semantic version
        "10.0.1",          # ✅ Valid semantic version
        "v1.0.0",          # ❌ Invalid (has 'v' prefix)
        "1.2",             # ❌ Invalid (missing patch)
        "1.2.3.4",         # ❌ Invalid (too many parts)
        "1.0.0-SNAPSHOT",  # ❌ Invalid (has suffix)
        "release-1.0",     # ❌ Invalid (not semantic)
        "staging",         # ❌ Invalid (not semantic)
        "production",      # ❌ Invalid (not semantic)
        "hotfix-auth",     # ❌ Invalid (not semantic)
    ]
    
    valid_versions = []
    for tag in test_tags:
        version = manager.parse_version(tag)
        if version:
            print(f"  ✅ '{tag}' -> {version}")
            valid_versions.append(version)
        else:
            print(f"  ❌ '{tag}' -> Invalid (filtered out)")
    
    print(f"\n📊 Summary:")
    print(f"  Total tags: {len(test_tags)}")
    print(f"  Valid semantic versions: {len(valid_versions)}")
    print(f"  Filtered out: {len(test_tags) - len(valid_versions)}")
    
    if valid_versions:
        # Sort and find latest
        valid_versions.sort(key=lambda v: (v.major, v.minor, v.patch), reverse=True)
        latest = valid_versions[0]
        print(f"  Latest valid version: {latest}")
        
        # Find highest major
        major_versions = [v.major for v in valid_versions]
        highest_major = max(major_versions)
        print(f"  Highest major version: {highest_major}")
        
        print(f"\n🚀 Next Release Versions:")
        print(f"  Next major: {latest.bump_major()}")
        print(f"  Next minor: {latest.bump_minor()}")
        print(f"  Next patch: {latest.bump_patch()}")


def demo_real_world_scenario():
    """Demonstrate a real-world scenario with mixed tags."""
    print("\n" + "=" * 50)
    print("🌍 Real-World Repository Scenario")
    print("=" * 50)
    
    print("\n📦 Imagine a repository with these tags:")
    mixed_tags = [
        "v0.1.0",              # Old versioning style
        "1.0.0",               # First semantic version
        "staging-deploy",       # Deployment tag
        "1.1.0",               # Semantic version
        "hotfix-2023-01",      # Hotfix tag
        "1.1.1",               # Semantic version
        "production-backup",    # Backup tag
        "2.0.0",               # Major version bump
        "temp-branch",         # Temporary tag
        "2.1.0",               # Latest semantic version
    ]
    
    manager = ReleaseManager()
    
    print("\n🔍 Tag Analysis:")
    semantic_versions = []
    for tag in mixed_tags:
        version = manager.parse_version(tag)
        if version:
            semantic_versions.append(version)
            print(f"  ✅ {tag} -> Will be considered for version logic")
        else:
            print(f"  🚫 {tag} -> Ignored (not semantic versioning)")
    
    print(f"\n📈 Version Management Results:")
    if semantic_versions:
        semantic_versions.sort(key=lambda v: (v.major, v.minor, v.patch), reverse=True)
        latest = semantic_versions[0]
        major_versions = [v.major for v in semantic_versions]
        highest_major = max(major_versions)
        
        print(f"  Latest semantic version: {latest}")
        print(f"  Highest major version: {highest_major}")
        print(f"  Next release version: {VersionInfo(highest_major + 1, 0, 0)}")
        
        print(f"\n💡 Benefits:")
        print(f"  ✅ Only semantic versions affect release logic")
        print(f"  ✅ Deployment/temp tags don't interfere")
        print(f"  ✅ Consistent version progression")
        print(f"  ✅ Robust handling of mixed tag types")


if __name__ == "__main__":
    # Import VersionInfo here to avoid circular imports
    from release_trucker.release_manager import VersionInfo
    
    demo_version_parsing()
    demo_real_world_scenario()
    
    print("\n" + "=" * 50)
    print("✨ The release manager now robustly handles repositories")
    print("   with mixed tag types, ensuring only semantic versions")
    print("   are used for release logic and version calculations!")
    print("=" * 50)