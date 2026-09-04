# Contributing to BioPAT® Spectro UV Server

Thank you for your interest in contributing! This project welcomes bug reports, feature requests, documentation improvements, and code contributions.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Code Style](#code-style)
- [Commit Message Convention](#commit-message-convention)

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) Code of Conduct. By participating you agree to abide by its terms.

---

## Reporting Bugs

Please open a [GitHub Issue](https://github.com/Sir-Narwhal/biopat-spectrouv-server/issues) and include:

- **Environment**: OS, Python version, Docker version, spectrometer model (if applicable)
- **Steps to reproduce** the problem
- **Expected behaviour** vs **actual behaviour**
- Relevant log output (redact any sensitive data)

---

## Suggesting Features

Open a GitHub Issue with the label enhancement. Describe:

1. The problem or use case you are trying to solve
2. Your proposed solution
3. Any alternatives you considered

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Docker & Docker Compose (for integration testing)
- Git

### Clone & install dependencies

```bash
git clone <https://github.com/Sir-Narwhal/biopat-spectrouv-server.git>
cd biopat-spectrouv-server

# Create a virtual environment

python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# Install runtime dependencies

pip install -r requirements.txt

# Install development dependencies (pytest)

pip install -r requirements-dev.txt
```

---

## Running Tests

The test suite uses **pytest** and requires no external services (no Redis, no hardware).

```bash
pytest tests/ -v
```

All tests must pass before a pull request can be merged. The CI pipeline runs
the suite against Python 3.10, 3.11, and 3.12 automatically on every push and PR.

### Test structure

| File | What it tests |
|---|---|
| tests/test_mock_emitter.py | build_tec5_packet() — binary packet construction, header fields, per-type value behaviour |
| tests/test_udp_parser.py | unpack_udp() — round-trip parsing, spectral physics, wavelength metadata |

---

## Submitting a Pull Request

1. **Fork** the repository and create a feature branch off main:
   ```bash
   git checkout -b feat/my-feature
   ```

2. Make your changes, following the [code style](#code-style) guidelines.

3. **Add or update tests** for any new behaviour. PRs that reduce test coverage will not be merged.

4. Run the full test suite locally and confirm all tests pass.

5. Update CHANGELOG.md under [Unreleased] with a concise description of your change.

6. **Push** your branch and open a Pull Request against main. Fill in the PR template.

7. A maintainer will review your PR. Please be responsive to review feedback.

---

## Code Style

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/). Maximum line length is **100 characters**.
- **Type hints**: Use type hints on all new public functions and methods.
- **Docstrings**: Use plain docstrings (Google or reStructuredText style) for all public functions.
- **Imports**: Standard library first, then third-party, then local — separated by blank lines.
- **No bare except:** — always catch specific exception types.

Optionally, format your code with [black](https://black.readthedocs.io/) and lint with [ruff](https://docs.astral.sh/ruff/) before committing.

---

## Commit Message Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>

[optional body]
```

Common types:

| Type | When to use |
| --- | --- |
| feat | New feature |
| fix | Bug fix |
| docs | Documentation changes only |
| test | Adding or correcting tests |
| refactor | Code change that is not a fix or feature |
| chore | Tooling, CI, dependency updates |

Example:

```
feat(udp-parser): add support for dual-channel simultaneous ingestion

Extends collect_mpt_spectra to process channel_2 datagrams in the
same batch loop, reducing latency for dual-spectrometer setups.
```

---

## Questions?

Open an issue or start a [GitHub Discussion](https://github.com/Sir-Narwhal/biopat-spectrouv-server/discussions) — we are happy to help.
