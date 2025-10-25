Changelog
All notable changes to the EduFlow project will be documented in this file.

The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

[Unreleased]
[1.1.0] - 2025-10-24
Added
-Docker containerization for simplified deployment
-PostgreSQL database support replacing SQLite for production readiness
-Dockerfile and docker-compose.yml for service orchestration
-Environment-based configuration for database connections

Changed
-Database configuration from SQLite to PostgreSQL in settings
-Project structure to support containerized deployment

[1.0.1] - 2025-10-23
Added
-OpenAPI/Swagger documentation using drf-spectacular
-API schema generation at /api/schema/
-Interactive Swagger UI at /api/docs/
-AutoSchema configuration in REST framework settings

Changed
-Updated REST_FRAMEWORK settings to include default schema class
-Enhanced URL patterns with schema and documentation endpoints

[1.0.0] - 2025-10-19
Added
-Core Django REST Framework API with JWT authentication
-User role system (student, instructor, admin) with custom User model
-CRUD operations for Courses, Lessons, and Enrollments
-JSON-structured logging with request IDs and timing middleware
-Custom exception handler following RFC 7807 Problem Details standard
-Access logging middleware for all HTTP requests
-Permission classes for owner-based and role-based access control
-Pagination, filtering, and search capabilities across API endpoints
-Model relationships between Users, Courses, Lessons, and Enrollments

Security
-JWT token authentication with configurable lifetimes (30min access, 7 days refresh)
-Role-based permission checks for all sensitive operations
-Input validation in serializers for all models

