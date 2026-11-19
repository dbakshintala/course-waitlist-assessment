# Course Registration and Waitlist Service
## Design Specification

### 1. Purpose

This document describes the design of a bounded course-registration service that supports learner enrolment, course withdrawal and waitlist promotion for a single course offering.

The implementation demonstrates core engineering considerations including input validation, capacity management, prerequisite enforcement, duplicate prevention, FIFO waitlist processing, concurrency control and automated verification.

The solution uses a lightweight in-memory implementation, keeping the focus on the required business rules rather than introducing unnecessary infrastructure.

### 2. Scope

The implementation supports:

- Enrolling eligible learners in a course.
- Adding eligible learners to a waitlist when the course is full.
- Preventing duplicate enrolment and waitlist entries.
- Dropping an enrolled learner.
- Promoting the next eligible learner when a seat becomes available.
- Updating prerequisite status for learners.
- Validating requests and protecting course-state invariants.
- Handling concurrent requests within a single service instance.

The implementation is deliberately limited to one course offering.

The following are outside the scope:

- User interfaces and course catalogues.
- Payment processing.
- External identity or student-management integrations.
- Multiple courses or academic terms.
- Distributed deployment and multi-process coordination.
- Persistent database storage.
- Configurable prerequisite or waitlist policy engines.

### 3. Technology and Architecture

**Language:** Python 3.9.6 or later

**Dependencies:** Python standard library only.

The solution uses:

- `dataclasses` for lightweight domain models.
- `threading.RLock` for thread-level synchronization.
- `unittest` for automated testing.

The main components are:

| Component | Responsibility |
|---|---|
| `Learner` | Represents a learner and their prerequisite eligibility |
| `CourseOffering` | Represents course capacity, enrolled learners and waitlist |
| `ServiceResult` | Provides a consistent result structure for service operations |
| `EnrollmentService` | Implements enrolment, withdrawal, prerequisite updates and promotion |

The `EnrollmentService` acts as the service boundary and owns the business rules governing course registration.

### 4. Data Model

#### Learner

Each learner contains:

- `learner_id`: Unique learner identifier.
- `name`: Learner name.
- `prerequisite_met`: Boolean indicating whether the learner satisfies the course prerequisite.

Validation is performed when a learner object is created:

- Learner ID must be a non-empty string.
- Learner name must be a non-empty string.
- Prerequisite status must be a Boolean value.

#### CourseOffering

Each course offering contains:

- `course_id`: Course identifier.
- `course_name`: Course name.
- `capacity`: Maximum number of enrolled learners.
- `enrolled`: List of enrolled learner IDs.
- `waitlist`: Ordered list of waitlisted learner IDs.

Course capacity must be a positive integer.

The waitlist is maintained in insertion order to support FIFO processing.

#### ServiceResult

Each service operation returns:

- `success`: Indicates whether the operation succeeded.
- `code`: Machine-readable result code.
- `message`: Human-readable explanation.

This provides consistent feedback to callers without requiring them to interpret internal exceptions for expected business outcomes.

### 5. Service Operations

#### Enrolment

`enroll(learner_id)`

The service performs the following checks:

1. Validate that the learner ID is a non-empty string.
2. Confirm that the learner exists.
3. Reject learners who are already enrolled.
4. Reject learners who are already waitlisted.
5. Verify prerequisite eligibility.
6. Enrol the learner if capacity is available.
7. Otherwise, add the eligible learner to the waitlist.

Expected result codes include:

- `INVALID_LEARNER_ID`
- `LEARNER_NOT_FOUND`
- `ALREADY_ENROLLED`
- `ALREADY_WAITLISTED`
- `INELIGIBLE`
- `ENROLLED`
- `WAITLISTED`

#### Withdrawal

`drop(learner_id)`

The service:

1. Validates the learner ID.
2. Confirms that the learner is currently enrolled.
3. Removes the learner from the enrolled list.
4. Attempts to promote the next eligible waitlisted learner.
5. Validates the resulting course state.

Expected result codes include:

- `INVALID_LEARNER_ID`
- `NOT_ENROLLED`
- `DROPPED`
- `DROPPED_AND_PROMOTED`

Repeated withdrawal requests are rejected without changing course state.

#### Prerequisite Update

`update_prerequisite_status(learner_id, new_status)`

The service:

1. Validates the learner ID.
2. Confirms that the learner exists.
3. Validates that the new prerequisite status is a Boolean.
4. Prevents an enrolled learner from being made ineligible.
5. Updates the learner's prerequisite status.
6. Validates the resulting state.

An ineligible waitlisted learner may become eligible through an update and can then be considered for promotion.

Expected result codes include:

- `INVALID_LEARNER_ID`
- `LEARNER_NOT_FOUND`
- `INVALID_PREREQUISITE_STATUS`
- `PREREQUISITE_UPDATE_REJECTED`
- `PREREQUISITE_UPDATED`

### 6. Business Rules and Waitlist Policy

#### Prerequisite Policy

A learner must satisfy the prerequisite before enrolment or waitlist admission.

Prerequisite eligibility is represented by a Boolean value for this bounded implementation.

A learner who does not satisfy the prerequisite cannot be enrolled or added to the waitlist through the enrolment service.

#### Waitlist Promotion Policy

The implementation follows FIFO ordering among currently eligible waitlisted learners.

When a seat becomes available:

1. The service examines the waitlist from the beginning.
2. If the learner at the front is eligible, that learner is promoted.
3. If the learner is ineligible, the learner is skipped but retained on the waitlist.
4. The service continues until it finds the earliest eligible learner.
5. If no eligible learner is found, the seat remains vacant and the waitlist is retained.

Eligibility is evaluated at promotion time rather than assumed from the learner's original waitlist admission.

This policy preserves the original queue position of temporarily ineligible learners while allowing eligible learners further down the queue to use an available seat.

### 7. State Invariants

The service validates the following invariants:

1. The number of enrolled learners must never exceed course capacity.
2. The enrolled list must not contain duplicate learner IDs.
3. The waitlist must not contain duplicate learner IDs.
4. A learner cannot appear in both enrolled and waitlisted lists.
5. Every enrolled learner must exist in the learner collection.
6. Every enrolled learner must satisfy the prerequisite.
7. Every waitlisted learner must exist in the learner collection.

Invariants are checked during service initialization and after successful state mutations.

The implementation uses Python assertions for these internal consistency checks. Assertions are intended for development and verification; they are not a substitute for production-grade runtime validation because Python can disable assertions when run with optimization enabled.

### 8. Input Validation and Error Handling

Validation is performed at two levels:

**Data-model validation**

The `Learner` model rejects invalid learner IDs, names and prerequisite values during object creation.

**Service-boundary validation**

The public service operations validate learner IDs independently of the data model.

A learner ID must be a non-empty string. Invalid values, including `None`, lists, empty strings and whitespace-only strings, return an `INVALID_LEARNER_ID` result.

Rejected requests do not modify enrolment, waitlist or prerequisite state.

Expected business failures are represented through `ServiceResult` rather than being treated as unexpected system exceptions.

### 9. Concurrency and Synchronization

The service uses `threading.RLock` to protect operations that modify shared course state.

The lock is applied to:

- Enrolment.
- Withdrawal and waitlist promotion.
- Prerequisite updates.

This ensures that concurrent threads using the same service instance cannot simultaneously modify the course state in a way that exceeds capacity or creates duplicate entries.

An `RLock` is used to provide re-entrant thread synchronization within the service.

**Important limitation:** This implementation protects shared state only within a single Python process and service instance. It does not provide distributed locking, cross-process coordination or transactional guarantees across multiple application instances.

A production implementation would require database transactions, appropriate row-level or equivalent locking, and potentially optimistic concurrency controls.

### 10. Persistence

The solution uses in-memory Python objects and collections.

This is appropriate for the bounded assessment because it avoids introducing database infrastructure that is not required by the specification.

The data is not persistent. Restarting the application loses the course and learner state.

A production implementation would require durable storage and transactional state management.

### 11. Automated Testing and Verification

The implementation is verified using Python's standard-library `unittest` framework.

The final verified test execution completed successfully:

- Total tests: 23
- Passed: 23
- Failed: 0
- Errors: 0

Coverage includes:

- Successful enrolment.
- Enrolment when capacity is full.
- Duplicate enrolment prevention.
- Duplicate waitlist request prevention.
- Prerequisite enforcement.
- Prerequisite updates.
- FIFO waitlist promotion.
- Skipping and retaining ineligible waitlisted learners.
- Withdrawal and repeated withdrawal handling.
- Initial-state invariant validation.
- Invalid learner IDs and names.
- Invalid prerequisite values.
- Concurrent enrolment and capacity protection.
- Service-boundary validation for invalid IDs across enrolment, withdrawal and prerequisite updates.
- Verification that rejected invalid-ID requests do not change relevant state.

The concurrency test uses multiple threads against the same service instance and verifies that course capacity and waitlist uniqueness are maintained.

### 12. Design Trade-offs and Limitations

The implementation prioritizes correctness, clarity and focused verification within the assessment scope.

Key trade-offs include:

- A Boolean prerequisite model instead of a configurable prerequisite hierarchy.
- An in-memory store instead of a persistent database.
- A single-process re-entrant lock instead of distributed transaction management.
- Assertions for internal invariant checks, rather than production-grade invariant enforcement.
- A single course offering rather than a multi-course registration platform.

These choices keep the solution proportionate to the stated requirements.

### 13. Potential Future Improvements

If extended beyond the assessment scope, the solution could evolve to include:

- Persistent storage with transactional enrolment and promotion.
- Database-level concurrency controls.
- Audit history for enrolment and withdrawal events.
- Structured logging and operational metrics.
- API-level request validation and authentication.
- Multiple course offerings and academic terms.
- Configurable prerequisite rules.
- Resilient handling of failures during promotion.

These are potential future enhancements and are not represented as implemented capabilities.

### 14. Conclusion

The solution implements the required course-registration and waitlist behaviour using a focused service design.

It applies explicit business rules, validates inputs at both model and service boundaries, protects critical state transitions through synchronization and verifies the key scenarios through 23 passing automated tests.

The implementation deliberately avoids unnecessary infrastructure while documenting the limitations that would need to be addressed before production deployment.