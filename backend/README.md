# Vesta Backend

This is the backend service for the Vesta Smart Home Assistant, built with FastAPI.

## Prerequisites

- Python 3.8+
- pip

## Installation

1.  **Navigate to the backend directory:**

    ```bash
    cd backend
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    -   **Windows:**
        ```powershell
        .\venv\Scripts\Activate
        ```
    -   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Set up environment variables:**

    Copy the `.env.example` file to a new file named `.env`:

    ```bash
    cp .env.example .env
    ```

    *Note: On Windows PowerShell, use `copy .env.example .env`*

2.  **Edit `.env`:**

    Open the `.env` file and fill in the required values:

    ```env
    OPENAI_API_KEY=your_openai_api_key
    HOME_ASSISTANT_URL=http://homeassistant.local:8123
    HOME_ASSISTANT_TOKEN=your_long_lived_access_token
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    ```

## Running the Server

Start the development server using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Documentation

Once the server is running, you can access the interactive API documentation at:

-   **Swagger UI:** `http://127.0.0.1:8000/docs`
-   **ReDoc:** `http://127.0.0.1:8000/redoc`

## Project Structure

-   `app/`: Main application package.
    -   `core/`: Core configuration and settings.
    -   `services/`: Business logic and external service integrations (LLM, Home Assistant).
    -   `main.py`: Application entry point.
-   `requirements.txt`: Python dependencies.
-   `.env.example`: Template for environment variables.
