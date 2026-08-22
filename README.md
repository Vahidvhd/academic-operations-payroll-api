# Instructor Operations and Payroll API

[![CI](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api/graph/badge.svg?token=P54EYCF2QU)](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api)

A Django REST Framework backend for managing academic operations, instructor assignments, course sessions, and instructor reporting workflows.

The project demonstrates backend engineering beyond basic CRUD, including role-based access control, historical teacher assignments, cross-model validation, transactional workflows, audit history, soft deletion, automated testing, and CI/CD tooling.

**Current status:** Phases 1–3 completed. Payroll calculation is planned for the next phase.

## Key Features

- JWT authentication with access and refresh tokens
- Custom Django user model
- Role-based access control for:
  - Teacher
  - Education Officer
  - Finance Officer
- Superuser-only user creation API
- Configured Django Admin for operational management
- School, academic term, course class, and session management
- Historical teacher-to-class assignments
- Teacher-specific data visibility
- Course and report filtering
- Soft deletion for key academic records
- Session scheduling with overlap validation
- Instructor session reporting
- Approval and rejection workflow
- Rejected report editing and resubmission
- Mandatory rejection reasons
- 48-hour report lateness calculation
- Report status audit history
- Monthly report status summaries
- Transactional bulk report approval
- OpenAPI schema and Swagger documentation
- PostgreSQL with Docker Compose
- GitHub Actions CI and Codecov integration
- 269 automated tests
- 97% test coverage

## Tech Stack

- Python 3.13
- Django 5.2
- Django REST Framework
- PostgreSQL 17
- Simple JWT
- django-filter
- Docker / Docker Compose
- drf-spectacular
- Coverage.py
- GitHub Actions
- Codecov

## Core Workflow

An Education Officer manages schools, terms, classes, teacher assignments, and course sessions.

Teachers can access only the classes and sessions relevant to their assignments. After a session ends, the assigned teacher can submit a report containing the lesson summary and attendance figures.

Reports start as `pending`.

An Education Officer can then:

- approve a report
- reject a report with a required reason
- review report status history
- filter reports by school, class, teacher, and date
- approve multiple selected reports in one atomic bulk operation

A rejected report can be edited and resubmitted by the teacher, returning it to `pending`.

When a report is approved, the system calculates lateness from the end of the session using a 48-hour grace period. Any partial hour beyond the grace period is rounded up.

Status transitions are recorded in an audit history with the user responsible for the change and the timestamp.

## Database Design

The data model preserves historical teacher assignments and report status changes rather than overwriting operational history.

![Entity Relationship Diagram](docs/erd/erd.png)

The editable Draw.io source is available at [`docs/erd/erd.drawio`](docs/erd/erd.drawio).

## API Overview

Authentication:

```text
POST /api/auth/token/
POST /api/auth/token/refresh/
GET  /api/users/me/
```

Superuser management:

```text
POST /api/users/admin/create/
```

Academic operations:

```text
/api/schools/
/api/terms/
/api/course-classes/
/api/teacher-class-assignments/
/api/course-sessions/
```

Instructor reporting:

```text
GET  /api/reports/
POST /api/reports/

GET   /api/reports/<id>/
PATCH /api/reports/<id>/

POST /api/reports/<id>/review/
GET  /api/reports/<id>/history/

GET  /api/reports/monthly-summary/?year=2026&month=8
POST /api/reports/bulk-approve/
```

Full endpoint documentation is available through Swagger.

## Roles and Permissions

### Teacher

Teachers can:

- view their assigned classes and sessions
- view their own session reports
- submit reports only for their own assigned sessions
- edit and resubmit rejected reports
- view their monthly report status summary

Teachers cannot approve or reject reports.

### Education Officer

Education Officers can:

- manage academic data
- manage teacher-class assignments
- manage course sessions
- view and filter reports
- approve or reject reports
- bulk approve selected reports
- view report status history

### Finance Officer

The Finance Officer role is defined and protected by the permission system.

Payroll functionality will be introduced in the next phase.

### System Administrator

Django administration is kept separate from business roles.

Django superusers can:

- manage users through `/admin/`
- assign one of the three business roles
- create users through the protected Admin API

Report and report-history data are configured as read-only in Django Admin to prevent bypassing the reporting workflow.

## Business Rules

The API enforces domain rules at the model and serializer layers, including:

- terms must start on the first day of a month
- terms must end on the final day of a month
- academic terms cannot overlap
- class dates must remain inside their term
- session duration must be 60, 90, or 120 minutes
- teacher assignments must remain inside class dates
- teacher assignments for the same class cannot overlap
- scheduled sessions cannot overlap
- session numbers must be unique within a class
- teachers can report only sessions belonging to their assignments
- reports cannot be submitted before a session ends
- only rejected reports can be edited
- rejection requires a review note
- approved reports cannot be reviewed again

## API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/api/docs/
```

OpenAPI schema:

```text
http://127.0.0.1:8000/api/schema/
```

## Local Setup

Clone the repository:

```bash
git clone https://github.com/Vahidvhd/instructor-reporting-payroll-api.git
cd instructor-reporting-payroll-api
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
cp .env.example .env
```

Start PostgreSQL:

```bash
docker compose up -d
```

Run migrations:

```bash
python manage.py migrate
```

Optional development users:

```bash
python manage.py seed_sample_users
```

Start the API:

```bash
python manage.py runserver
```

## Testing

Run the complete test suite:

```bash
python manage.py test
```

Run with coverage:

```bash
coverage run manage.py test
coverage report
coverage xml
```

Current test suite:

```text
269 tests
97% coverage
```

GitHub Actions runs Django system checks, the full test suite, and coverage reporting on pushes and pull requests.

## Project Structure

```text
academics/   Academic models, serializers, filters, APIs, and admin
reports/     Session reporting workflow, review logic, audit history
users/       Authentication, roles, permissions, admin user management
core/        Shared model abstractions
config/      Django project configuration
docs/erd/    ERD diagram and editable source
```

## Roadmap

The next phase will introduce the payroll workflow, including instructor rates, monthly salary calculation, late-report penalties, and payroll locking rules.