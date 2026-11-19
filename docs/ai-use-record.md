# AI-Assisted Engineering Use Record
## Course Registration and Waitlist Assessment

### 1. Purpose

This document records how I used AI as an engineering assistant during the design, implementation, testing and review of the course-registration and waitlist service.

My objective was to use AI to accelerate engineering activities while retaining responsibility for technical decisions, implementation review, trade-off evaluation and independent verification.

AI assistance was used as a supporting engineering tool. The final implementation decisions and verification remain my responsibility.

### 2. Engineering Approach

I approached the assessment in the following stages:

1. Reviewed the assessment requirements and identified the required functional scope and deliverables.
2. Decomposed the problem into learner modelling, course capacity, enrolment, waitlist management, withdrawal, promotion and validation.
3. Evaluated design alternatives and selected an implementation proportionate to the bounded assessment.
4. Implemented the service and focused automated tests.
5. Reviewed potential edge cases and engineering risks.
6. Executed the complete automated test suite.
7. Reviewed the documentation against the final implementation.

I used AI to support reasoning, challenge assumptions, suggest implementation approaches and identify potential gaps.

### 3. AI-Assisted Activities and Decisions

The following records summarize the principal AI-assisted engineering activities. They are summaries of the prompts and interactions rather than verbatim transcripts.

#### Activity 1: Requirement Analysis and Task Decomposition

**Prompt summary**

Help analyse the course-registration assessment requirements, identify the implementation scope and break the work into manageable engineering steps.

**AI assistance**

AI helped organize the assessment into functional requirements, acceptance criteria, implementation tasks, test scenarios and deliverables.

**My decision**

I retained the assessment's bounded scope and avoided adding unrelated capabilities such as a user interface, payment integration, external identity services or a database.

**Impact**

This established a focused implementation plan and kept the solution aligned with the assessment.

#### Activity 2: Waitlist Eligibility and Promotion Policy

**Prompt summary**

Evaluate alternative approaches for handling an ineligible learner who reaches the front of a course waitlist.

**AI assistance**

AI explained the trade-offs between retaining an ineligible learner at the front of the queue and skipping that learner while continuing to search for the next eligible learner.

**My decision**

I selected the policy to skip but retain the ineligible learner.

The service continues through the waitlist and promotes the earliest currently eligible learner. Ineligible learners retain their queue position and can be considered again when their prerequisite status changes.

**Impact**

This decision was implemented in the promotion logic and verified through a focused automated test.

#### Activity 3: Prerequisite Data Model

**Prompt summary**

Evaluate a simple Boolean prerequisite model against a more complex prerequisite representation for the bounded assessment.

**AI assistance**

AI outlined the simplicity and limitations of representing prerequisite eligibility using a Boolean attribute.

**My decision**

I selected a Boolean `prerequisite_met` field on the learner model.

This was proportionate to the single-course scope and avoided introducing an unnecessary prerequisite engine.

**Impact**

The decision informed the learner data model, enrolment checks and promotion eligibility checks.

#### Activity 4: Concurrency Control

**Prompt summary**

Evaluate concurrency-control alternatives for a bounded Python implementation of course enrolment and waitlist promotion.

**AI assistance**

AI explained the trade-offs between synchronization within one process and database-backed transactional controls.

**My decision**

I selected `threading.RLock` to protect operations that modify shared state.

The lock is applied to enrolment, withdrawal and promotion, and prerequisite updates.

I documented that this approach protects threads sharing one service instance but does not provide distributed or multi-process coordination.

**Impact**

The decision informed the service implementation and a focused concurrent-enrolment test.

#### Activity 5: Input Validation and State Protection

**Prompt summary**

Review the service for invalid inputs, duplicate requests, state consistency and possible failure scenarios.

**AI assistance**

AI helped identify validation requirements for learner IDs, names and prerequisite values, and suggested explicit checks for course-state invariants.

**My decision**

I implemented:

- Non-empty string validation for learner IDs and names.
- Strict Boolean validation for prerequisite status.
- Duplicate enrolment and waitlist checks.
- State invariant checks for capacity, duplicates, eligibility and enrolled/waitlisted separation.
- Rejection of prerequisite changes that would make an enrolled learner ineligible.

**Impact**

These decisions strengthened the data model and service behaviour and informed the automated tests.

#### Activity 6: Service-Boundary Validation Review

**Prompt summary**

Review the completed service implementation for invalid requests that might bypass data-model validation, particularly non-string or unhashable learner IDs.

**AI assistance**

AI identified that dictionary lookups using an unhashable learner ID, such as a list, could raise an unhandled `TypeError` before the service returned a structured result.

AI recommended consistent learner-ID validation at the beginning of each public service operation.

**My decision**

I accepted this improvement and introduced a shared `_is_valid_learner_id()` helper.

The validation is applied to:

- `enroll()`
- `drop()`
- `update_prerequisite_status()`

Invalid IDs return `INVALID_LEARNER_ID` with a clear message. The rejected operations do not change the relevant course or learner state.

**Impact**

The service now validates input independently at its public boundary instead of relying only on learner-object construction.

I added three focused tests to verify this behaviour across all three operations.

### 4. Implementation and Review Responsibilities

AI assistance informed the implementation and review process, but I retained responsibility for:

- Interpreting the assessment requirements.
- Selecting the waitlist eligibility policy.
- Selecting the prerequisite representation.
- Evaluating concurrency-control trade-offs.
- Reviewing suggested implementation approaches.
- Deciding which recommendations were appropriate for the assessment scope.
- Ensuring that documented limitations accurately reflected the implementation.
- Running the automated tests and evaluating their results.

I did not treat AI-generated suggestions as automatically correct. I reviewed them against the requirements, implementation scope and expected engineering behaviour.

### 5. Verification Evidence

I used Python's standard-library `unittest` framework to independently execute the automated test suite.

The final command was:

`python3 -m unittest -v`

**Final execution result:**

- Tests executed: 23
- Tests passed: 23
- Failures: 0
- Errors: 0

The tests verify:

- Successful enrolment and full-capacity waitlisting.
- Duplicate enrolment and duplicate waitlist prevention.
- Prerequisite eligibility and updates.
- FIFO promotion.
- Skipping and retaining ineligible learners.
- Withdrawal and repeated withdrawal handling.
- Invalid learner and prerequisite data.
- Initial-state invariant checks.
- Concurrent enrolment and capacity protection.
- Service-boundary validation for invalid IDs across enrolment, withdrawal and prerequisite updates.
- Preservation of relevant state when invalid requests are rejected.

The final test output ended with `OK`.

This verification provides evidence that the implemented scenarios covered by the suite passed. It does not establish production readiness or distributed concurrency guarantees.

### 6. Deliverables Informed by AI Assistance

| Deliverable | AI assistance and my contribution |
|---|---|
| `src/course_waitlist.py` | Design discussion, implementation guidance, validation review and refinement |
| `tests/test_course_waitlist.py` | Test-scenario identification, edge-case review and additional validation tests |
| `docs/design-specification.md` | Structuring design decisions, assumptions, invariants and limitations |
| `README.md` | Setup, execution, project structure and usage documentation |
| `docs/ai-use-record.md` | Recording AI-assisted activities, decisions and verification evidence |

### 7. Limitations and Further Considerations

The implementation deliberately uses an in-memory store and process-level thread synchronization.

It does not implement:

- Durable database persistence.
- Distributed locking.
- Multi-process or multi-instance concurrency control.
- Production authentication or authorization.
- Operational monitoring or audit logging.
- A configurable prerequisite policy engine.

The use of Python assertions for internal invariant checks is also a development-oriented choice; assertions can be disabled when Python runs with optimization enabled.

These limitations are documented in the design specification and are appropriate to acknowledge for a bounded assessment implementation.

### 8. Reflection

This assessment reinforced the importance of treating AI as an engineering assistant rather than a substitute for engineering judgement.

The most useful contributions came from structured requirement analysis, evaluating design alternatives, identifying edge cases and reviewing the implementation against expected behaviour.

The service-boundary validation review was particularly useful because it highlighted a gap that was not exposed by the initial test suite.

I evaluated the recommendation, adopted the correction, added focused tests and reran the complete test suite.

My approach throughout was to use AI to improve the quality and efficiency of engineering work while retaining accountability for design choices, implementation quality and verification.

### 9. Final Statement

The assessment demonstrates an AI-assisted engineering workflow covering requirement decomposition, design evaluation, implementation, test development, technical review and independent verification.

The final implementation passed all 23 automated tests executed in the assessment environment.

The solution remains intentionally bounded, with production-related limitations and potential future improvements explicitly documented.