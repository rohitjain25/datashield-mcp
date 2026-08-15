# Contributing to DataShield MCP

We love contributions! Here's how you can help.

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/datashield-mcp.git
cd datashield-mcp

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre‑commit hooks (optional)
pre-commit install
```

## Code Style

We follow PEP 8 with Black formatting. Run `black .` to format code.

## Running Tests

```bash
pytest
```

## Documentation

Keep `README.md` and the `docs/` directory up to date with your changes.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Open an issue or reach out to the maintainers.