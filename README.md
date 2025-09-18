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

## 🛠️ Usage

```bash
python main.py [OPTIONS]

Options:
  -c, --config PATH    Configuration file path [default: config.yaml]
  -o, --output PATH    Output HTML file path [default: release_report.html]
  -v, --verbose        Enable verbose logging
  --cleanup            Clean up cloned repositories after analysis
  --help               Show this message and exit
```

## 🔧 How It Works

1. **🌐 Fetch Version Info** - Calls `/actuator/info` endpoints to get current deployments
2. **📋 Git Analysis** - Clones/updates repos and analyzes commit differences  
3. **📊 Smart Comparison** - Uses environment hierarchy for meaningful diffs:
   - **PROD** → Baseline (production-ready commits)
   - **PRE** → Shows commits ready for production  
   - **TEST** → Shows commits ready for pre-production
   - **DEV** → Shows all development commits
4. **🎨 Report Generation** - Creates interactive HTML with commit details

## ⚙️ Configuration

### Basic Setup
```yaml
projects:
  - name: "api-gateway"
    repoUrl: "git@github.com:company/api-gateway.git"
    env:
      PROD: "https://gateway-prod.company.com"
      PRE: "https://gateway-pre.company.com"
      TEST: "https://gateway-test.company.com"
      DEV: "https://gateway-dev.company.com"
      
  - name: "user-service"
    repoUrl: "https://github.com/company/user-service.git"
    env:
      PROD: "https://users-prod.company.com"
      PRE: "https://users-pre.company.com"
      TEST: "https://users-test.company.com"
      DEV: "https://users-dev.company.com"
```

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