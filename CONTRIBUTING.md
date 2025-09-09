# Contributing to Kamstrup 402 MQTT

Thank you for your interest in contributing to the Kamstrup 402 MQTT project! This document provides guidelines for contributing to this project.

## Code of Conduct

Be respectful and constructive in all interactions. This project is maintained by volunteers who give their time to help the community.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Access to a Kamstrup Multical 402/403/603 heat meter for testing

### Setting up the Development Environment

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/your-username/kamstrup-402-mqtt.git
   cd kamstrup-402-mqtt
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install development tools (optional but recommended):
   ```bash
   pip install black flake8 mypy isort
   ```

## Code Style

This project follows Python best practices:

- **Code Formatting**: Use [Black](https://black.readthedocs.io/) for code formatting
- **Linting**: Use [Flake8](https://flake8.pycqa.org/) for linting
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all classes and functions
- **Line Length**: Maximum 88 characters per line

### Running Code Quality Tools

```bash
# Format code
black .

# Check linting
flake8 .

# Type checking
mypy .

# Sort imports
isort .
```

## Documentation

- All public functions and classes must have comprehensive docstrings
- Use Google-style docstrings with Args, Returns, and Raises sections
- Update the README.md if you add new features or change configuration options
- Add inline comments for complex algorithms or protocol-specific code

## Testing

### Manual Testing

Since this project interfaces with physical hardware, automated testing is limited:

1. Test with a real Kamstrup meter when possible
2. Verify MQTT publishing works with your broker
3. Test configuration validation with invalid configs
4. Test error handling by introducing connection issues

### Code Validation

Always run these checks before submitting:

```bash
# Syntax check
python3 -m py_compile daemon.py kamstrup_meter.py mqtt_handler.py

# Type checking
mypy --strict .

# Linting
flake8 .
```

## Submitting Changes

### Pull Request Process

1. **Fork** the repository and create a feature branch from `main`
2. **Make your changes** following the code style guidelines
3. **Test** your changes thoroughly
4. **Document** any new features or configuration changes
5. **Submit** a pull request with a clear description

### Commit Messages

Use clear, descriptive commit messages:

```
Add type hints and docstrings to mqtt_handler.py

- Added comprehensive type hints for all methods
- Added Google-style docstrings with full parameter documentation
- Improved error handling with specific exception types
- Fixed inconsistent indentation
```

### Pull Request Description

Include in your PR description:

- **What** changes you made and **why**
- **How** to test the changes
- Any **breaking changes** or **migration notes**
- Screenshots for UI changes (if applicable)

## Types of Contributions

### Bug Reports

When reporting bugs, include:

- Python version
- Operating system
- Kamstrup meter model
- Complete error messages and logs
- Steps to reproduce the issue
- Configuration file (with sensitive data removed)

### Feature Requests

Before suggesting new features:

- Check existing issues to avoid duplicates
- Explain the use case and expected behavior
- Consider if the feature fits the project scope

### Code Contributions

Priority areas for contributions:

- **Protocol Support**: Adding support for new Kamstrup meter models
- **Error Handling**: Improving robustness and error recovery
- **Configuration**: Adding validation and better error messages
- **Documentation**: Improving setup guides and troubleshooting
- **Performance**: Optimizing serial communication and MQTT publishing

## Hardware Compatibility

If you add support for new Kamstrup meter models:

- Document the meter model and firmware version tested
- Add parameter mappings to the `KAMSTRUP_402_PARAMS` dictionary
- Update the README.md with compatibility information
- Test thoroughly with the actual hardware

## Questions?

- **General Questions**: Open a GitHub Discussion
- **Bug Reports**: Open a GitHub Issue
- **Security Issues**: Email the maintainer directly

Thank you for contributing!