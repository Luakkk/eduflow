
# 🎓 EduFlow — Highload Backend for Online Learning Platform

EduFlow is a backend for an online learning platform, built as the final project for the **Highload Backend** course.

The project demonstrates:

- **Django + DRF** for REST API.
- **JWT authentication** and user roles.
- **RBAC** (role-based access control).
- **Validated CRUD endpoints**.
- **Structured JSON logging**.
- **Redis cache** for popular read requests.
- **Celery tasks** for background processing.
- **Swagger / OpenAPI** documentation.
- Deployment via **Docker Compose** (`web + db + redis + celery`).

---

## 📦 Core Functionality

### 👤 Users & Roles

Custom `User` model based on `AbstractUser`:

- Fields: `username`, `email`, `role` + standard Django fields.
- Roles:
  - `admin`
  - `instructor`
  - `student`

Main auth endpoints:

- `POST /api/v1/auth/register/` — user registration.
- `POST /api/v1/auth/login/` — obtain JWT pair (access + refresh).
- `POST /api/v1/auth/refresh/` — refresh access token.
- `GET  /api/v1/auth/me/` — get current user profile.

Role behavior:

- **Admin** — full access to all courses, lessons, enrollments.
- **Instructor** — creates and manages **only their own** courses and lessons.
- **Student** — can browse published courses and enroll into them.

Validation:

- `email` is validated for format and uniqueness (case-insensitive).
- `username` must be at least 3 characters long.
- `password` is validated via Django’s password validators.

---

### 📚 Courses & Lessons

Simplified models:

- `Course` — a course (`owner`, `title`, `description`, `price`, `is_published`, etc.).
- `Lesson` — a lesson belonging to a course.

Endpoints:

- Public course list (read-only, can be cached):

  - `GET /api/v1/courses-public/` → `CourseListView`

- Main courses CRUD (`CourseViewSet`):

  - `GET    /api/v1/courses/` — list courses  
    (students/anonymous see only published ones).
  - `POST   /api/v1/courses/` — create a course (only `admin` or `instructor`).
  - `GET    /api/v1/courses/<id>/` — retrieve course details (cached for 5 minutes).
  - `PUT    /api/v1/courses/<id>/` — full update.
  - `PATCH  /api/v1/courses/<id>/` — partial update.
  - `DELETE /api/v1/courses/<id>/` — delete a course.

- Lessons CRUD (`LessonViewSet`):

  - `GET    /api/v1/lessons/` — list lessons.
  - `POST   /api/v1/lessons/` — create a lesson  
    (only course owner or `admin`).
  - `PUT    /api/v1/lessons/<id>/`
  - `PATCH  /api/v1/lessons/<id>/`
  - `DELETE /api/v1/lessons/<id>/`

Access rules:

- Anonymous users & students:
  - see only lessons of courses where `course.is_published = True`.
- Instructors & admins:
  - can manage lessons **only in their own** courses  
    (except admin, who can manage everything).

---

### 🎓 Course Enrollments

`Enrollment` model links:

- `student` (user),
- `course`.

Endpoints (`EnrollmentViewSet`):

- `GET    /api/v1/enrollments/`:
  - students see **only their own** enrollments,
  - `instructor` and `admin` see **all** enrollments.
- `POST   /api/v1/enrollments/`:
  - only users with role `student` can enroll,
  - `student` is taken from `request.user`.
- `DELETE /api/v1/enrollments/<id>/`:
  - can be deleted by:
    - `admin`, or
    - the student who owns this enrollment.

On successful enrollment:

- a Celery task `send_enrollment_email(enrollment.id)` is triggered,
- the task is idempotent (re-run with the same `enrollment_id` is ignored).

---

### 🧊 Caching (Redis)

Django cache is configured with Redis backend.

- Public courses list:
  - `CourseListView` is wrapped with `@cache_page(60 * 5, cache="default")`.
  - Endpoint: `GET /api/v1/courses-public/`.

- Course detail:
  - `CourseViewSet.retrieve()`:
    - reads/writes data to cache under key `course:{id}`,
    - cache TTL is 5 minutes.

Cache invalidation:

- `_invalidate_course_cache(course)` method in `CourseViewSet`:
  - removes:
    - `courses:list` (reserved key for lists, if used),
    - `course:{id}` — for course detail.
- Called after `create`, `update`, and `delete` on a course.

Cache toggle:

- Controlled via `ENABLE_CACHE` in `.env`:
  - `ENABLE_CACHE=True` — cache is used.
  - `ENABLE_CACHE=False` — views behave like regular DRF views (no caching).

---

### 🧵 Background Tasks (Celery)

Celery is configured with Redis as broker and result backend.

Main tasks in `common/tasks.py`:

- `send_enrollment_email(enrollment_id)`:

  - fetches `Enrollment` by `id`;
  - provides idempotency via a Redis flag:

    ```python
    key = f"task:send_email:{enrollment_id}"
    if not cache.add(key, "1", timeout=3600):
        # Task was already processed for this enrollment_id
        return
    ```

  - logs “email sending” (can be replaced with real `send_mail` if needed).

- `generate_daily_report()`:

  - counts `Course.objects.count()` and `Enrollment.objects.count()`,
  - logs a simple daily report.

- `cleanup_abandoned_enrollments()`:

  - demo task for cleaning “abandoned” enrollments,
  - currently just logs execution (can be extended with real cleanup logic).

Celery runs as a separate `celery` service in `docker-compose.yml` and shares `.env` configuration with Django.

---

### 📜 Logging (JSON + Request ID)

Structured logging is configured in `common/logging.py` and `common/middleware.py`.

- `JsonFormatter`:

  - outputs logs in JSON with fields:
    - `timestamp`
    - `level`
    - `logger`
    - `message`
    - `request_id`
    - `extra`
    - stack trace for errors.

- `RequestIDMiddleware`:

  - creates `request.id` (UUID) for each request,
  - measures processing time (`duration_ms`),
  - adds headers:
    - `X-Request-ID`
    - `X-Response-Time-ms`.

- `AccessLogMiddleware`:

  - logs access events using the `app.access` logger:
    - HTTP method, URL, status, `user_id`, `duration_ms`, `request_id`.

- `rfc7807_exception_handler` in `common/exceptions.py`:

  - wraps DRF errors into **RFC7807 Problem Details** responses,
  - logs handled and unhandled errors via the `app.error` logger.

---

## 🧱 Tech Stack

| Layer             | Technology          |
|-------------------|----------------------|
| Backend           | Django 5 + DRF       |
| Authentication    | SimpleJWT            |
| Database          | PostgreSQL           |
| Cache / Queue     | Redis                |
| Background Tasks  | Celery               |
| API Documentation | drf-spectacular      |
| Logging           | JSON + Request ID    |
| Containerization  | Docker / Compose     |

---

## 🚀 Local Development (without Docker)

> Useful if you just want to run the API quickly in dev mode.

### 1. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
````

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. `.env` file in the project root


### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Run dev server

```bash
python manage.py runserver
```

---

## 🐳 Running via Docker Compose

> This setup runs **PostgreSQL + Redis + Django + Celery** together.

Before running:

* ensure local ports `5432` (Postgres) and `8000` (Django) are free;
* if you have a local Postgres running, stop it or change ports in `docker-compose.yml`.

### 1. Build and start containers

```bash
docker compose up --build
```

Services:

| Service | Description            |
| ------- | ---------------------- |
| web     | Django API             |
| db      | PostgreSQL             |
| redis   | Redis (cache + broker) |
| celery  | Celery worker          |

### 2. Run migrations inside the container

```bash
docker compose exec web python manage.py migrate
```

### 3. Create superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 4. Check everything is up

API:

* `http://localhost:8000/api/v1/courses-public/`
* `http://localhost:8000/api/v1/courses/`

Swagger UI:

* `http://localhost:8000/api/docs/`

OpenAPI schema:

* `http://localhost:8000/api/schema/`

In the `celery` container logs you should see something like:

```text
[INFO/MainProcess] celery@<hostname> ready.
```

---

## 📡 Main Endpoints (Summary)

### 🔑 Auth (`/api/v1/auth/`)

* `POST /register/` — register a new user.
* `POST /login/` — obtain access/refresh tokens.
* `POST /refresh/` — refresh access token.
* `GET  /me/` — get current user profile.

---

### 📚 Courses (`/api/v1/`)

* `GET  /courses-public/` — public course list (read-only, cacheable).
* `GET  /courses/` — main course list (role-based + publish status).
* `POST /courses/` — create a new course (`admin`, `instructor`).
* `GET  /courses/<id>/` — get course details (cached for 5 minutes).
* `PUT/PATCH /courses/<id>/` — update a course.
* `DELETE /courses/<id>/` — delete a course.

---

### 📖 Lessons (`/api/v1/lessons/`)

* `GET  /lessons/` — list lessons.
* `POST /lessons/` — create a lesson (course owner or `admin`).
* `PUT/PATCH/DELETE /lessons/<id>/` — manage a lesson.

---

### 🎓 Enrollments (`/api/v1/enrollments/`)

* `GET  /enrollments/` — student’s own enrollments / all enrollments (for instructor/admin).
* `POST /enrollments/` — enroll into a course (only `student`).
* `DELETE /enrollments/<id>/` — delete an enrollment (student-owner or `admin`).

---

## 🧠 Architecture (Short Overview)

```text
Client (web / mobile / API client)
        │ HTTP (JWT)
        ▼
Django + DRF (EduFlow API)
        │
        ├─ PostgreSQL (users, courses, lessons, enrollments)
        │
        ├─ Redis (cache for popular read requests + Celery message broker)
        │
        └─ Celery worker (background jobs: emails, reports, cleanup)
```

---

## ✅ Mapping to Course Requirements

**Task 1 — CRUD + Validation**

* CRUD for `User`, `Course`, `Lesson`, `Enrollment`.
* Responses in JSON with proper HTTP status codes.
* Validation for email/username/password.

**Task 2 — Security & Access Control**

* JWT auth via SimpleJWT.
* Roles: `admin / instructor / student`.
* Role-based access checks in viewsets.
* Structured logging (access + error) in JSON.

**Task 3 — Performance & Background Tasks**

* Redis cache on courses.
* Cache invalidation when data changes.
* Celery background tasks + idempotency via Redis flags.

**Task 4 — Documentation**

* README with local + Docker setup instructions.
* Summary of main endpoints.
* Swagger documentation at `/api/docs/` and `/api/schema/`.

