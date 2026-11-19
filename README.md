# Course Registration and Waitlist Service

## Overview

This project implements a bounded course-registration service using Python.

It supports learner enrolment, course withdrawal and FIFO waitlist promotion while enforcing prerequisite eligibility, capacity limits, duplicate prevention and state consistency.

The implementation was developed with AI assistance. Engineering decisions, trade-offs, code review and final test verification were evaluated against the assessment requirements.

## Features

- Enrol eligible learners when course capacity is available.
- Add eligible learners to the waitlist when the course is full.
- Prevent duplicate enrolment and waitlist requests.
- Drop an enrolled learner.
- Promote the earliest eligible waitlisted learner when a seat becomes available.
- Skip but retain ineligible learners during promotion.
- Update prerequisite status for waitlisted learners.
- Reject invalid learner IDs and prerequisite values.
- Protect shared state using thread synchronization.
- Validate internal course-state invariants.

## Technology

- Python 3.9.6 or later
- Python standard library
- `dataclasses`
- `threading.RLock`
- `unittest`

No third-party runtime dependencies are required.

## Project Structure

```text
course-waitlist-assessment/
├── docs/
│   ├── design-specification.md
│   └── ai-use-record.md
├── src/
│   ├── __init__.py
│   └── course_waitlist.py
├── tests/
│   ├── __init__.py
│   └── test_course_waitlist.py
├── README.md
└── requirements-dev.txt
```

## Setup

### Prerequisites

Ensure Python 3.9.6 or later is installed.

Check the installed version:

```bash
python3 --version
```

No additional package installation is required to run the service or its tests.

## Run the Automated Tests

From the project root directory, execute:

```bash
python3 -m unittest -v
```

Alternatively, run test discovery explicitly:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

### Final Verification Result

The final recorded test execution completed successfully:

```text
Ran 23 tests in 0.001s

OK
```

All 23 tests passed, with zero failures and zero errors.

The test suite covers:

- Successful enrolment.
- Full-capacity waitlisting.
- Duplicate enrolment prevention.
- Duplicate waitlist prevention.
- Prerequisite eligibility.
- Prerequisite updates.
- FIFO promotion.
- Skipping and retaining ineligible waitlisted learners.
- Withdrawal and repeated withdrawal.
- Invalid learner IDs and names.
- Invalid prerequisite values.
- Initial-state invariant validation.
- Concurrent enrolment and capacity protection.
- Service-boundary validation for invalid learner IDs.
- State preservation after rejected invalid requests.

## Service Behaviour

The main service class is `EnrollmentService`.

### Enrol a learner

```python
result = service.enroll("L1")
```

Possible outcomes include:

- `ENROLLED`
- `WAITLISTED`
- `INVALID_LEARNER_ID`
- `LEARNER_NOT_FOUND`
- `ALREADY_ENROLLED`
- `ALREADY_WAITLISTED`
- `INELIGIBLE`

### Drop an enrolled learner

```python
result = service.drop("L1")
```

Possible outcomes include:

- `DROPPED`
- `DROPPED_AND_PROMOTED`
- `INVALID_LEARNER_ID`
- `NOT_ENROLLED`

### Update prerequisite status

```python
result = service.update_prerequisite_status("L3", True)
```

Possible outcomes include:

- `PREREQUISITE_UPDATED`
- `INVALID_LEARNER_ID`
- `LEARNER_NOT_FOUND`
- `INVALID_PREREQUISITE_STATUS`
- `PREREQUISITE_UPDATE_REJECTED`

Each operation returns a `ServiceResult` containing success status, a result code and a human-readable message.

## Key Engineering Decisions

### Waitlist Policy

The service follows FIFO ordering among eligible learners.

If an ineligible learner reaches the front of the waitlist, that learner is skipped but retained. The service continues checking the queue for the earliest eligible learner.

### Prerequisite Model

Prerequisite eligibility is represented by a Boolean field on the learner model.

This keeps the model proportionate to the single-course assessment scope.

### Concurrency

A `threading.RLock` protects enrolment, withdrawal, promotion and prerequisite updates within a shared service instance.

This supports concurrent threads within one process. It does not provide distributed or multi-process coordination.

### Input Validation

Learner IDs are validated at both the data-model and service boundaries.

Invalid IDs return `INVALID_LEARNER_ID` rather than causing unexpected dictionary lookup errors.

Rejected invalid-ID requests do not modify the relevant state.

### Persistence

The implementation uses in-memory data structures. State is not retained after the process exits.

## Limitations

This implementation is intentionally limited to the assessment requirements.

It does not include:

- Database persistence.
- Distributed transactions or locking.
- Multi-process concurrency management.
- User interfaces.
- External identity integrations.
- Payment processing.
- Multiple course offerings or academic terms.
- Production monitoring and audit infrastructure.

Internal state invariants use Python assertions, which can be disabled when Python runs with optimization enabled.

These limitations would need to be addressed before considering the service for production deployment.

## Documentation

Additional design and assessment information is available in:

- `docs/design-specification.md` — architecture, data model, business rules, invariants, concurrency, assumptions and limitations.
- `docs/ai-use-record.md` — AI-assisted engineering activities, decisions, review and verification evidence.

## Assessment Summary

The project delivers the required bounded course-registration and waitlist functionality, supported by focused automated tests and documented engineering decisions.

The final recorded verification result is **23 passing tests**.