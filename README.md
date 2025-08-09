# PIF Backend 2

This project is a Django backend initialized with a virtual environment and Django installed.

## Getting Started

1. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
2. Run the development server:
   ```powershell
   & ".venv\Scripts\python.exe" manage.py runserver
   ```

## Project Structure
- `pif_project/`: Django project directory
- `manage.py`: Django management script

## Useful Commands
- Make migrations: `& ".venv\Scripts\python.exe" manage.py makemigrations`
- Migrate: `& ".venv\Scripts\python.exe" manage.py migrate`
- Create app: `& ".venv\Scripts\python.exe" manage.py startapp <appname>`
