# Instructions for GitHub Copilot AI Agent

### (Django Backend API Edition)

Welcome, Copilot! Follow these guidelines whenever you generate code or documentation for this repository. **Security comes first**, followed closely by maintainability and clarity.

---

## 1 · Security Is Paramount

### 1.1 Authentication & Token Lifecycle Management

* Use **JSON Web Tokens (JWT)** for stateless authentication (recommend **djangorestframework‑simplejwt**).
* **Access‑token lifetime:** **10 minutes**.
* **Refresh‑token lifetime:** **4 hours**.
* Always issue a **refresh token** together with the access token.

    * Enable **token rotation** and **blacklisting** to prevent replay attacks.
    * Couple refresh‑token reuse detection with IP / User‑Agent checks and forced logout.
* Store all secrets (JWT signing key, DB creds, third‑party keys) in **environment variables** or a **secrets manager**—never commit them to VCS.

### 1.2 Centralized Middleware / Authentication Class

* Implement a single **authentication class** (or extend `SimpleJWTAuthentication`) and apply it globally via **DRF’s `DEFAULT_AUTHENTICATION_CLASSES`**.
* Responsibilities:

  1. Read the `Authorization: Bearer <token>` header.
  2. Validate & decode the JWT.
  3. Attach the authenticated `request.user`.
  4. Reject missing, expired, or malformed tokens with **HTTP 401**.
* Keep authorization logic **outside** view functions; rely on **permission classes** (e.g. `IsAuthenticated`, role‑based permissions).

### 1.3 Input Validation & SQL Injection Prevention

* **Validate and sanitize** every external input: query params, body, headers, path variables.
* Use **DRF Serializers** or **Pydantic** to enforce:

  * Field types, max lengths, regex patterns.
  * Enumerated choices / whitelists where applicable.
* Never build SQL with string concatenation. Use the **Django ORM** or **parameterized queries** (`django.db.connection.cursor()` with placeholders).
* Escape/encode user‑supplied data in HTML templates (though APIs should default to JSON).

### 1.4 Other Mandatory Security Measures

| Concern            | Django‑Friendly Solution                                                    |
| ------------------ | --------------------------------------------------------------------------- |
| Rate‑limiting      | **DRF Throttle classes** (e.g. `UserRateThrottle`, `AnonRateThrottle`).     |
| Password hashing   | Default PBKDF2 is fine; optionally switch to **Argon2** (`django[argon2]`). |
| Transport security | Set `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, HSTS.         |
| CORS               | Use **django‑cors‑headers** with an explicit allow‑list.                    |
| Activity logging   | Log auth failures & suspicious traffic via **`logging`** or **Sentry**.     |

---

## 2 · Architecture & Patterns

### 2.1 Apps ≈ Feature Modules

Leverage Django’s native **app** concept to achieve modularity. Each domain (e.g. `auth`, `dashboard`) lives in its own app:

```
project_root/
  auth/
    __init__.py
    models.py
    views.py
    serializers.py
    urls.py
    permissions.py
    services/
      __init__.py
      token_service.py
    repositories/
      __init__.py
      user_repository.py
    tests/
  dashboard/
    ...
  project_root/settings/
  manage.py
```

*Shared, cross‑cutting utilities* go in a top‑level `common/` or `core/` package.

### 2.2 Repository & Service Layers (Clean Architecture)

* **Repositories** isolate data‑access logic (ORM queries, external DBs).
* **Services** contain business workflows and orchestrate multiple repositories / external APIs.
* Views (controllers) should be **thin**: parse request → invoke service → return response serializer.

### 2.3 Dependency Injection

While Django lacks built‑in DI, mimic it via **constructor injection** in services, or use a library such as **django‑injector** when tests need to swap implementations.

---

## 3 · Project Conventions

| Aspect                 | Convention                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------ |
| Code style             | **Black** + **isort** + **flake8** (pre‑commit hooks).                                           |
| Environment management | **`.env`** files parsed by **django‑environ** or **dynaconf**.                                   |
| Migrations             | Let Copilot generate them, but review: field types, indices, `on_delete` behaviours.             |
| Third‑party packages   | Prefer well‑maintained, actively updated libs; justify each addition in the PR description.      |
| Tests                  | **pytest‑django** with **factory‑boy** for fixtures; aim for 80 %+ cov.                          |
| Documentation          | Docstrings (Google style) + **auto‑generated API docs** via **drf‑spectacular** or **drf‑yasg**. |

---

## 4 · FAQ

* **Q:** *Can Copilot write migrations?*
  **A:** Yes, but reviewers must verify field definitions, indexes, and FK constraints.

* **Q:** *Where should business rules live?*
  **A:** In **services/**, not in views, serializers, or models.

* **Q:** *How do we version the API?*
  **A:** Prefix URLs (`/api/v1/…`) and lock serializer schemas; bump major version on breaking changes.

---

> **Remember:** *Security first*, **clean architecture** second, **feature speed** third. Let’s build something robust!
