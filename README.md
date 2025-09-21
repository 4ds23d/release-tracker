# Git Release Tracker 🚀

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python CLI tool that analyzes deployment states across environments and manages git release processes. Generate beautiful HTML reports showing deployment differences and automate release workflows across multiple projects with a single JIRA ticket.

## ✨ Features

### 📊 Deployment Analysis
- 🔍 **Smart Environment Analysis** - Automatically compares DEV → TEST → PRE → PROD deployments
- 🌐 **Spring Boot Integration** - Fetches version info from actuator endpoints
- 📊 **Interactive HTML Reports** - Beautiful, expandable commit details with modern UI
- 🎯 **Commit Diff Logic** - Shows exactly what's new in each environment

### 🚀 Release Management
- 🎫 **JIRA-Based Releases** - Start releases across multiple projects with a single JIRA ticket
- 🏷️ **Semantic Versioning** - Automatic version bumping based on git tags
- 🌿 **Branch Management** - Creates and manages release branches automatically
- 📝 **Change Detection** - Skips projects with no changes since last release
- 🔄 **Git Operations** - Automated tag creation and remote pushing
- ✅ **Interactive Confirmation** - User control over each push operation

### 🛠️ General
- 🔄 **Multi-Project Support** - Handle multiple repositories and services
- ⚡ **Auto Git Management** - Clones and updates repositories automatically
- 🎫 **JIRA Integration** - Automatically extracts and links JIRA tickets from commit messages

## 🖼️ Screenshot

![Example Report](example_report.html)
*Interactive HTML report showing deployment differences*

## 🚀 Quick Start

### 1. Clone and Install
```bash
git clone https://github.com/yourusername/deployment-diff.git
cd deployment-diff
pip install -r requirements.txt
```

### 2. Configure Projects
Edit `config.yaml`:
```yaml
projects:
  - name: "user-service"
    repoUrl: "https://github.com/company/user-service.git"
    main_branch: main  # Default: main (used for release management)
    env:
      PROD: "https://api-prod.company.com/actuator/info"
      PRE: "https://api-pre.company.com/actuator/info" 
      TEST: "https://api-test.company.com/actuator/info"
      DEV: "https://api-dev.company.com/actuator/info"
    jira_base_url: "https://yourcompany.atlassian.net"  # Optional: JIRA base URL for linking tickets
```

### 3. Usage Examples

#### Deployment Analysis
```bash
# Analyze deployments across environments
python -m release_trucker.cli analyze --config config.yaml --output report.html
```

#### Release Management
```bash
# Start release process for JIRA ticket BWD-123
python -m release_trucker.cli release --config config.yaml BWD-123
```

### 4. View Results
- **Deployment Reports**: Open `report.html` in your browser to explore deployment analysis
- **Release Process**: Follow the interactive prompts to push branches and tags

## 🛠️ Usage

### Deployment Analysis
```bash
python -m release_trucker.cli analyze [OPTIONS]

Options:
  -c, --config PATH    Configuration file path [default: config.yaml]
  -o, --output PATH    Output HTML file path [default: release_report.html]
  -v, --verbose        Enable verbose logging
  --cleanup            Clean up cloned repositories after analysis
  --help               Show this message and exit
```

### Release Management
```bash
python -m release_trucker.cli release [OPTIONS] JIRA_TICKET

Arguments:
  JIRA_TICKET          JIRA ticket ID (e.g., BWD-123, AUTH-456)

Options:
  -c, --config PATH    Configuration file path [default: config.yaml]
  -v, --verbose        Enable verbose logging
  --help               Show this message and exit
```

## 🔧 How It Works

### 📊 Deployment Analysis
1. **🌐 Fetch Version Info** - Calls `/actuator/info` endpoints to get current deployments
2. **📋 Git Analysis** - Clones/updates repos and analyzes commit differences  
3. **📊 Smart Comparison** - Uses environment hierarchy for meaningful diffs:
   - **PROD** → Baseline (production-ready commits)
   - **PRE** → Shows commits ready for production  
   - **TEST** → Shows commits ready for pre-production
   - **DEV** → Shows all development commits
4. **🎨 Report Generation** - Creates interactive HTML with commit details

### 🚀 Release Process
1. **✅ Validation** - Validates JIRA ticket format (e.g., `BWD-123`)
2. **📋 Repository Management** - Fetches/updates repositories and checks out main branch
3. **🌿 Branch Operations** - Creates or updates release branches (`release/{jira_ticket}`)
4. **🏷️ Version Calculation** - Determines new version based on existing semantic versioning tags
5. **📝 Change Detection** - Uses remote branch references to detect changes since last tag
6. **👤 User Confirmation** - Interactive prompts for pushing branches and tags
7. **🔄 Git Operations** - Creates annotated tags and pushes to remote repositories

## ⚙️ Configuration

### Basic Setup
```yaml
projects:
  - name: "api-gateway"
    repoUrl: "git@github.com:company/api-gateway.git"
    main_branch: main  # Default: main (used for release management)
    env:
      PROD: "https://gateway-prod.company.com/actuator/info"
      PRE: "https://gateway-pre.company.com/actuator/info"
      TEST: "https://gateway-test.company.com/actuator/info"
      DEV: "https://gateway-dev.company.com/actuator/info"
    # verify_ssl: true  # Optional: Enable/disable SSL verification (default: true)
    # use_version_fallback: true  # Optional: Use version as commit fallback (default: true)
    # jira_base_url: "https://yourcompany.atlassian.net"  # Optional: JIRA base URL for linking tickets
      
  - name: "user-service"
    repoUrl: "https://github.com/company/user-service.git"
    main_branch: develop  # Custom main branch for release operations
    env:
      PROD: "https://users-prod.company.com/actuator/info"
      PRE: "https://users-pre.company.com/actuator/info"
      TEST: "https://users-test.company.com/actuator/info"
      DEV: "https://users-dev.company.com/actuator/info"
    verify_ssl: false  # Disable SSL verification for self-signed certificates
    use_version_fallback: true  # Use version as git tag if no commit ID available
```

### SSL Configuration
For internal environments with self-signed certificates or when SSL verification needs to be bypassed:

```yaml
projects:
  - name: "internal-service"
    repoUrl: "https://github.com/company/internal-service.git"
    env:
      PROD: "https://internal-prod.company.local"
      DEV: "https://internal-dev.company.local"
    verify_ssl: false  # Disable SSL certificate verification
```

### Version Fallback Strategy
For applications that only expose version information (without git commit details):

```yaml
projects:
  - name: "version-only-service"
    repoUrl: "https://github.com/company/version-service.git"
    env:
      PROD: "https://version-prod.company.com"
      DEV: "https://version-dev.company.com"
    use_version_fallback: true  # Use version as git tag/commit reference
```

#### How Version Fallback Works:
1. **Primary Strategy**: Use git commit ID from `/actuator/info` if available
2. **Fallback Strategy**: If no git commit found, use version as git reference (tag/commit)
3. **Resolution**: Tool attempts to resolve version string to actual commit in repository

#### Example Actuator Response (Version Only):
```json
{
  "build": {
    "version": "v2.1.0"
  }
  // No git commit information
}
```
The tool will use `"v2.1.0"` to lookup the corresponding git tag/commit.

⚠️ **Security Warning**: Only disable SSL verification (`verify_ssl: false`) for trusted internal environments. This should not be used for external or untrusted endpoints.

### Release Management Configuration

#### Main Branch Setting
The `main_branch` setting specifies which branch to use as the base for release operations:

```yaml
projects:
  - name: "frontend-app"
    repoUrl: "https://github.com/company/frontend-app.git"
    main_branch: main     # Uses 'main' branch for releases
    
  - name: "backend-api"
    repoUrl: "https://github.com/company/backend-api.git"
    main_branch: develop  # Uses 'develop' branch for releases
```

#### Semantic Versioning
The release manager only considers tags that follow semantic versioning (major.minor.patch) pattern:

- ✅ **Valid tags**: `1.0.0`, `2.1.3`, `10.0.1`
- ❌ **Ignored tags**: `v1.0.0`, `1.2`, `staging-deploy`, `hotfix-auth`, `1.0.0-SNAPSHOT`

#### Version Bumping Logic
- **New Release Branch**: Major = highest existing major + 1, minor/patch = 0
- **Existing Release Branch**: Bumps minor version, keeps existing major

#### JIRA Ticket Format
Valid JIRA ticket formats for release commands:
- ✅ `BWD-123`, `AUTH-456`, `FEAT-1`, `PROJECT-9999`
- ❌ `bwd-123` (lowercase), `BWD123` (missing dash), `BWD-` (missing number)

### JIRA Integration
For projects with JIRA tickets referenced in commit messages, configure `jira_base_url` to automatically extract and link tickets:

```yaml
projects:
  - name: "project-with-jira"
    repoUrl: "https://github.com/company/project.git"
    env:
      PROD: "https://project-prod.company.com"
      DEV: "https://project-dev.company.com"
    jira_base_url: "https://yourcompany.atlassian.net"
```

#### How JIRA Integration Works:
1. **Ticket Detection**: Scans commit messages for JIRA ticket patterns (e.g., `ABC-123`, `PROJ-456`)
2. **Pattern**: Matches 1-10 uppercase letters followed by dash and digits: `[A-Z]{1,10}-\d+`
3. **Link Generation**: Creates clickable links to `{jira_base_url}/browse/{ticket-id}`
4. **Display**: Shows tickets as blue badges near each environment in the report

#### Example Commit Messages:
- ✅ `ABC-123: Fix authentication bug`
- ✅ `Feature implementation for PROJ-456 and ABC-789`
- ✅ `Multiple tickets: DEV-111, QA-222, RELEASE-333`
- ❌ `123-ABC` (digits first)
- ❌ `TOOLONGPROJECTNAME-123` (more than 10 characters)

### Expected Actuator Response
Your `/actuator/info` endpoints should return:
```json
{
  "build": {
    "version": "2.1.0"
  },
  "git": {
    "commit": {
      "id": "a7f3b2c1d8e4f5g6h7i8j9k0"
    }
  }
}
```

## 📊 Example Release Process Output

```bash
$ python -m release_trucker.cli release --config config.yaml BWD-123

🚀 Starting release process for JIRA ticket: BWD-123
📋 Processing 3 projects...

📦 Processing project: frontend-app
   ✅ Release prepared: release/BWD-123
   🏷️  New version: 3.0.0
   📝 Commits to include: 15

📦 Processing project: backend-api
   ✅ Release prepared: release/BWD-123
   🏷️  New version: 2.1.0
   📝 Commits to include: 8

📦 Processing project: mobile-service
   ⏭️  Skipped (no changes since last tag)

📊 Release Summary:
Project              Branch                    Version    Commits 
----------------------------------------------------------------------
frontend-app         release/BWD-123           3.0.0      15      
backend-api          release/BWD-123           2.1.0      8       

🔄 Project: frontend-app
   Push branch 'release/BWD-123' to remote? [y/N]: y
   ✅ Branch pushed successfully
   🏷️  Tag 3.0.0 created
   Push tag '3.0.0' to remote? [y/N]: y
   ✅ Tag pushed successfully

🔄 Project: backend-api
   Push branch 'release/BWD-123' to remote? [y/N]: y
   ✅ Branch pushed successfully
   🏷️  Tag 2.1.0 created
   Push tag '2.1.0' to remote? [y/N]: y
   ✅ Tag pushed successfully

🎉 Release process completed for BWD-123!
```

## 📋 Requirements

- **Python 3.7+**
- **Git** installed and accessible
- **Network access** to APIs and repositories
- **Spring Boot** applications with actuator endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for teams managing microservices across multiple environments
- Inspired by the need for deployment visibility and change tracking
- Designed to work seamlessly with Spring Boot and Git workflows