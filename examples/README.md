# Git Release Tracker - Examples and Usage

This directory contains examples demonstrating how to use the Git Release Tracker for both deployment analysis and release management.

## 🚀 Release Process Overview

The release functionality allows you to start a git release process across multiple projects with a single JIRA ticket.

### Release Process Flow

1. **Validation**: Validates JIRA ticket format (e.g., `BWD-123`)
2. **Repository Checkout**: Checks out the main branch for each project
3. **Branch Management**: Creates or updates release branches (`release/{jira_ticket}`)
4. **Version Calculation**: Determines new version based on existing git tags
5. **Change Detection**: Skips projects with no changes since last tag
6. **User Confirmation**: Asks for confirmation before pushing branches and tags
7. **Git Operations**: Creates annotated tags and pushes to remote

## 📋 Configuration

Create a `config.yaml` file with your project details:

```yaml
projects:
  - name: frontend-app
    repoUrl: https://github.com/company/frontend-app.git
    main_branch: main  # Default: main
    env:
      DEV: https://dev-frontend.company.com/actuator/info
      STAGING: https://staging-frontend.company.com/actuator/info
      PROD: https://prod-frontend.company.com/actuator/info
    verify_ssl: true
    use_version_fallback: true
    jira_base_url: https://company.atlassian.net

  - name: backend-api
    repoUrl: https://github.com/company/backend-api.git
    main_branch: develop  # Can be different per project
    env:
      DEV: https://dev-api.company.com/actuator/info
      PROD: https://prod-api.company.com/actuator/info
```

## 🎯 Usage Examples

### 1. Get Help

```bash
# Main help
python -m release_trucker.cli --help

# Analyze command help
python -m release_trucker.cli analyze --help

# Release command help
python -m release_trucker.cli release --help
```

### 2. Deployment Analysis

```bash
# Analyze deployments across environments
python -m release_trucker.cli analyze --config config.yaml --output report.html

# With verbose logging
python -m release_trucker.cli analyze --config config.yaml --verbose

# With cleanup of cloned repositories
python -m release_trucker.cli analyze --config config.yaml --cleanup
```

### 3. Release Process

```bash
# Start release process for JIRA ticket BWD-123
python -m release_trucker.cli release --config config.yaml BWD-123

# With custom config file
python -m release_trucker.cli release --config my-config.yaml AUTH-456
```

## 🏷️ Version Management

### Version Bumping Logic

- **New Release Branch**: Major = highest existing major + 1, minor/patch = 0
- **Existing Release Branch**: Bumps minor version, keeps existing major

### Semantic Versioning Tag Filtering

The release manager **only considers tags that follow semantic versioning** (major.minor.patch) pattern:

- ✅ **Valid**: `1.0.0`, `2.1.3`, `10.0.1`
- ❌ **Filtered out**: `v1.0.0`, `1.2`, `staging-deploy`, `hotfix-auth`, `1.0.0-SNAPSHOT`

This ensures that deployment tags, temporary tags, or non-semantic tags don't interfere with version logic.

### Examples

If your repository has mixed tags: `v0.1.0`, `1.0.0`, `staging-deploy`, `1.1.0`, `hotfix-2023`, `2.0.0`

**Only semantic versions are considered**: `1.0.0`, `1.1.0`, `2.0.0`

- **New release branch**: Creates version `3.0.0` (highest major + 1)
- **Existing release branch**: Bumps to next minor version based on latest semantic version

### JIRA Ticket Format

Valid JIRA ticket formats:
- ✅ `BWD-123`
- ✅ `AUTH-456` 
- ✅ `FEAT-1`
- ✅ `PROJECT-9999`

Invalid formats:
- ❌ `bwd-123` (lowercase)
- ❌ `BWD123` (missing dash)
- ❌ `BWD-` (missing number)
- ❌ `-123` (missing project code)

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
   ⏭️  Skipped (no changes or error)

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

## 🧪 Running the Demo

Run the comprehensive demo to see all functionality:

```bash
cd examples
python demo_release_process.py
```

This demo will show:
- Help commands
- Version management examples
- JIRA ticket validation
- Release process simulation
- Error handling scenarios

## 🔧 Development and Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_cli.py -v
python -m pytest tests/test_release_manager.py -v

# Run with coverage
python -m pytest tests/ --cov=release_trucker --cov-report=term-missing
```

### Project Structure

```
release_trucker/
├── cli.py              # Main CLI interface
├── release_manager.py  # Release management logic
├── config.py           # Configuration handling
├── analyzer.py         # Deployment analysis
├── git_manager.py      # Git operations
└── report_generator.py # HTML report generation

tests/
├── test_cli.py              # CLI tests
├── test_release_manager.py  # Release manager tests
└── ...

examples/
├── README.md                # This file
├── config_example.yaml      # Example configuration
└── demo_release_process.py  # Comprehensive demo
```

## 🚨 Important Notes

1. **Git Access**: Ensure you have proper access to all repositories in your config
2. **Authentication**: Set up SSH keys or appropriate git credentials
3. **Branch Protection**: Be aware of branch protection rules in your repositories
4. **Testing**: Always test with a small subset of projects first
5. **Backup**: Consider backing up important branches before running release processes

## 💡 Tips

- Use `--verbose` flag for detailed logging during development
- Test JIRA ticket validation before running on multiple projects
- Use the analyze command first to understand current deployment state
- Keep your configuration file in version control
- Set up appropriate `main_branch` values for each project

## 🆘 Troubleshooting

### Common Issues

1. **"Configuration file not found"**
   - Check the path to your config.yaml file
   - Use absolute paths if relative paths don't work

2. **"Invalid JIRA ticket format"**
   - Ensure ticket follows pattern: `LETTERS-DIGITS`
   - Examples: `BWD-123`, `AUTH-456`

3. **Git authentication errors**
   - Set up SSH keys for repository access
   - Check repository URLs in configuration

4. **"No changes since last tag"**
   - This is expected behavior - projects are skipped if no changes
   - Check if there are actual commits since the last tag

5. **Branch already exists**
   - The tool will checkout existing release branches
   - It will bump the minor version for existing branches

For more help, run any command with `--help` or check the test files for usage examples.