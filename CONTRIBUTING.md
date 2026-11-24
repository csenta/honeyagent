# Contributing to HoneyAgent

We welcome contributions to HoneyAgent.

## Development Workflow

1. Fork and clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the test suite before submitting pull requests:
   ```bash
   PYTHONPATH=. python3 -m unittest discover -s tests -v
   ```
4. Follow PEP 8 style guidelines and ensure complete type hints and modular error handling.
