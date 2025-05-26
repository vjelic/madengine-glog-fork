# Contributing to madengine Library

Thank you for your interest in contributing to our madengine library! We welcome all contributions, whether they are bug fixes, new features, or improvements to documentation. Please follow the steps below to get started:

## Getting started

1. Fork the Repository: Start by forking the repository on GitHub to your own account.

2. Clone the Repository: Clone your forked repository to your local machine:

```shell
git clone https://github.com/ROCm/madengine.git
cd madengine
```

3. Create a Branch: Create a new branch for your changes:

```shell
git checkout -b feature-or-bugfix-name
```

4. Install Dependencies: Install madengine and required dependencies using `pip`:

```shell
pip install -e .[dev]
```

## Making changes

1. Implement Your Changes: Make your changes or add new features in the appropriate files.

2. Write Tests: Ensure that you write tests for your changes. Place your test files in the `tests` directory.

## Validating changes with `pytest`

1. Install `pytest`: If you haven't already, install `pytest`:

```shell
pip install pytest
```

2. Run Tests: Run the tests to validate your changes:

```shell
pytest
```

3. Check Test Results: Ensure all tests pass. If any tests fail, debug and fix the issues.

## Submitting your changes

1. Commit Your Changes: Commit your changes with a meaningful commit message:

```shell
git add .
git commit -m "Description of your changes"
```

2. Push to GitHub: Push your changes to your forked repository:

```shell
git push origin feature-or-bugfix-name
```

3. Create a Pull Request: Go to the original repository on GitHub and create a pull request from your forked repository. Provide a clear description of your changes and any relevant information.

## Review process

Your pull request will be reviewed by the maintainers. They may request changes or provide feedback. Once your pull request is approved, it will be merged into the main branch.

Thank you for your contribution!
