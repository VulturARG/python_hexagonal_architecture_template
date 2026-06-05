# Python Hexagonal Architecture Template

A production-ready Python template implementing the Hexagonal Architecture (Ports and Adapters) pattern. Use it as the starting point for any Python application that requires a strict separation between domain logic, use cases, and infrastructure concerns.

---

## Requirements

- Python 3.10+
- pip / venv

---

## Directory Structure

```
src/
├── domain/             # Core domain model — entities, DTOs, enums, exceptions
│   ├── entities/       # BaseEntity and shared base entity classes
│   ├── enums/          # Shared domain enumerations
│   ├── dtos/           # BaseDTO and Data Transfer Objects
│   ├── exceptions/     # BaseSrcError hierarchy + per-grouping error files
│   │   └── decorators/ # @generic_error_handler
│   └── tests/          # Domain unit tests (pure Python, no infrastructure)
│       ├── dtos/
│       ├── entities/
│       └── exceptions/
│           └── decorators/
├── applications/       # Use cases — orchestrate domain logic through ports
└── infrastructure/     # Adapters, wirings, and infrastructure tests
    ├── adapters/       # Concrete implementations of domain ports
    ├── wirings/        # Dependency assembly (the only place adapters are instantiated)
    └── tests/
        └── test_doubles/  # Test wirings and fake adapters
```

---

## Dependency Flow

```
infrastructure  →  applications  →  domain
```

Each layer may only import from layers to its right:

| Layer | May import from |
|---|---|
| `src/domain/` | Standard library and other domain modules only |
| `src/applications/` | `src/domain/` |
| `src/infrastructure/` | All layers and external frameworks |

> All imports MUST use the `from x import y` form. Accessing attributes on an imported module (`import x; x.y()`) is forbidden.

---

## Error Handling

### Exception Hierarchy

All application exceptions inherit from `BaseSrcError`:

```
BaseSrcError(Exception)
├── SrcGenericError       — wraps unexpected infrastructure exceptions
├── SrcBaseWarning        — non-fatal warnings
├── SrcBaseNotAuthorized  — authorization failures
└── SrcBaseNotFound       — resource not found
```

Defined in `src/domain/exceptions/base_src_error.py`.

### Custom Exception Rules

- **Never** raise `BaseSrcError` or its base subclasses directly.
- Each domain grouping that raises errors MUST define its own file at `src/domain/exceptions/<grouping>_errors.py`.
- Custom exceptions MUST inherit from one of the four base types and use the grouping name as prefix:

```python
# src/domain/exceptions/user_errors.py
from src.domain.exceptions.base_src_error import SrcBaseNotFound

class UserNotFound(SrcBaseNotFound):
    MESSAGE = "The requested user does not exist."
```

### `@generic_error_handler` Decorator

Apply this decorator to every method on infrastructure adapters (`src/infrastructure/adapters/`). It enforces a consistent error boundary:

- Re-raises `SrcBaseWarning`, `SrcBaseNotAuthorized`, and `SrcBaseNotFound` as-is.
- Logs and re-raises any other `BaseSrcError`.
- Wraps unexpected `Exception` in `SrcGenericError` and re-raises.

```python
from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler

class UserDatabaseAdapter:
    @generic_error_handler
    def find_by_id(self, user_id: str) -> User:
        ...
```

---

## Running Tests

Tests use `unittest.TestCase` and run through the standard `unittest` discovery:

```bash
python -m unittest discover -s src
```

With coverage:

```bash
coverage run -m unittest discover -s src && coverage report
```

---

## Code Quality Setup

Install `pre-commit` and `ruff` in your **system Python** (not inside a container or virtualenv):

```bash
pip install pre-commit ruff
```

Register the hooks with git:

```bash
pre-commit install
```

Run all hooks manually against the full codebase:

```bash
pre-commit run --all-files
```

> `ruff` replaces `flake8`, `isort`, and `black` — linting, import sorting, and formatting in a single faster tool. Configuration lives in `ruff.toml`.
