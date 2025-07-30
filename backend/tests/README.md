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

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-asyncio coverage
```

Or use the PowerShell script:

```powershell
.\run_tests.ps1 -Install
```

### Basic Usage

**Run all tests:**

```bash
python run_tests.py
# or
.\run_tests.ps1
```

**Run specific test categories:**

```bash
python run_tests.py unit          # Unit tests only
python run_tests.py integration   # Integration tests only
python run_tests.py performance   # Performance tests only
```

**Run specific test files:**

```bash
python run_tests.py auth          # Authentication tests
python run_tests.py items         # Items tests
python run_tests.py users         # Users tests
python run_tests.py main          # Main app tests
```

### Advanced Options

**Run with verbose output:**

```bash
python run_tests.py all -v
# or
.\run_tests.ps1 -Verbose
```

**Run without coverage:**

```bash
python run_tests.py all --no-coverage
# or
.\run_tests.ps1 -NoCoverage
```

**Using pytest directly:**

```bash
pytest tests/ -v                           # All tests, verbose
pytest tests/test_auth.py -v              # Specific file
pytest -m "not performance" -v            # Exclude performance tests
pytest --cov=app --cov-report=html        # With coverage report
```

## Test Fixtures

The `conftest.py` file provides several useful fixtures:

- **`client`**: FastAPI test client for making HTTP requests
- **`sample_item_data`**: Sample data for item testing
- **`sample_user_data`**: Sample data for user testing
- **`sample_credentials`**: Sample login credentials

## Coverage Reports

Test coverage reports are generated in the `htmlcov/` directory when running with coverage enabled (default).

**View coverage report:**

- Open `htmlcov/index.html` in your browser
- Or use PowerShell script prompt to open automatically

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
    python run_tests.py all
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

Run performance tests regularly to ensure these benchmarks are met.
