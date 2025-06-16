# PyAutoEnum

Automated Enumeration Tool for Security Testing

PyAutoEnum is a comprehensive tool for automated reconnaissance and enumeration of target systems, designed for security professionals and penetration testers.

## Features

- Automated port scanning and service detection
- Modular architecture for easy extension
- Customizable attack modules
- Interactive terminal-based UI
- Session persistence for resumed scans
- Multi-threaded execution of enumeration modules

## Project Structure

The project follows modern Python package organization:

```text
src/
└── pyautoenum/          # Main package
    ├── __init__.py      # Package metadata
    ├── __main__.py      # Entry point
    ├── config/          # Configuration management
    ├── core/            # Core functionality
    ├── data/            # Data models and storage
    ├── modules/         # Attack modules
    ├── resources/       # Static resources
    ├── ui/              # User interface components
    └── utils/           # Utility functions
tests/                   # Test suite
```

## Installation

### From Source

```bash
git clone https://github.com/parzival-hub/PyAutoEnum.git
cd PyAutoEnum
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Using pip (when available)

```bash
pip install pyautoenum
```

## Usage

```bash
# Basic usage
pyautoenum -t target.example.com

# Specify output directory
pyautoenum -t 192.168.1.100 --path /path/to/output

# Start a new session (ignore saved data)
pyautoenum -t target.example.com -n
```

## Adding Custom Modules

Custom modules can be added by creating a new module in the `modules.yml` file or by implementing Python functions in the modules directory.

Example module definition:

```yaml
- name: custom_module
  description: My custom module
  command: my_custom_function
  protocols:
    - http
    - https
  requires:
    - port
  analyse_function: analyse_custom_module
```

## TODOs

- Page scraper for users and wordlist generation with only one page scrape combined
- Implement more attack modules
- Add reporting functionality
- Improve UI with more interactive features
- Add host discovery for subnet scanning

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
