# Instructor Operations and Payroll API

[![CI](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Vahidvhd/instructor-reporting-payroll-api/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api/graph/badge.svg?token=P54EYCF2QU)](https://codecov.io/github/Vahidvhd/instructor-reporting-payroll-api)

A Django REST API project for instructor operations, academic class management, instructor reporting, and payroll.

The project is currently developed through **Phase 2**.

## Phase 1

Phase 1 established the technical foundation of the project.

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

## Phase 2

Phase 2 adds the academic management workflow required for schools, terms, classes, and teacher assignments.

### Implemented

- School API
- Term API
- CourseClass API
- TeacherClassAssignment API
- Education Officer academic management permissions
- Teacher access to assigned classes
- CourseClass filtering by school, term, and teacher
- CourseClass search by school and teacher information
- Current teacher summary in CourseClass detail responses
- Validation for class dates and session durations
- Validation for teacher assignment date ranges
- Validation preventing overlapping teacher assignments on the same class
- Support for multiple teachers on the same class in different date ranges
- Soft deletion for School, Term, and CourseClass
- Automated tests for Phase 2 business rules and permissions

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

## User Roles

The system supports three business roles.

### Teacher

Represents an instructor.

Teachers have additional profile information:

- phone number
- emergency phone number

Teachers can access only the classes assigned to them.

### Education Officer

Responsible for academic management operations, including:

- schools
- terms
- course classes
- teacher-class assignments

### Finance Officer

Responsible for finance and payroll-related operations.

Phase 2 academic management endpoints are not available to the Finance Officer.

Each normal application user has one business role.

Django staff and superuser permissions are kept separate from these business roles.

## Authentication

Authentication is handled using JWT access and refresh tokens.

There is no public user registration endpoint.

Users are created by the system or through management commands.

### Obtain Tokens

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

### Refresh Access Token

```text
POST /api/token/refresh/
```

### Current User

The authenticated user can check their own account information and role using:

```text
GET /api/users/me/
```

Protected endpoints require an access token:

```text
Authorization: Bearer <ACCESS_TOKEN>
```

## Academic Models

### School

Stores school information.

Main fields:

- name
- address

A school is unique by the combination of its name and address.

School records use soft deletion.

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

Term records use soft deletion.

A term that already has course classes cannot currently be deleted.

### CourseClass

Represents a class running inside a specific school and term.

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

Current validation includes:

- end date cannot be before start date
- class dates must be inside the selected term
- session duration must be 60, 90, or 120 minutes
- school, term, and class code combination must be unique

CourseClass records use soft deletion.

### TeacherClassAssignment

Represents the relationship between a teacher and a class during a specific date range.

Main fields:

- teacher
- course class
- start date
- optional end date

The separate assignment model preserves teacher changes over the lifetime of a class.

Example:

```text
Teacher A: 2026-09-01 to 2026-10-31
Teacher B: 2026-11-01 to 2026-12-31
```

Current validation includes:

- assigned user must have the Teacher role
- start date cannot be after end date
- assignment dates must stay inside the CourseClass date range
- teacher assignment date ranges on the same class cannot overlap
- multiple sequential teacher assignments are allowed
- an open assignment must be closed before another overlapping assignment can become active

If `end_date` is omitted, the assignment is treated as continuing through the relevant class period.

## Academic API

All academic endpoints require authentication.

### Schools

```text
GET    /api/schools/
POST   /api/schools/
GET    /api/schools/<id>/
PUT    /api/schools/<id>/
PATCH  /api/schools/<id>/
DELETE /api/schools/<id>/
```

School management is restricted to the Education Officer.

Deleting a School performs a soft delete.

### Terms

```text
GET    /api/terms/
POST   /api/terms/
GET    /api/terms/<id>/
DELETE /api/terms/<id>/
```

Term management is restricted to the Education Officer.

`PUT` and `PATCH` are not currently exposed for Term.

Deleting an eligible Term performs a soft delete.

A Term that already has CourseClass records cannot currently be deleted.

### Course Classes

```text
GET    /api/course-classes/
POST   /api/course-classes/
GET    /api/course-classes/<id>/
PUT    /api/course-classes/<id>/
PATCH  /api/course-classes/<id>/
DELETE /api/course-classes/<id>/
```

Education Officers can manage course classes.

Teachers have read access only to classes assigned to them.

Deleting a CourseClass performs a soft delete.

### Teacher-Class Assignments

```text
GET    /api/teacher-class-assignments/
POST   /api/teacher-class-assignments/
GET    /api/teacher-class-assignments/<id>/
PUT    /api/teacher-class-assignments/<id>/
PATCH  /api/teacher-class-assignments/<id>/
DELETE /api/teacher-class-assignments/<id>/
```

Teacher-class assignment management is restricted to the Education Officer.

## CourseClass Filtering

CourseClass records can be filtered by school, term, or teacher.

Examples:

```text
GET /api/course-classes/?school=1
GET /api/course-classes/?term=1
GET /api/course-classes/?teacher=3
```

Filters can also be combined:

```text
GET /api/course-classes/?school=1&term=1&teacher=3
```

## CourseClass Search

CourseClass records support text search using the `search` query parameter.

Examples:

```text
GET /api/course-classes/?search=Maktab
GET /api/course-classes/?search=Vahid
```

Search currently covers:

- school name
- term type
- assigned teacher first name
- assigned teacher last name

## Current Teacher Summary

The detail response for a CourseClass includes a summary of the currently assigned teacher when an active assignment exists.

Example:

```text
GET /api/course-classes/1/
```

Example response fragment:

```json
{
  "id": 1,
  "title": "Python Backend",
  "class_code": "PY101",
  "current_teacher": {
    "id": 3,
    "first_name": "Vahid",
    "last_name": "Vahedi"
  }
}
```

If there is no active teacher assignment for the current date, `current_teacher` is returned as `null`.

## Teacher Class Visibility

A Teacher can only see CourseClass records connected to their own teacher assignments.

The current implementation includes assigned classes regardless of whether the assignment is current, past, or future.

Teachers cannot use these endpoints to manage schools, terms, teacher assignments, or other teachers' classes.

## Date Format

The current implementation uses **Gregorian dates** in API requests and responses.

Example:

```text
2026-09-01
```

## Soft Deletion

Soft deletion is currently implemented for:

- School
- Term
- CourseClass

A soft-deleted record remains in the database but is excluded from the normal API queryset.

TeacherClassAssignment currently uses the default delete behavior.

Deletion and locking rules may be extended in later phases when session reports introduce historical operational data.

## Role-Based Permissions

Reusable Django REST Framework permission classes include:

- `IsTeacher`
- `IsEducationOfficer`
- `IsFinanceOfficer`
- `IsEducationOfficerOrTeacher`

These permissions check authentication and the user's assigned business role.

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

Coverage reports are uploaded to Codecov through GitHub Actions.

Phase 2 tests cover the main academic workflow, including:

- role-based access boundaries
- School API behavior
- Term validation
- CourseClass validation
- valid session duration choices
- teacher assignment date validation
- multiple sequential teachers on one class
- overlapping teacher assignment rejection
- teacher visibility restrictions
- CourseClass filtering and search
- current teacher detail behavior

## Continuous Integration

GitHub Actions runs automatically on pushes and pull requests.

The CI workflow:

- starts a PostgreSQL service
- installs project dependencies
- runs Django system checks
- runs the test suite
- generates the coverage report
- uploads coverage results to Codecov

## Current Project Status

### Phase 1

Completed foundation:

- authentication and users
- role-based access control
- academic data models
- PostgreSQL integration
- automated testing
- CI and coverage reporting
- API documentation

### Phase 2

Implemented academic management workflow:

- School management
- Term management
- CourseClass management
- teacher-class assignment history
- multiple sequential teachers per class
- teacher-specific class visibility
- filtering and search
- current teacher summary
- Phase 2 validations and tests

## Current Limitations

The following features are intentionally not part of the current implementation:

- session scheduling and session reports
- report approval and rejection workflow
- late-report handling
- report status history
- payroll rates and monthly salary calculation

These workflows belong to later project phases.

Term updates through `PUT` and `PATCH` are not currently exposed.

Deletion and historical locking rules will be revisited when report data is introduced, so academic records connected to operational history can be protected appropriately.

## Next Phase

Phase 3 will introduce the session reporting workflow, including:

- scheduled course sessions
- teacher session reports
- report submission rules
- late report detection
- Education Officer approval and rejection
- report resubmission
- report-related permissions and tests
