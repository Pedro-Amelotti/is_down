# Status Monitor

This is a Django application to monitor the status of websites.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd status_monitor
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install django requests
    ```

4.  **Run the database migrations:**
    ```bash
    python manage.py migrate
    ```

## Running the server

To start the development server, run:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`.
