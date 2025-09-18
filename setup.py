from setuptools import setup, find_packages

setup(
    name="git-release-notifier",
    version="1.0.0",
    description="Command line application for retrieving deployment states across environments",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "GitPython>=3.1.40",
        "click>=8.1.7",
        "pyyaml>=6.0.1",
        "jinja2>=3.1.2",
    ],
    entry_points={
        'console_scripts': [
            'git-release-notifier=git_release_notifier.cli:main',
        ],
    },
    python_requires=">=3.7",
)