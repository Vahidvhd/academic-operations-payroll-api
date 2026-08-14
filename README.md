# Instructor Operations and Payroll API

[![CI](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api/graph/badge.svg?token=P54EYCF2OU)](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api)

A Django REST API for class scheduling, instructor operations, reporting workflows, approvals, and payroll calculation.

The project is currently implemented through **Phase 2**.

---

## Project Overview

The system is built around three business roles:

- Teacher
- Education Officer
- Finance Officer

The current implementation includes JWT authentication, role-based permissions, academic data management, teacher-class assignments, filtering and search, automated tests, PostgreSQL integration, CI, coverage reporting, and API documentation.

---

## Phase 1

Phase 1 established the project foundation.

### Implemented

- Custom Django user model
- Three business roles:
  - Teacher
  - Education Officer
  - Finance Officer
- JWT authentication
- Current user endpoint
- Role-based permission classes
- School model
- Term model
- CourseClass model
- PostgreSQL database
- Docker Compose for PostgreSQL
- User creation management command
- Sample user seed command
- Automated tests
- Test coverage
- GitHub Actions CI
- Codecov integration
- OpenAPI schema
- Swagger UI
- Soft deletion for academic models

---

## Phase 2

Phase 2 adds the academic workflows required by Education Officers and Teachers.

### School Management

Education Officers can:

- create schools
- list schools
- retrieve school details
- update schools
- soft delete schools

A school is unique by the combination of its name and address.

### Term Management

Education Officers can:

- create terms
- list terms
- retrieve term details
- soft delete eligible terms

Each term contains:

- start date
- end date
- term type

Supported term types:

- regular
- summer

Validation rules include:

- end date cannot be before start date
- term must start on the first day of a month
- term must end on the last day of a month
- terms cannot overlap

A term that has already been linked to a CourseClass cannot be deleted.

### Course Class Management

Education Officers can create and manage classes for a specific School and Term.

Each CourseClass contains:

- school
- term
- title
- class code
- start date
- end date
- session duration

Supported session durations:

- 60 minutes
- 90 minutes
- 120 minutes

Validation rules include:

- class start date cannot be after class end date
- class dates must stay inside the selected term
- session duration must be 60, 90, or 120 minutes
- school, term, and class code combination must be unique
- inactive schools and terms cannot be used for new classes

CourseClass records use soft deletion.

### Teacher-Class Assignments

Teachers are connected to classes through a separate `TeacherClassAssignment` model.

Each assignment stores:

- teacher
- course class
- start date
- optional end date

This allows one class to have different teachers during different periods.

Example:

```text
Teacher A: 2026-09-01 -> 2026-10-31
Teacher B: 2026-11-01 -> 2026-12-31
```

Sequential teacher assignments are allowed.

Overlapping assignments for the same class are rejected.

Example of an invalid overlap:

```text
Teacher A: 2026-09-01 -> 2026-10-31
Teacher B: 2026-10-15 -> 2026-12-31
```

Assignment validation also ensures that:

- the selected user has the Teacher role
- assignment start date cannot be after assignment end date
- assignment dates stay inside the CourseClass date range
- an open assignment must be closed before another teacher takes over the same class

### Teacher Class Visibility

Teachers can retrieve the CourseClasses connected to their own assignments.

Teachers cannot use the CourseClass API to view classes belonging only to other teachers.

Write operations remain restricted to the Education Officer.

### Course Class Filtering

Course classes can be filtered by School:

```text
GET /api/course-classes/?school=1
```

By Term:

```text
GET /api/course-classes/?term=1
```

By Teacher:

```text
GET /api/course-classes/?teacher=3
```

Filters can be combined:

```text
GET /api/course-classes/?school=1&term=1&teacher=3
```

### Course Class Search

Course classes support search across relevant School, Term, and Teacher information.

Example:

```text
GET /api/course-classes/?search=Maktab
```

### Current Teacher Summary

CourseClass detail responses include a short summary of the currently assigned teacher when one exists.

Example:

```json
{
  "current_teacher": {
    "id": 3,
    "first_name": "Example",
    "last_name": "Teacher"
  }
}
```

This avoids requiring a separate request to retrieve the current teacher.

---

## Tech Stack

- Python 3.13
- Django 5
- Django REST Framework
- PostgreSQL
- Simple JWT
- django-filter
- Docker / Docker Compose
- drf-spectacular
- Coverage.py
- Codecov
- GitHub Actions

---

## User Roles

### Teacher

Represents an instructor.

Teacher-specific profile information includes:

- phone number
- emergency phone number

Teachers can access classes connected to their assignments according to the academic permission rules.

### Education Officer

Responsible for academic operations.

The Education Officer manages:

- schools
- terms
- course classes
- teacher-class assignments

### Finance Officer

Reserved for finance and payroll operations.

Finance-specific workflows are planned for later phases.

### Django Administrative Permissions

Django staff and superuser permissions are separate from the three business roles.

Being a Django administrator does not introduce a fourth business role.

---

## Authentication

Authentication uses JWT access and refresh tokens.

There is no public registration endpoint.

Users are created through management commands or system administration.

### Get Access and Refresh Tokens

```text
POST /api/token/
```

Example request:

```json
{
  "username": "education_sample",
  "password": "SamplePassword@"
}
```

Example response:

```json
{
  "refresh": "...",
  "access": "..."
}
```

Use the access token for authenticated API requests:

```text
Authorization: Bearer ACCESS_TOKEN
```

### Refresh an Access Token

```text
POST /api/token/refresh/
```

Example request:

```json
{
  "refresh": "REFRESH_TOKEN"
}
```

### Current User

The authenticated user can retrieve their own identity and role with:

```text
GET /api/users/me/
```

---

## API Endpoints

### Authentication

```text
POST /api/token/
POST /api/token/refresh/
GET  /api/users/me/
```

### Schools

```text
GET    /api/schools/
POST   /api/schools/
GET    /api/schools/<id>/
PUT    /api/schools/<id>/
PATCH  /api/schools/<id>/
DELETE /api/schools/<id>/
```

### Terms

```text
GET    /api/terms/
POST   /api/terms/
GET    /api/terms/<id>/
DELETE /api/terms/<id>/
```

### Course Classes

```text
GET    /api/course-classes/
POST   /api/course-classes/
GET    /api/course-classes/<id>/
PUT    /api/course-classes/<id>/
PATCH  /api/course-classes/<id>/
DELETE /api/course-classes/<id>/
```

### Teacher-Class Assignments

```text
GET    /api/teacher-class-assignments/
POST   /api/teacher-class-assignments/
GET    /api/teacher-class-assignments/<id>/
PUT    /api/teacher-class-assignments/<id>/
PATCH  /api/teacher-class-assignments/<id>/
DELETE /api/teacher-class-assignments/<id>/
```

---

## Academic Models

### School

Main fields:

- name
- address

Schools support soft deletion.

### Term

Main fields:

- start date
- end date
- term type

Supported types:

- regular
- summer

Terms support soft deletion.

### CourseClass

Main fields:

- school
- term
- title
- class code
- start date
- end date
- session duration

Supported session durations:

- 60
- 90
- 120

Course classes support soft deletion.

### TeacherClassAssignment

Represents a teacher's responsibility for a CourseClass during a specific date range.

Main fields:

- teacher
- course class
- start date
- end date

Multiple assignment records may exist for the same CourseClass as long as their date ranges do not overlap.

---

## Date Format

The project currently uses Gregorian dates.

Example:

```text
2026-09-01
```

---

## Role-Based Permissions

Reusable Django REST Framework permission classes are available for:

```text
IsTeacher
IsEducationOfficer
IsFinanceOfficer
```

These permissions check authentication and the user's assigned business role.

Role boundaries are covered by automated tests.

---

## Management Commands

### Create a User

Users can be created from the command line instead of through public registration.

Example:

```bash
python manage.py create_user --role=teacher
```

Available roles:

```text
teacher
education_officer
finance_officer
```

### Create Sample Users

For development and testing, sample users can be created with:

```bash
python manage.py seed_sample_users
```

The command is idempotent, so running it more than once does not create duplicate sample users.

Sample accounts:

| Username | Role |
|---|---|
| `teacher_sample` | Teacher |
| `education_sample` | Education Officer |
| `finance_sample` | Finance Officer |

Sample password:

```text
SamplePassword@
```

---

## API Documentation

OpenAPI documentation is generated using `drf-spectacular`.

Swagger UI:

```text
/api/docs/
```

OpenAPI schema:

```text
/api/schema/
```

When the development server is running, Swagger is available at:

```text
http://127.0.0.1:8000/api/docs/
```

---

## Local Setup

Clone the repository:

```bash
git clone git@github.com:Vahidvhd/instructor-reporting-payroll-api.git
cd instructor-reporting-payroll-api
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start PostgreSQL:

```bash
docker compose up -d
```

Run migrations:

```bash
python manage.py migrate
```

Optionally create sample users:

```bash
python manage.py seed_sample_users
```

Start the Django development server:

```bash
python manage.py runserver
```

---

## Testing

Run the complete test suite:

```bash
python manage.py test
```

Run tests with coverage:

```bash
python -m coverage run manage.py test
python -m coverage report
```

The test suite covers areas including:

- authentication
- user roles
- permissions
- School operations
- Term validation
- CourseClass operations
- CourseClass validation
- teacher-class assignments
- multiple sequential teachers on one class
- overlapping assignment rejection
- teacher-specific class visibility
- filtering
- search
- current teacher summary

Coverage reports are uploaded to Codecov through GitHub Actions.

---

## Continuous Integration

GitHub Actions runs automatically on pushes and pull requests.

The CI workflow:

- starts a PostgreSQL service
- installs project dependencies
- runs Django system checks
- runs the automated test suite
- generates coverage information
- uploads coverage results to Codecov

---

## Phase 2 Status

Phase 2 currently includes:

- School management
- Term creation and validation
- CourseClass management
- allowed session-duration validation
- TeacherClassAssignment management
- multiple sequential teachers for one class
- overlapping assignment prevention
- Teacher-specific class visibility
- CourseClass filtering
- CourseClass search
- current teacher summary
- automated tests

---

## Current Limitations

The project is currently implemented through Phase 2.

Current Phase 2 limitations include:

- Term update operations are not currently exposed through the API.
- Later reporting and payroll workflows are not implemented yet.

The following workflows belong to later phases:

- course sessions
- one-session substitute teachers
- instructor session reports
- report approval workflows
- report status history
- teacher wages
- monthly salary calculation
- payroll operations

---

## Next Phases

Future phases will build on the current academic foundation to add:

- session generation and management
- instructor reporting
- report review and approval
- substitute-teacher handling
- wage configuration
- salary calculation
- payroll workflows
