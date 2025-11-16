
# 🎓 **EduFlow – Highload Backend for Online Learning Platform**

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.0-darkgreen?logo=django)
![DRF](https://img.shields.io/badge/DRF-REST%20Framework-red)
![Postgres](https://img.shields.io/badge/Postgres-15-blue?logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7.0-red?logo=redis)
![Celery](https://img.shields.io/badge/Celery-worker-green?logo=celery)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)

EduFlow is a highload-ready backend system for an online courses platform.
It demonstrates production-level architecture using:

* Django + DRF
* Role-based access control (`admin / instructor / student`)
* JWT authentication
* Advanced validation + RFC7807 error format
* JSON structured logging
* Redis caching
* Celery background tasks
* Swagger / OpenAPI documentation
* Docker-Compose orchestration (web + db + redis + worker)

This project is built as a final assignment for the **Highload Backend course**.

---

# ⚡️ **Features Overview**

## 🔐 Authentication & Roles

* JWT (access + refresh tokens)
* Custom User model with roles:

  * **Admin** — full access
  * **Instructor** — create/manage own courses
  * **Student** — enroll & browse

## 📚 Courses & Lessons

* CRUD for Courses
* CRUD for Lessons
* Permissions enforced at both:

  * View level
  * Object level (owner/admin only)

## 🎓 Enrollments

* Students can enroll/unenroll
* Instructors/admin see all enrollments
* Validation prevents duplicate enrollments

## 🔥 Highload Components

* Redis caching
* Celery distributed task queue
* Structured JSON logs
* Request ID correlation
* Cache invalidation on writes
* Redis SETNX idempotency patterns

## 📘 Documentation

* OpenAPI schema – `/api/schema/`
* Swagger UI – `/api/docs/`

---

# 🧱 **Tech Stack**

| Layer            | Technology        |
| ---------------- | ----------------- |
| Backend          | Django 5 + DRF    |
| Auth             | SimpleJWT         |
| Database         | PostgreSQL        |
| Cache / Queue    | Redis             |
| Background Tasks | Celery            |
| API Docs         | drf-spectacular   |
| Logging          | JSON + Request ID |
| Containerization | Docker / Compose  |

---

# 🚀 **Local Development Setup**

### 1. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` file

Create a file `.env` in the **root directory**:

```
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=dev-secret-key
ALLOWED_HOSTS=*
POSTGRES_DB=eduflow
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
ENABLE_CACHE=True
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. (Optional) Create superuser

```bash
python manage.py createsuperuser
```

### 6. Start server

```bash
python manage.py runserver
```

---

# 🐳 **Docker-Compose Setup**

> This runs **Postgres + Redis + Django + Celery worker**.

```bash
docker-compose up --build
```

Services:

| Service         | Purpose         |
| --------------- | --------------- |
| web             | Django API      |
| db              | PostgreSQL      |
| redis           | Cache + broker  |
| worker          | Celery worker   |
| beat (optional) | Scheduled tasks |

---

# 📡 **API Endpoints**

### 🔑 Auth

* `POST /api/v1/auth/register/`
* `POST /api/v1/auth/login/`
* `POST /api/v1/auth/refresh/`
* `GET /api/v1/auth/me/`

### 📚 Courses

* `GET /api/v1/courses/` — list (cached)
* `POST /api/v1/courses/` — create (admin/instructor)
* `GET /api/v1/courses/<id>/` — retrieve (cached)
* `PUT/PATCH /api/v1/courses/<id>/`
* `DELETE /api/v1/courses/<id>/`

### 📖 Lessons

* `POST /api/v1/lessons/` — owner/admin
* `GET /api/v1/lessons/`
* `PUT/PATCH/DELETE /api/v1/lessons/<id>/`

### 🎓 Enrollments

* `POST /api/v1/enrollments/`
* `GET /api/v1/enrollments/`
* `DELETE /api/v1/enrollments/<id>/`

---

# 🧪 **Smoke Test cURL Examples**

### Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "testpass"}'
```

### Create course (Instructor)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/courses/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Django Pro", "price": 0, "description":"course"}'
```

### Enroll (Student)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/enrollments/ \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"course": 1}'
```

---

# 🗂 **Architecture Diagram (ASCII)**

```
                ┌───────────────────────┐
                │        Client         │
                │  web / mobile / api  │
                └──────────┬────────────┘
                           │ HTTP
                           ▼
                   ┌───────────────┐
                   │    Django     │
                   │  DRF API App  │
                   └───────┬───────┘
                           │
                           │ ORM
                           ▼
                  ┌───────────────────┐
                  │    PostgreSQL     │
                  └───────────────────┘

                           ▲
                           │ Cache / Broker
                           ▼
                ┌───────────────────────┐
                │        Redis          │
                │ cache + celery broker │
                └──────────┬────────────┘
                           │
                           ▼
                  ┌───────────────────┐
                  │    Celery Worker  │
                  │ email / reports   │
                  └───────────────────┘
```

---

# 🧩 **Highload Features**

### ✔ Redis Caching

* Cache layer for:

  * GET /courses/
  * GET /courses/<id>/
* Low-level caching for detail views
* Cache invalidation on update/delete

### ✔ Celery Background Tasks

Examples:

* Send enrollment confirmation email
* Clean abandoned enrollments
* Generate daily activity report

### ✔ Idempotency (SETNX)

Tasks include:

* idempotent locks
* prevent duplicates on retries

### ✔ JSON Structured Logs

* request_id injected at middleware
* access/error logs separated
* latency (duration_ms) tracked

---

# 📚 **Theory Answers (For Defense)**

## **1. SQL vs NoSQL**

SQL:

* strict schema
* ACID transactions
* good for complex relations (joins)

NoSQL:

* horizontal scaling
* flexible schema
* eventually-consistent reads

Effect on CRUD:

* SQL → predictable API validation
* NoSQL → more defensive validation required

---

## **2. Mass Update Problems**

* long-running transactions
* locks / table locks
* partial failures
* huge load on DB I/O

---

## **3. HTTP Method Semantics**

* GET is cacheable & idempotent
* POST is not idempotent
* PUT/PATCH — idempotent update
* Correct methods = predictable behavior

---

## **4. JWT Storage Risks**

* localStorage vulnerable to XSS
* token leaks -> full account takeover
* refresh token rotation solves many issues

---

## **5. TTL vs UX**

* Short TTL → secure, but users re-login often
* Long TTL → smooth UX but higher security risk

---

## **6. Logging for Incident Analysis**

* request_id → reconstruct timeline
* structured logs → easy to search/grep
* correlate errors with user actions

---

## **7. Horizontal vs Vertical Scaling**

Vertical:

* add more CPU/RAM
  Horizontal:
* add more instances
* requires cache + distributed locks

---

## **8. Message Queue Failures**

If Redis/RabbitMQ goes down:

* tasks delayed
* lost tasks (if not durable)
* duplicate processing on retry

---

## **9. Idempotent Tasks**

Must be safe to run twice:

* SETNX lock keys
* check-if-already-processed flags

