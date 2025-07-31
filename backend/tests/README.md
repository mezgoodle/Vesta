# FastAPI Testing Suite

This directory contains comprehensive tests for the Vesta FastAPI application.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_main.py               # Tests for main application endpoints
├── test_auth.py               # Tests for authentication endpoints
├── test_items.py              # Tests for items endpoints
├── test_users.py              # Tests for users endpoints
├── test_integration.py        # Integration tests
└── test_performance.py        # Performance and load tests
```

## Test Categories

### 🔧 **Unit Tests**

- **test_main.py**: Root endpoints, health checks, API info
- **test_auth.py**: Authentication functionality (login, register, logout, profile)
- **test_items.py**: Items CRUD operations
- **test_users.py**: Users CRUD operations

### 🔗 **Integration Tests**

- **test_integration.py**: End-to-end workflows, API accessibility, error handling

### ⚡ **Performance Tests**

- **test_performance.py**: Response time, concurrent requests, large payload handling

## Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-asyncio coverage
```

## Running Tests with pytest

### Basic Commands

**Run all tests:**

```bash
pytest
```

**Run all tests with verbose output:**

```bash
pytest -v
```

**Run all tests with coverage:**

```bash
pytest --cov=app --cov=main --cov-report=html --cov-report=term-missing
```

### Running Specific Test Files

**Run authentication tests:**

```bash
pytest tests/test_auth.py
```

**Run items tests:**

```bash
pytest tests/test_items.py
```

**Run users tests:**

```bash
pytest tests/test_users.py
```

**Run main application tests:**

```bash
pytest tests/test_main.py
```

**Run integration tests:**

```bash
pytest tests/test_integration.py
```

**Run performance tests:**

```bash
pytest tests/test_performance.py
```

### Running Tests by Category (using markers)

**Run only unit tests (exclude integration and performance):**

```bash
pytest -m "not integration and not performance"
```

**Run only integration tests:**

```bash
pytest -m integration
```

**Run only performance tests:**

```bash
pytest -m performance
```

**Exclude slow tests:**

```bash
pytest -m "not slow"
```

### Advanced pytest Options

**Run with extra verbosity and show local variables:**

```bash
pytest -vv -l
```

**Run tests and stop on first failure:**

```bash
pytest -x
```

**Run tests with detailed output on failures:**

```bash
pytest --tb=long
```

**Run specific test methods:**

```bash
pytest tests/test_auth.py::TestAuthEndpoints::test_login_endpoint
```

**Run tests matching a pattern:**

```bash
pytest -k "login"              # Run tests with 'login' in the name
pytest -k "auth and not logout" # Run auth tests except logout
```

**Run tests in parallel (if pytest-xdist is installed):**

```bash
pip install pytest-xdist
pytest -n auto                # Use all available cores
pytest -n 4                   # Use 4 cores
```

### Coverage Reports

**Generate HTML coverage report:**

```bash
pytest --cov=app --cov=main --cov-report=html
```

**Generate terminal coverage report:**

```bash
pytest --cov=app --cov=main --cov-report=term-missing
```

**Generate both HTML and terminal reports:**

```bash
pytest --cov=app --cov=main --cov-report=html --cov-report=term-missing
```

**View coverage report:**

- HTML report: Open `htmlcov/index.html` in your browser
- Terminal report: Shows missing lines directly in terminal

### Debugging Tests

**Run with Python debugger:**

```bash
pytest --pdb                   # Drop into debugger on failures
pytest --pdbcls=ipdb.debugger  # Use ipdb if installed
```

**Run with print statements visible:**

```bash
pytest -s                     # Don't capture output
```

**Run with extra debugging info:**

```bash
pytest --tb=long -vv -s
```

## Test Fixtures

The `conftest.py` file provides several useful fixtures:

- **`client`**: FastAPI test client for making HTTP requests
- **`sample_item_data`**: Sample data for item testing
- **`sample_user_data`**: Sample data for user testing
- **`sample_credentials`**: Sample login credentials

## Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow-running tests

**Run tests by marker:**

```bash
pytest -m integration           # Only integration tests
pytest -m "not performance"     # Exclude performance tests
pytest -m "slow"               # Only slow tests
```

## Writing New Tests

### Test Class Structure

```python
class TestNewFeature:
    """Test class for new feature."""

    def test_feature_functionality(self, client: TestClient):
        """Test description."""
        response = client.get("/api/v1/new-endpoint")
        assert response.status_code == 200
        data = response.json()
        assert "expected_field" in data
```

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Test both positive and negative cases**
4. **Use fixtures for common test data**
5. **Keep tests independent** - each test should be able to run alone
6. **Mock external dependencies** when necessary

## Continuous Integration

The test suite is designed to work with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov=main --cov-report=xml
```

## Test Data

Tests use sample data defined in fixtures:

- **Items**: Name, description, price
- **Users**: Username, email, password
- **Credentials**: Username, password for authentication

All test data is designed to be realistic but safe for testing environments.

## Troubleshooting

**Common issues:**

1. **Import errors**: Ensure you're running tests from the backend directory
2. **Missing dependencies**: Run `pip install -r requirements.txt`
3. **Port conflicts**: Tests use TestClient, so no actual server ports are used
4. **Path issues**: Use absolute imports in your application code

**Debug failing tests:**

```bash
pytest tests/test_failing.py -v -s --tb=long
```

## Performance Benchmarks

Current performance targets:

- **Response time**: < 1 second for standard endpoints
- **Concurrent requests**: Handle 10 simultaneous requests
- **Large payloads**: Process 10KB+ payloads within 2 seconds

Run performance tests regularly to ensure these benchmarks are met:

```bash
pytest tests/test_performance.py -v
```

## Common pytest Commands Cheat Sheet

```bash
# Basic usage
pytest                                    # Run all tests
pytest -v                                # Verbose output
pytest -q                                # Quiet output
pytest -x                                # Stop on first failure

# File/directory selection
pytest tests/                            # Run tests in directory
pytest tests/test_auth.py                # Run specific file
pytest tests/test_auth.py::TestAuthEndpoints  # Run specific class
pytest tests/test_auth.py::TestAuthEndpoints::test_login  # Run specific test

# Filtering
pytest -k "auth"                         # Run tests matching pattern
pytest -m "integration"                  # Run tests with marker
pytest -m "not slow"                     # Exclude tests with marker

# Output and debugging
pytest -s                                # Show print statements
pytest --tb=short                        # Short traceback format
pytest --tb=long                         # Long traceback format
pytest --pdb                             # Drop into debugger on failure

# Coverage
pytest --cov=app                         # Run with coverage
pytest --cov=app --cov-report=html       # Generate HTML report
pytest --cov=app --cov-report=term-missing  # Show missing lines

# Parallel execution (requires pytest-xdist)
pytest -n auto                           # Use all CPU cores
pytest -n 4                              # Use 4 workers
```
