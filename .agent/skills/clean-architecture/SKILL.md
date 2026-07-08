---
name: clean-architecture
description: >
  LLM-first guide for Python clean hexagonal architecture. Covers layer boundaries,
  import invariants, naming conventions, error hierarchy, testing rules, and coding
  style. Load whenever reading, writing, or reviewing any file under src/.
triggers:
  - "src/"
  - use case
  - adapter
  - port
  - repository
  - dto
  - domain entity
  - hexagonal architecture
  - clean architecture
---

# Clean Hexagonal Architecture — Conventions

## 0. Runtime Requirements

- **Python version**: 3.10+
- `dict[str, T]`, `list[T]`, and other built-in generics are natively subscriptable at runtime (since Python 3.9).
- **PEP 604 Union Types**: Avoid the use of `Optional[Type]`. Use `Type | None` instead.
  - **Forbidden:**
    ```python
    def f(parameter: Optional[int]) -> Optional[str]:
    def f(parameter: Optional[int] = None) -> Optional[str] = None:
    ```
  - **Allowed:**
    ```python
    def f(parameter: int | None) -> str | None:
    def f(parameter: int | None = None) -> str | None = None:
    ```
- `from __future__ import annotations` (PEP 563) is optional — use it only when you need forward references. Do not add it defensively or habitually to every file.

---

## 1. Directory Structure

```
src/
├── domain/
│   ├── entities/                            # BaseEntity and shared base classes
│   ├── enums/                               # Shared domain enumerations
│   ├── dtos/                                # Data Transfer Objects (BaseDTO)
│   ├── exceptions/                          # Exception hierarchy
│   │   ├── base_src_error.py
│   │   ├── <grouping>_errors.py             # Per-entity error files
│   │   └── decorators/
│   │       └── generic_error_handler.py
│   ├── tests/                               # Domain unit tests
│   │   ├── dtos/
│   │   ├── entities/
│   │   └── exceptions/
│   │       └── decorators/
│   └── <entity_name>/                       # One folder per entity
│       ├── <port>.py    (only if needed)
│       └── <service>.py
├── application/
└── infrastructure/
    ├── adapters/
    │   └── <entity_name>/                   # Mirrors the domain entity folder name
    │       └── <adapter>.py
    ├── wirings/                             # Dependency assembly for use cases
    │   └── <use_case>_wiring.py
    └── tests/
        ├── test_<name>.py
        └── test_doubles/                    # Test wirings and infrastructure doubles
            └── <use_case>_wiring_for_test.py
```

**Standard skeleton folders** (always present):
- `domain/entities/` — `BaseEntity` and shared base entity classes.
- `domain/enums/` — shared domain enumerations.
- `domain/dtos/` — `BaseDTO` and Data Transfer Objects.
- `domain/exceptions/` — exception hierarchy.
- `infrastructure/wirings/` — dependency assembly (see Section 8).
- `infrastructure/tests/test_doubles/` — test wirings.

**Not in the default skeleton**: `config/`. Configuration and settings live in `infrastructure/wirings/` or are injected at the controller level.

**No default `services/` or `ports/` top-level folders** — they live inside each entity's folder, only when needed.

---

## 2. Core Concepts

### Use case

> The unit of logic representing a specific action the system must perform. It acts as the business orchestrator: it receives a request, coordinates the execution of one or more domain services, and returns a result.
>
> It must NOT contain business logic of its own. Its responsibility is to coordinate the execution flow, delegating all business logic to the domain services.

**Responsibilities:**

- Receive the input data.
- Invoke one or more domain services.
- Coordinate the execution order.
- Return the result.

**Must NOT:**

- Implement business rules.
- Access databases directly.
- Know about frameworks or infrastructure.

### Domain service

> Represents a business action or process that does not naturally belong to a single entity, or that requires collaboration between multiple domain entities.
>
> It also encapsulates business rules that need to access external resources through ports (interfaces), keeping the domain independent of any technology.

> **Naming note**: "Domain service" is a *role*, not a name suffix. Per Section 5, these classes use a descriptive name with **NO `Service` suffix** (e.g., `PasswordHasher`, `OrderProcessor`).

Ports are interfaces (typically abstract classes or protocols) injected through the service constructor.

A service's methods must receive only domain objects, their own DTOs, or primitive types. They must never depend on objects coming from frameworks, ORMs, HTTP controllers, GUIs, or other external technologies.

**Responsibilities:**

- Implement business rules.
- Coordinate domain entities.
- Use ports when infrastructure is needed.
- Keep technological independence.

**Must NOT:**

- Know about HTTP.
- Know about Odoo, Django, FastAPI, Flask, etc.
- Know about SQL or persistence details.

### Adapter

> The component responsible for translating data between an external technology and the format used by the domain.
>
> It fully isolates the business logic from frameworks, databases, APIs, external systems, or user interfaces.

It typically implements a port defined by the domain or the application layer.

An adapter can be, for example:

- a database repository;
- a REST client to an external API;
- an SMTP client;
- a message-queue producer (e.g., Kafka);
- a gateway to another system.

Its sole responsibility is to translate data and delegate the work to the domain.

> **Driven vs. driving**: The adapters modeled here are *driven* (secondary) adapters — they implement a domain port on the output side (database, external API, email, queue). The *driving* (primary) side — HTTP routes, CLI, message consumers that trigger a use case — belongs to the framework, which enters through the **Wiring** (Section 8) to build and invoke the use case, rather than being wired as a domain-port adapter.

**Responsibilities:**

- Implement a port.
- Convert external data into domain DTOs or entities.
- Convert domain responses into the format expected by the external system.

**Must NOT:**

- Contain business rules.
- Decide business processes.
- Alter the domain's functional behavior.

### Dependency flow

```
Framework
    │  builds & invokes the use case through its Wiring (Section 8)
    ▼
Use Case
    │  calls
    ▼
Domain Service ──── uses ────> Port (interface, defined by the domain)
    │                             ▲
    │ uses                        │ implements
    ▼                             │
Entities                 Infrastructure Adapter
```

Dependencies always point toward the domain. The domain never knows about adapters or frameworks. Entities are the innermost core and depend on nothing. The framework never calls an adapter or the domain directly: it goes through the **Wiring** (Section 8), which builds the fully assembled use case and hands it back to be invoked. The **use case is a thin orchestrator**: it only coordinates domain services and never touches ports or infrastructure directly. Ports are interfaces **defined by** the domain and **used by** domain services (never by use cases directly); infrastructure adapters **implement** them (dependency inversion). This keeps the business logic decoupled and lets you replace technologies without touching the core.

---

## 3. Import Invariants (STRICT — unidirectional)

| Layer | Allowed imports | Forbidden imports |
|---|---|---|
| `src/domain/` | stdlib (via `from x import y`), other domain modules | `src/applications/`, `src/infrastructure/`, external frameworks |
| `src/applications/` | `src/domain/` | `src/infrastructure/` |
| `src/infrastructure/` | all layers, external frameworks | — |

---

## 4. Import Style

Always import specific names, never the module itself. This applies to **all** modules including stdlib:

```python
# Wrong
import os
import unittest
import typing
file_path = os.path(...)

# Correct
from os import path
from unittest import TestCase
from typing import get_type_hints
file_path = path(...)
```

- **No local imports**: Never use imports inside functions or methods. All imports must be placed at the top of the file.
- **No wildcard imports**: Never use wildcard imports (`from <module> import *`).

---

## 5. Naming Conventions

### Language and readability

- All class names, method names, function names, variable names, and constants MUST be in English.
- All names MUST be self-explanatory (Clean Code). A name must communicate intent without needing a comment to explain it.
- **No abbreviations (MANDATORY)**: All identifiers — variables, parameters, functions, methods, classes, files, and modules — MUST use full, unabbreviated names. A reader must never need to decode a shorthand.
  - Wrong: `tb`, `msg`, `exc_msg`, `mgr`, `cfg`, `req`, `res`, `btn`, `usr`
  - Right: `traceback_frames`, `message`, `exception_message`, `manager`, `config`, `request`, `response`, `button`, `user`
  - Accepted Python idioms (not considered abbreviations): `cls` in `@classmethod`, `exc` in `except ... as exc:`, `args`/`kwargs` in variadic signatures, `i`/`j` as loop counters in tight numeric loops.

### Class suffixes

| Artifact | Suffix rule | Example |
|---|---|---|
| Use case | `UseCase` | `RegisterUserUseCase` |
| DB port (interface) | `Repository` — for database interactions only | `UserRepository`, `MyDatabaseRepository` |
| Non-DB port (interface) | `Port` — for all other external interactions | `NotificationPort`, `MyGatewayPort` |
| Domain service | Descriptive name — NO `Service` suffix | `PasswordHasher`, `OrderProcessor` |
| Infrastructure adapter | `Adapter` — derived from port name (see below) | `MyGatewayAdapter`, `MyDatabaseAdapter` |
| Data Transfer Object | `DTO` | `UserRegistrationDTO` |

### Port naming rules

- FORBIDDEN: `RepositoryPort` or `PortRepository` — never combine both words.
- FORBIDDEN: same name prefix for both a `Port` and a `Repository`.
  - Having `SomeClassPort` and `SomeClassRepository` in the same codebase is not allowed.
- A port is either a `Repository` (DB) or a `Port` (everything else) — never both.

```
# Correct
MyGatewayPort          # external API / service
MyDatabaseRepository   # database interaction

# Wrong
MyGatewayPortRepository
MyDatabaseRepositoryPort
```

### Adapter naming

Adapter names are derived by replacing the port suffix with `Adapter`:

```
MyGatewayPort          → MyGatewayAdapter
MyDatabaseRepository   → MyDatabaseAdapter
```

### File naming

- **One class per file** — with one explicit exception: files inside `src/domain/exceptions/` MAY contain multiple related exception classes (e.g., a base hierarchy or a group of domain-specific errors).
- Filename is `snake_case` matching the class `PascalCase`:
  - `RegisterUserUseCase` → `register_user_use_case.py`
  - `MyGatewayAdapter` → `my_gateway_adapter.py`
- Every file ends with exactly one blank line.

---

## 6. Error Handling

### Exception hierarchy (`src/domain/exceptions/base_src_error.py`)

```python
BaseSrcError(Exception)      # root — all custom exceptions inherit from here
├── SrcGenericError          # wraps unexpected exceptions from infrastructure
├── SrcBaseWarning           # non-fatal warnings
├── SrcBaseNotAuthorized     # authorization failures
└── SrcBaseNotFound          # entity/resource not found
```

### Domain-group errors

Each folder inside `src/domain/` is a domain grouping. Every grouping that needs to raise errors MUST define its own exception file inside `src/domain/exceptions/`, named after the grouping:

```
src/domain/exceptions/
├── base_src_error.py         # base types — do not raise directly
├── user_errors.py            # errors for src/domain/user/
├── order_errors.py           # errors for src/domain/order/
└── decorators/
    └── generic_error_handler.py
```

Each exception in those files MUST inherit from one of the base types in `base_src_error.py`:

```python
from src.domain.exceptions.base_src_error import SrcBaseNotFound, SrcBaseWarning


class UserNotFound(SrcBaseNotFound):
    """Raised when a user entity cannot be located."""


class UserAlreadyExists(SrcBaseWarning):
    """Raised when attempting to register a duplicate user."""
```

Rules:
- Raise the most specific exception available — never raise `BaseSrcError` directly.
- Exception class names MUST follow the domain grouping name as prefix (e.g., `User...`, `Order...`).
- The base types (`SrcGenericError`, `SrcBaseWarning`, `SrcBaseNotAuthorized`, `SrcBaseNotFound`) are ONLY used as parent classes, never raised directly.

### Rules by layer

`@generic_error_handler` is applied in **exactly one place**: the use case.

| Layer | Approach | `@generic_error_handler` |
|---|---|---|
| **Use case** (application orchestrator) | Decorate the use case's public entry method. It is the single error boundary that normalizes anything unexpected into the `BaseSrcError` hierarchy. | ✅ **MANDATORY — only here** |
| `src/domain/` (entities, domain services) | Raise domain-group-specific subclasses of `BaseSrcError`. | ❌ **NEVER** |
| `src/infrastructure/adapters/` | Raise domain-group-specific subclasses of `BaseSrcError` where meaningful; let any other exception propagate up to the use case boundary. | ❌ **NEVER** |

> **MANDATORY**: `@generic_error_handler` goes **only** on the use case's public method. It MUST NEVER be placed on a domain service, an entity, or an adapter. Domain services and adapters raise specific exceptions (or let them propagate); the use case is the single funnel where unexpected errors are caught and wrapped.

`@generic_error_handler` (from `src/domain/exceptions/decorators/generic_error_handler.py`), applied to the use case's public method:
- Re-raises `SrcBaseWarning`, `SrcBaseNotAuthorized`, `SrcBaseNotFound` as-is.
- Logs and re-raises any other `BaseSrcError`.
- Wraps unexpected `Exception` in `SrcGenericError` and re-raises.

```python
from src.domain.exceptions.decorators.generic_error_handler import generic_error_handler
from src.domain.user.user_registrar import UserRegistrar


class RegisterUserUseCase:
    def __init__(self, user_registrar: UserRegistrar) -> None:
        self._user_registrar = user_registrar

    @generic_error_handler
    def execute(self, registration: UserRegistrationDTO) -> None:
        self._user_registrar.register(registration)
```

Entry points (controllers, CLI) catch `BaseSrcError` subclasses and map them to delivery-specific formats (HTTP codes, CLI exit codes). Never let `BaseSrcError` propagate raw to the user.

---

## 7. Testing Rules

### Location and framework

`unittest.TestCase` is **MANDATORY** for all tests. No exceptions.

| Layer touched | Test path | Framework |
|---|---|---|
| `src/domain/` | `src/domain/tests/<topic>/test_<class>.py` | `unittest.TestCase` |
| `src/infrastructure/` | `src/infrastructure/tests/test_<name>.py` | `unittest.TestCase` |

Domain tests MUST run as pure Python — no real DB, no network. Test doubles (in-memory storage, fake adapters) are allowed.

The skeleton includes tests for its own base classes:

| Source file | Test file |
|---|---|
| `domain/dtos/base_dto.py` | `domain/tests/dtos/test_base_dto.py` |
| `domain/entities/base_entity.py` | `domain/tests/entities/test_base_entity.py` |
| `domain/exceptions/base_src_error.py` | `domain/tests/exceptions/test_base_src_error.py` |
| `domain/exceptions/decorators/generic_error_handler.py` | `domain/tests/exceptions/decorators/test_generic_error_handler.py` |

### Naming

- Test method names in **English**, self-documenting:
  - `test_returns_empty_list_when_no_players` ✓
  - `test_1` ✗
- No comments or docstrings inside test bodies.

### Style

```python
from unittest import TestCase

from src.domain.exceptions.base_src_error import BaseSrcError, SrcBaseNotFound


class TestSrcBaseNotFound(TestCase):
    def test_is_subclass_of_base_src_error(self):
        self.assertTrue(issubclass(SrcBaseNotFound, BaseSrcError))

    def test_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SrcBaseNotFound()
```

---

## 8. Wirings

A wiring assembles all the dependencies a use case needs. It is the only place where concrete adapters are instantiated and injected.

### File location and naming

- Production wiring: `src/infrastructure/wirings/<use_case>_wiring.py`
- Test wiring: `src/infrastructure/tests/test_doubles/<use_case>_wiring_for_test.py`
- Filename is `snake_case` matching the class `PascalCase`: `RegisterUserUseCaseWiring` → `register_user_use_case_wiring.py`

### Structure

```python
from src.application.register_user_use_case import RegisterUserUseCase
from src.domain.user.user_registrar import UserRegistrar
from src.domain.user.user_repository import UserRepository
from src.infrastructure.adapters.user.postgres_user_adapter import PostgresUserAdapter


class RegisterUserUseCaseWiring:
  def get_register_user_use_case(self) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_registrar=self._user_registrar())

  def _user_registrar(self) -> UserRegistrar:
    return UserRegistrar(user_repository=self._user_repository())

  def _user_repository(self) -> UserRepository:
    return PostgresUserAdapter()
```

Rules:
- One public method that returns the fully assembled use case. Named `get_<use_case_snake_case>()`.
- One private method per dependency (`_<dependency_name>()`), named after what it builds.
- Assemble the chain **port → domain service → use case**: the use case receives domain services, and each domain service receives the ports it needs. Never inject a port directly into a use case.
- Methods that build an **adapter** return the **port type** (interface), not the concrete adapter. Methods that build a **domain service** return the concrete service type.
- The wiring class has no business logic — only object creation and wiring.
- Constructor parameters (`__init__`) are allowed only for runtime values (e.g., timestamps, config) that cannot be resolved statically.

### Test wiring

`WiringForTest` inherits from the production wiring and overrides only the infrastructure methods that need test doubles:

```python
from src.domain.user.user_repository import UserRepository
from src.infrastructure.tests.test_doubles.in_memory_user_adapter import InMemoryUserAdapter
from src.infrastructure.wirings.register_user_use_case_wiring import RegisterUserUseCaseWiring


class RegisterUserUseCaseWiringForTest(RegisterUserUseCaseWiring):
    def _user_repository(self) -> UserRepository:
        return InMemoryUserAdapter()
```

This pattern isolates the test from the database while reusing the full wiring structure.

---

## 9. Other Rules

- No `print()` for debugging.
- Do not write inline comments (`#`) in production code. Names and structure must be self-explanatory.
- Docstrings are documentation, not comments — they ARE required on public classes and methods. Follow PEP 257. Prefer single-line form:
  ```python
  def as_dict(self) -> dict[str, Any]:
      """Return the entity as a plain dictionary."""
  ```
- Do not delete existing docstrings or comments without an explicit decision.
