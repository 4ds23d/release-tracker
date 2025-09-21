#!/bin/bash

# Manual Verification Script for Git Release Tracker
# This script demonstrates the CLI commands you can run manually

set -e

echo "🎯 Git Release Tracker - Manual Verification"
echo "=============================================="
echo ""

# Activate virtual environment if available
if [ -d "../.venv" ]; then
    echo "📦 Activating virtual environment..."
    source ../.venv/bin/activate
    echo "✅ Virtual environment activated"
    echo ""
fi

cd ..

echo "🔧 1. Help Command"
echo "Command: python -m release_trucker.cli --help"
echo "----------------------------------------"
python -m release_trucker.cli --help
echo ""

echo "📊 2. Analyze Command Help"
echo "Command: python -m release_trucker.cli analyze --help"
echo "----------------------------------------------------"
python -m release_trucker.cli analyze --help
echo ""

echo "🚀 3. Release Command Help"
echo "Command: python -m release_trucker.cli release --help"
echo "----------------------------------------------------"
python -m release_trucker.cli release --help
echo ""

echo "❌ 4. Invalid JIRA Ticket Test"
echo "Command: python -m release_trucker.cli release --config examples/config_example.yaml invalid-ticket"
echo "------------------------------------------------------------------------------------------------"
python -m release_trucker.cli release --config examples/config_example.yaml invalid-ticket || echo "✅ Expected failure for invalid JIRA ticket"
echo ""

echo "✅ 5. Valid JIRA Ticket Test (will fail on git operations - expected)"
echo "Command: python -m release_trucker.cli release --config examples/config_example.yaml BWD-123"
echo "---------------------------------------------------------------------------------------------"
python -m release_trucker.cli release --config examples/config_example.yaml BWD-123 || echo "✅ Expected failure due to missing git repositories"
echo ""

echo "🎉 Manual verification completed!"
echo ""
echo "💡 Next Steps:"
echo "   1. Update examples/config_example.yaml with real repository URLs"
echo "   2. Ensure you have git access to those repositories"
echo "   3. Run: python -m release_trucker.cli release --config examples/config_example.yaml YOUR-TICKET-123"
echo ""
echo "📋 For deployment analysis:"
echo "   1. Update config with real actuator endpoints"
echo "   2. Run: python -m release_trucker.cli analyze --config examples/config_example.yaml"