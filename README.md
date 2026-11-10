# Rydeon - Vehicle Rental System

A fast, reliable, database-connected vehicle rental web application built for a university mini-project.

---

## 📌 Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 (CDN)
- **Backend**: Python 3.12+ / Flask (Application Factory & Modular Blueprints)
- **Database**: MySQL 8.0+
- **Database Connector**: `mysql-connector-python` (Official Oracle driver with connection pooling)
- **Development Environment**: Windows 10 / 11 (PowerShell & Command Prompt compatible)

---

## 🏛️ Project Architecture & Directory Structure

The project follows a clean, modular Flask architecture separating presentation (templates & static), routing (blueprints), business logic (services), and data persistence (database layer).

```
Rydeon/
├── app/
│   ├── __init__.py           # Application factory (create_app), extensions, blueprint registration
│   ├── routes/               # Modular Flask Blueprints (auth, vehicles, bookings, admin)
│   ├── templates/            # Jinja2 HTML5 templates with Bootstrap 5
│   │   ├── base.html         # Base template (navbar, footer, flash alerts, Bootstrap CDN)
│   │   ├── auth/             # Login, registration, profile templates
│   │   ├── vehicles/         # Vehicle catalogue, details, search/filter
│   │   ├── bookings/         # Booking form, confirmation, user booking history
│   │   └── admin/            # Admin dashboard, fleet management, reservation approvals
│   ├── static/               # Static assets
│   │   ├── css/              # Custom stylesheets (style.css)
│   │   ├── js/               # Client-side scripts & form validations (main.js)
│   │   └── images/           # UI icons, branding logos, vehicle placeholders
│   ├── services/             # Business logic layer (authentication, booking calculation, validation)
│   └── database/             # Database connection pool manager (db.py) and schema DDL (schema.sql)
├── uploads/                  # Uploaded vehicle photos and documents (gitignored)
├── config/                   # Configuration management classes (Development, Testing, Production)
├── tests/                    # Pytest test cases (unit and integration tests)
├── run.py                    # Application launch entry point
├── requirements.txt          # Python dependencies specification
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusions (credentials, virtualenv, cache, uploads)
└── README.md                 # Project documentation and setup guide
```

### Architectural Notes
- **Direct Workspace Root**: The project root `Rydeon/` contains the application modules directly rather than inside an extra nested folder. This simplifies execution (`python run.py`), path resolution, and virtual environment isolation.
- **Application Factory Pattern**: `create_app()` initializes Flask configurations and registers blueprints cleanly.
- **Service Layer**: Route handlers delegate business logic (e.g., date conflicts, pricing computation) to `services/`, keeping routes concise and testable.
- **Database Access Layer**: `database/db.py` manages a pooled connection to MySQL using `mysql-connector-python`, avoiding overhead and dangling connections.

---

## ⚙️ Prerequisites

Ensure the following software is installed on your Windows system:
1. **Python 3.10+** (Python 3.12+ recommended; verify via `python --version`)
2. **Git** (verify via `git --version`)
3. **MySQL Server 8.0+** running as a Windows service (`MySQL80`)

---

## 🚀 Installation & Setup Instructions

Follow these step-by-step instructions in Windows PowerShell or CMD:

### 1. Clone or Open the Repository
```powershell
cd "c:\Users\Mohommed Adil\Desktop\Projects\SDD\Rydeon"
```

### 2. Create a Virtual Environment
Isolate project dependencies by creating a Python virtual environment:
```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment
- **In PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(Note: If script execution is blocked on Windows PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **In Command Prompt (cmd.exe)**:
  ```cmd
  .\.venv\Scripts\activate.bat
  ```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy the template configuration file:
```powershell
Copy-Item .env.example .env
```
Open `.env` in your text editor and update:
- `SECRET_KEY`: A secure random string for session signing.
- `DB_USER`: Your MySQL username (default: `root`).
- `DB_PASSWORD`: Your MySQL password.
- `DB_NAME`: Database name (e.g., `vehicle_rental_db`).

> ⚠️ **IMPORTANT**: Never commit `.env` to Git. It is already added to `.gitignore`.

### 6. Initialize Database (Phase 2)
The database schema (`schema.sql`) and sample seed data will be created and executed in subsequent phases.

### 7. Run the Application
```powershell
python run.py
```
By default, the development server will run at:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔍 Dependencies & Environment Analysis

| Package | Version | Purpose |
|---|---|---|
| `Flask` | `>=3.0.3` | Lightweight, modular WSGI web application framework. |
| `Werkzeug` | `>=3.0.3` | WSGI utility library handling secure password hashing and request parsing. |
| `mysql-connector-python` | `>=9.0.0` | Official Oracle MySQL driver providing native connection pooling. |
| `python-dotenv` | `>=1.0.1` | Loads configuration and sensitive secrets from `.env` into `os.environ`. |
| `pytest` | `>=8.3.0` | Testing framework for running test suites. |

### Identified Environment Considerations & Solutions
1. **Windows PowerShell Execution Policy**:
   - *Issue*: PowerShell may prevent running `.venv\Scripts\Activate.ps1` with an `Execution_Policies` restriction.
   - *Solution*: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the current terminal session, or invoke Python directly via `.\.venv\Scripts\python.exe`.

2. **MySQL 8.0 Authentication (`caching_sha2_password`)**:
   - *Issue*: Older MySQL Python libraries (e.g., `MySQLdb`, legacy `PyMySQL` configs) sometimes fail with MySQL 8's default authentication plugin.
   - *Solution*: Using official `mysql-connector-python>=9.0.0` natively supports `caching_sha2_password` without needing to downgrade user passwords to `mysql_native_password`.

3. **File Path Handling across Windows**:
   - *Issue*: Windows uses backslashes `\` whereas URLs and Unix environments use `/`. Hardcoding path separators can cause broken image links.
   - *Solution*: Use Python's `os.path.join` or `pathlib.Path` for filesystem operations, and Flask's `url_for('static', filename=...)` for templates.

4. **Security & Secrets**:
   - `.env` is excluded in `.gitignore` to prevent leaking credentials in university git repositories.

---

## 📋 Project Roadmap

- [x] **Phase 1**: Workspace setup, architecture design, directory structure, environment configuration, dependency management.
- [ ] **Phase 2**: Configuration loading, MySQL database schema, connection pool manager, migrations/seed data.
- [ ] **Phase 3**: Core backend models, service layer, authentication blueprint (Customer & Admin).
- [ ] **Phase 4**: Vehicle catalog, filtering, dynamic search, and detail views.
- [ ] **Phase 5**: Rental booking workflow, date conflict checks, pricing calculation, reservation status.
- [ ] **Phase 6**: Admin dashboard, fleet management (CRUD), booking management.
- [ ] **Phase 7**: Frontend refinement with Bootstrap 5, responsive design, validation, end-to-end testing.
