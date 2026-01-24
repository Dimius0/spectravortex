text

---

### 📄 Содержимое для нового файла `CONTRIBUTING.md`

Создайте этот файл в корневой папке репозитория (`/spectravortex/CONTRIBUTING.md`).

```markdown
# Contributing to SpectraVortex

Thank you for your interest in contributing to SpectraVortex! This guide will help you get set up to make changes and submit improvements.

## 🏗️ Development Setup

1.  **Fork and clone** the repository to your local machine.
2.  **Navigate** into the project directory:
    ```bash
    cd spectravortex
    ```
3.  **Install dependencies in development mode**. We recommend using a virtual environment:
    ```bash
    # Create and activate a virtual environment (optional but recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

    # Install the package in development/editable mode
    pip install -e .
    ```
    This installs the project and its dependencies (`numpy`) and links your local code, so changes are reflected immediately.

## 🧪 Running Tests

We use `pytest` for testing. Once the project is installed in development mode, you can run the test suite from the project root:

```bash
pytest
To run a specific test file or test case:

bash
pytest tests/test_lexer.py
pytest tests/test_lexer.py::TestLexer::test_basic_tokens
Please ensure all tests pass before submitting a pull request.

🔍 Code Quality & Style
We aim to keep the code clean and consistent.

Formatting: We use the black code formatter. You can run it manually:

bash
black .
Linting: We use ruff for fast linting. You can check for common issues:

bash
ruff check .
(Note: The project maintainer will set up automated checks for these tools in the CI pipeline.)

🚀 Making Changes & Submitting a Pull Request (PR)
Create a feature branch for your work:

bash
git checkout -b feature/your-feature-name
Make your changes. Write clear commit messages.

Run tests to ensure you haven't broken anything.

Push your branch to your fork on GitHub.

Open a Pull Request (PR) from your branch to the main branch of the main SpectraVortex repository.

Describe your changes clearly in the PR description. Link to any related issues.

🎯 Finding Work
Check the GitHub Issues for open tasks.

Issues tagged with good first issue are specifically curated for new contributors.

You can also propose new features or improvements by opening a new issue for discussion first.

💬 Getting Help
If you have questions, feel free to:

Comment on the relevant GitHub issue.

(Future: Link to a discussion forum or chat channel can be added here).

Thank you for helping build the future of photonic programming!
