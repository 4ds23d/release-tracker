# Deployment Diff 🚀

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python CLI tool that analyzes deployment states across environments and generates beautiful HTML reports showing exactly what changes are deployed where.

## ✨ Features

- 🔍 **Smart Environment Analysis** - Automatically compares DEV → TEST → PRE → PROD deployments
- 🌐 **Spring Boot Integration** - Fetches version info from actuator endpoints
- 📊 **Interactive HTML Reports** - Beautiful, expandable commit details with modern UI
- 🔄 **Multi-Project Support** - Handle multiple repositories and services
- ⚡ **Auto Git Management** - Clones and updates repositories automatically
- 🎯 **Commit Diff Logic** - Shows exactly what's new in each environment

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
    env:
      PROD: "https://api-prod.company.com"
      PRE: "https://api-pre.company.com" 
      TEST: "https://api-test.company.com"
      DEV: "https://api-dev.company.com"
```

### 3. Generate Report
```bash
python main.py --config config.yaml --output report.html
```

### 4. View Results
Open `report.html` in your browser to explore the deployment analysis.

## Usage

```bash
python main.py [OPTIONS]

Options:
  -c, --config PATH    Configuration file path [default: config.yaml]
  -o, --output PATH    Output HTML file path [default: release_report.html]
  -v, --verbose        Enable verbose logging
  --cleanup            Clean up cloned repositories after analysis
  --help               Show this message and exit
```

## How it Works

1. **Fetch Version Info**: Calls `/actuator/info` endpoint for each environment to get version and commit information
2. **Git Analysis**: Clones/updates repositories and compares commits between environments
3. **Report Generation**: Creates an HTML report showing:
   - PROD: Baseline environment (no commits shown)
   - PRE: Commits not yet deployed to PROD
   - TEST: Commits not yet deployed to PRE
   - DEV: Commits not yet deployed to TEST

## Configuration

The `config.yaml` file defines your projects and their environment URLs. Each project requires:

- `name`: Unique project identifier
- `repoUrl`: Git repository URL (HTTPS or SSH)
- `env`: Dictionary mapping environment names to their actuator URLs

## Requirements

- Python 3.7+
- Git installed and accessible
- Network access to configured APIs and repositories
- Spring Boot applications with `/actuator/info` endpoint enabled

## License

MIT License