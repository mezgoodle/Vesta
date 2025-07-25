# Vesta Backend

This is the backend service for the Vesta project, built with FastAPI.

## Features

- FastAPI framework for high-performance API development
- CORS middleware for cross-origin requests
- Health check endpoint
- Auto-generated API documentation

## Installation

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

```bash
# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

To start the development server:

```bash
fastapi dev main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- **API**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint

## Development

The application includes:

- Automatic API documentation generation
- CORS support for frontend integration
- Hot reload during development
- Type hints and validation with Pydantic
