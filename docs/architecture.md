
# EduFlow Architecture

> Short note (RU):  
> Этот документ описывает архитектуру проекта **EduFlow** (финальный проект по курсу *Highload Backend*): основные компоненты, их взаимодействие, потоки данных, аутентификацию, кэш, фоновые задачи и точки роста по масштабированию.

---

## 1. High-Level Overview

EduFlow is a backend for an online learning platform.  
It is designed as a **monolithic Django application** with a few highload-oriented components:

- Django + DRF as the main API layer.
- PostgreSQL as the primary relational database.
- Redis as:
  - cache backend for popular read endpoints,
  - message broker + result backend for Celery.
- Celery worker for background processing.
- JWT-based authentication with role-based access control.
- Structured JSON logging for observability.

At runtime, the system is typically deployed via **Docker Compose**:

- `web`  – Django / DRF API service  
- `db`   – PostgreSQL database  
- `redis` – Redis cache and Celery broker  
- `celery` – Celery worker

---

## 2. Component Diagram

### 2.1 Logical Architecture

```text
                   ┌────────────────────────────────┐
                   │            Clients             │
                   │  Web / Mobile / API consumers  │
                   └───────────────┬────────────────┘
                                   │ HTTP (REST, JWT)
                                   ▼
                        ┌────────────────────┐
                        │    Django + DRF    │
                        │   "web" container  │
                        └─────────┬──────────┘
                                  │
                     ┌────────────┼───────────────┐
                     │            │               │
                     ▼            ▼               ▼
              ┌───────────┐ ┌───────────┐ ┌──────────────┐
              │PostgreSQL │ │   Redis   │ │  Celery      │
              │   "db"    │ │  "redis"  │ │  worker      │
              └───────────┘ └───────────┘ └──────────────┘
                 (main DB)   (cache +       (background
                              broker)        tasks)
````

---

## 3. Django Application Structure

The Django project is organized into several apps and common modules:

* `config/`

  * `settings.py` – base configuration, database, cache, logging, DRF, SimpleJWT.
  * `urls.py` – main URL routing (auth, courses, API docs).
  * `celery.py` – Celery application configuration.

* `users/`

  * `models.py` – custom `User` model (`username`, `email`, `role`).
  * `serializers.py` – `RegisterSerializer`, `ProfileSerializer` with validation.
  * `views.py` – registration + profile API.
  * `urls.py` – auth endpoints (`register`, `login`, `refresh`, `me`).

* `courses/`

  * `models.py` – `Course`, `Lesson`, `Enrollment`.
  * `serializers.py` – API serializers for the above models.
  * `views.py` – `CourseViewSet`, `LessonViewSet`, `EnrollmentViewSet`, `CourseListView`.
  * `permissions.py` – object-level RBAC for courses.

* `common/`

  * `logging.py` – JSON logger, request ID, loggers configuration.
  * `middleware.py` – access logs (request method, path, status, user, latency).
  * `exceptions.py` – RFC7807 error handler.
  * `tasks.py` – Celery tasks (email, reports, cleanup).

---

## 4. Authentication & RBAC

### 4.1 User Model & Roles

The system uses a custom `User` model based on `AbstractUser` with an additional `role` field:

* `admin`
* `instructor`
* `student`

This allows for **role-based access control (RBAC)** at the API layer.

### 4.2 JWT Authentication

Authentication is handled via **SimpleJWT**:

* `POST /api/v1/auth/login/` → returns `access` + `refresh` tokens.
* `POST /api/v1/auth/refresh/` → returns new `access` token.
* Tokens are expected in the `Authorization: Bearer <token>` header.

The `access` token is used to:

* identify the user in DRF,
* check role (`user.role`) in viewsets,
* enforce access logic.

---

## 5. Domain Model & CRUD Flows

### 5.1 Main Entities

* `User` – application user, with role.
* `Course` – course created by an instructor.
* `Lesson` – lesson belonging to a course.
* `Enrollment` – relation between `student` and `course`.

### 5.2 Typical Flows

#### 5.2.1 Viewing Courses

1. Client calls:

   * `GET /api/v1/courses-public/` (public list) or
   * `GET /api/v1/courses/` (role-aware list).
2. Django / DRF builds a queryset:

   * only `is_published=True` for students/anonymous,
   * all courses for admin/instructor.
3. Optional: response may be served from Redis cache.

#### 5.2.2 Creating a Course

1. Authenticated user (`admin` or `instructor`) calls:

   * `POST /api/v1/courses/`.
2. `CourseViewSet` checks role, saves `owner=user`.
3. Cache for course lists/details is invalidated.

#### 5.2.3 Enrolling into a Course

1. Authenticated `student` calls:

   * `POST /api/v1/enrollments/` with `course` id.
2. `EnrollmentViewSet`:

   * checks role `student`,
   * creates `Enrollment` linked to `request.user`.
3. Celery task `send_enrollment_email(enrollment_id)` is triggered asynchronously.

---

## 6. Caching Layer (Redis)

Redis is used as a cache backend for Django.

### 6.1 What Is Cached

* **Public courses list**:

  * `CourseListView` may be wrapped with `@cache_page(60 * 5, cache="default")`.
  * Endpoint: `GET /api/v1/courses-public/`.

* **Course detail**:

  * `CourseViewSet.retrieve()`:

    * reads from cache key `course:{id}`,
    * on cache miss:

      * fetches from DB,
      * serializes data,
      * stores into cache with TTL = 300 seconds.

### 6.2 Cache Invalidation

To avoid stale data, cache is invalidated on write operations:

* `_invalidate_course_cache(course)`:

  * deletes:

    * `courses:list` (reserved key for list caching),
    * `course:{course.id}` for course detail.

This method is called in:

* `perform_create`
* `perform_update`
* `perform_destroy`

### 6.3 Cache Toggle

Caching is controlled by the `ENABLE_CACHE` environment flag:

* `ENABLE_CACHE=True` → caching is active.
* `ENABLE_CACHE=False` → code falls back to standard DRF behavior without cache.

This allows using the same codebase both in:

* **development** (no cache, easier debugging),
* **production-like** mode (cache enabled).

---

## 7. Background Processing (Celery)

Celery is used to execute non-critical, potentially slow tasks outside the HTTP request lifecycle.

### 7.1 Celery Topology

```text
Django "web" → pushes jobs → Redis (broker) → Celery "worker" → executes tasks
                                        ▲
                                        │ (results / flags)
                                        └──── Redis (backend)
```

The Celery app is configured in `config/celery.py` and uses Redis for:

* `CELERY_BROKER_URL` – message broker
* `CELERY_RESULT_BACKEND` – task result backend

### 7.2 Tasks

Key tasks in `common/tasks.py`:

1. `send_enrollment_email(enrollment_id)`:

   * fetches `Enrollment`,
   * uses Redis `cache.add()` as an idempotency flag:

     * if the key already exists, the task is skipped.
   * logs that a notification email would be sent.

2. `generate_daily_report()`:

   * aggregates counters (`courses_count`, `enrollments_count`),
   * writes them into logs (can be extended to email or dashboard).

3. `cleanup_abandoned_enrollments()`:

   * demo task for future cleanup logic,
   * currently logs execution (placeholder).

---

## 8. Logging & Error Handling

### 8.1 JSON Logging

The logging configuration in `common/logging.py` sets up:

* `JsonFormatter` → outputs logs as JSON.
* Loggers:

  * `app.access` – for HTTP access logs.
  * `app.error` – for application errors.
  * `django` / `django.request` – framework-level logs.

Each log entry can include:

* timestamp,
* log level,
* logger name,
* message,
* `request_id`,
* additional structured `extra` data.

### 8.2 Request ID & Access Logging

Middlewares in `common/middleware.py`:

* `RequestIDMiddleware`:

  * assigns a UUID (`request.id`) to each request,
  * measures latency (`duration_ms`),
  * adds headers:

    * `X-Request-ID`
    * `X-Response-Time-ms`.

* `AccessLogMiddleware`:

  * logs each HTTP request:

    * method, path, status, user ID, duration, request ID.

### 8.3 Error Responses (RFC7807)

Custom exception handler `rfc7807_exception_handler` in `common/exceptions.py`:

* wraps DRF errors into **RFC7807 Problem Details** JSON structure:

  * `type`
  * `title`
  * `status`
  * `detail`
  * `instance`
  * `timestamp`
  * `request_id`
* logs both handled and unhandled exceptions via `app.error`.

This helps during incident investigation and makes error responses consistent.

---

## 9. Deployment & Scaling

### 9.1 Docker Compose Topology

In development and demo environments, services are orchestrated via `docker-compose.yml`:

* `web`:

  * Django / DRF.
  * Exposes port `8000`.
* `db`:

  * PostgreSQL 15.
  * Exposes `5432` (internal or mapped to host).
* `redis`:

  * Redis 7.
  * Default port `6379`.
* `celery`:

  * Celery worker running with the same codebase as `web`.

### 9.2 Scaling Options

Current project is a **monolith**, but the architecture allows:

* Vertical scaling:

  * more CPU/RAM for `web` and `db` containers.
* Horizontal scaling:

  * multiple `web` containers behind a load balancer,
  * multiple `celery` workers consuming from the same Redis broker.

Redis caching and idempotent tasks help the system behave predictably under increased load.

---

## 10. Summary

EduFlow is a monolithic, but highload-aware backend:

* clear separation of responsibilities between Django, PostgreSQL, Redis, and Celery,
* JWT-based auth + RBAC on API level,
* Redis-powered caching and idempotent background tasks,
* structured JSON logging with request correlation,
* Docker-based deployment topology.

This architecture satisfies the requirements of the **Highload Backend** course for:

* CRUD and validation (Task 1),
* security and access control (Task 2),
* performance and background tasks (Task 3),
* documentation and runbook (Task 4).

```