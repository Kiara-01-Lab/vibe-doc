# Contributing to VibeDoc

Thank you for considering contributing to VibeDoc! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear title and description
- Steps to reproduce the issue
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or screenshots

### Suggesting Features

We love new ideas! Open an issue with:
- A clear description of the feature
- Why it would be useful
- Examples of how it would work

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/Kiara-01-Lab/vibe-doc.git
   cd vibe-doc
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Test your changes locally
   - Update documentation if needed

4. **Test your changes**
   ```bash
   # Test on a sample repository
   python src/autodoc.py
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Use conventional commits:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `refactor:` code refactoring
   - `test:` adding tests
   - `chore:` maintenance tasks

6. **Push and create a PR**
   ```bash
   git push origin feature/your-feature-name
   ```

   Then open a Pull Request on GitHub with:
   - Clear description of changes
   - Link to related issue (if applicable)
   - Screenshots/examples if relevant

## Development Setup

### Prerequisites

- Python 3.9+
- Git

### Local Development

1. Clone the repo:
   ```bash
   git clone https://github.com/Kiara-01-Lab/vibe-doc.git
   cd vibe-doc
   ```

2. Install dependencies:
   ```bash
   pip install anthropic
   ```

3. Set up your API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

4. Test on a sample repo:
   ```bash
   cd /path/to/test/repo
   python /path/to/vibe-doc/src/autodoc.py
   ```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

## Testing

Before submitting a PR:
- [ ] Test on at least one real repository
- [ ] Verify all 5 docs generate correctly
- [ ] Check for errors in console output
- [ ] Ensure no API keys are hardcoded

## Community Guidelines

- Be respectful and welcoming
- Help others learn
- Give constructive feedback
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)

## Questions?

- Open a [GitHub Discussion](https://github.com/Kiara-01-Lab/vibe-doc/discussions)
- Check existing [Issues](https://github.com/Kiara-01-Lab/vibe-doc/issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing!** 🎉
