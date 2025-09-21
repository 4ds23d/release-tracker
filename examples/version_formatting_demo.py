#!/usr/bin/env python3
"""
Demo to verify that VersionInfo f-string formatting works correctly.

This addresses the error: "unsupported format string passed to VersionInfo.__format__"
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from release_trucker.release_manager import VersionInfo


def demo_version_formatting():
    """Demonstrate various formatting scenarios for VersionInfo."""
    print("🏷️  VersionInfo Formatting Demo")
    print("=" * 40)
    
    version = VersionInfo(1, 2, 3)
    
    print(f"\n📋 Testing different formatting methods:")
    
    # Direct string conversion
    print(f"  str(version): {str(version)}")
    
    # F-string formatting (this was causing the error)
    print(f"  f-string: {version}")
    print(f"  f-string with text: Version {version} is ready")
    print(f"  f-string in message: 🏷️  New version: {version}")
    
    # Format function
    print(f"  format(): {format(version)}")
    
    # Version bumping with f-strings
    print(f"\n🚀 Version bumping examples:")
    print(f"  Current: {version}")
    print(f"  Next major: {version.bump_major()}")
    print(f"  Next minor: {version.bump_minor()}")
    print(f"  Next patch: {version.bump_patch()}")
    
    # Simulate CLI output scenarios
    print(f"\n📊 CLI-style output simulation:")
    print(f"   ✅ Release prepared: release/BWD-123")
    print(f"   🏷️  New version: {version}")
    print(f"   📝 Commits to include: 5")
    
    print(f"\n🎉 All formatting scenarios work correctly!")
    print("The f-string formatting error has been resolved! ✅")


if __name__ == "__main__":
    demo_version_formatting()