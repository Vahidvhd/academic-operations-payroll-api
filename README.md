# Instructor Operations and Payroll API

[![CI](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api/graph/badge.svg?token=P54EYCF2QU)](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api)

A Django REST API project for instructor operations and payroll, currently developed through Phase 1.

This README describes the current implementation of **Phase 1** of the project.

## Phase 1

Phase 1 focuses on setting up the main project structure, authentication, user roles, academic models, permissions, testing, and development infrastructure.

### Implemented

- Custom Django user model
- Three business roles:
  - Teacher
  - Education Officer
  - Finance Officer
- JWT authentication
- Current user endpoint
- Role-based permission classes
- School, Term, and CourseClass models
- PostgreSQL database
- Docker Compose for PostgreSQL
- User creation management command
- Sample user seed command
- Automated tests
- Test coverage
- GitHub Actions CI
- Codecov integration
- OpenAPI schema and Swagger UI

## Tech Stack

- Python 3.13
- Django 5
- Django REST Framework
- PostgreSQL
- Simple JWT
- Docker / Docker Compose
- drf-spectacular
- Coverage.py
- Codecov
- GitHub Actions

## User Roles

The system currently supports three business roles.

### Teacher

Represents an instructor.

Teachers have additional profile information:

- phone number
- emergency phone number

### Education Officer

Responsible for academic and reporting-related operations.

### Finance Officer

Responsible for finance and payroll-related operations.

Each normal application user has one business role.

Django staff and superuser permissions are kept separate from these business roles.

## Authentication

Authentication is handled using JWT access and refresh tokens.

There is no public user registration endpoint.

Users are created by the system or through management commands.

The authenticated user can check their own account information and role using:

```text
GET /api/users/me/
```

## Academic Models

### School

Stores school information.

Main fields:

- name
- address

A school is unique by the combination of its name and address.

### Term

Represents an academic term.

Main fields:

- start date
- end date
- term type

Supported term types:

- regular
- summer

Current validation includes:

- end date cannot be before start date
- term starts on the first day of a month
- term ends on the last day of a month
- terms cannot overlap

### CourseClass

Represents a class running inside a term.

Main fields:

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

A class must be inside its term date range.

The combination of school, term, and class code must be unique.

## Date Format

The project currently uses **Gregorian dates**.

## Role-Based Permissions

Reusable Django REST Framework permission classes are available for:

- `IsTeacher`
- `IsEducationOfficer`
- `IsFinanceOfficer`

These permissions check both authentication and the user's assigned role.

Role boundaries are covered by automated tests.

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

The command is idempotent, so running it more than once does not create duplicate users.

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

When the development server is running, Swagger can be opened at:

```text
http://127.0.0.1:8000/api/docs/
```

## Local Setup

Clone the repository:

```bash
git clone git@github.com:Vahidvhd/instructor-reporting-payroll-api.git
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

Start PostgreSQL:

```bash
docker compose up -d
```

Run migrations:

```bash
python manage.py migrate
```

Optionally create the sample users:

```bash
python manage.py seed_sample_users
```

Start the Django development server:

```bash
python manage.py runserver
```

## Testing

Run the complete test suite with:

```bash
python manage.py test
```

Run the tests with coverage:

```bash
python -m coverage run manage.py test
python -m coverage report
```

Coverage reports are also uploaded to Codecov through GitHub Actions.

## Continuous Integration

GitHub Actions runs automatically on pushes and pull requests.

The CI workflow:

- starts a PostgreSQL service
- installs project dependencies
- runs Django system checks
- runs the test suite
- generates the coverage report
- uploads coverage results to Codecov

## Phase 1 Status

Phase 1 establishes the foundation of the application:

- authentication and users
- role-based access control
- core academic data models
- PostgreSQL integration
- automated testing
- CI and coverage reporting
- API documentation

Further business workflows such as sessions, instructor reports, approvals, and payroll are intentionally outside the scope of this phase.