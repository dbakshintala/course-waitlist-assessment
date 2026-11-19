
from dataclasses import dataclass, field
from threading import RLock


# -----------------------------
# Data Models
# -----------------------------

@dataclass
class Learner:
    learner_id: str
    name: str
    prerequisite_met: bool

    def __post_init__(self):
        if not isinstance(self.learner_id, str):
            raise ValueError("Learner ID must be a string.")

        if not self.learner_id.strip():
            raise ValueError("Learner ID cannot be empty.")

        if not isinstance(self.name, str):
            raise ValueError("Learner name must be a string.")

        if not self.name.strip():
            raise ValueError("Learner name cannot be empty.")

        if type(self.prerequisite_met) is not bool:
            raise ValueError(
                "prerequisite_met must be True or False."
            )


@dataclass
class CourseOffering:
    course_id: str
    course_name: str
    capacity: int
    enrolled: list = field(default_factory=list)
    waitlist: list = field(default_factory=list)

    def __post_init__(self):
        if type(self.capacity) is not int or self.capacity < 1:
            raise ValueError(
                "Course capacity must be a positive integer."
            )


@dataclass
class ServiceResult:
    success: bool
    code: str
    message: str


# -----------------------------
# Enrollment Service
# -----------------------------

class EnrollmentService:

    def __init__(self, course, learners):
        self.course = course
        self.learners = learners
        self.lock = RLock()

        self._validate_invariants()

    # -------------------------
    # Validate learner ID
    # -------------------------

    def _is_valid_learner_id(self, learner_id):
        return (
            isinstance(learner_id, str)
            and bool(learner_id.strip())
        )

    # -------------------------
    # Validate course invariants
    # -------------------------

    def _validate_invariants(self):

        enrolled = self.course.enrolled
        waitlist = self.course.waitlist

        assert len(enrolled) <= self.course.capacity, (
            "Course capacity exceeded."
        )

        assert len(enrolled) == len(set(enrolled)), (
            "Duplicate learner found in enrolled list."
        )

        assert len(waitlist) == len(set(waitlist)), (
            "Duplicate learner found in waitlist."
        )

        assert set(enrolled).isdisjoint(set(waitlist)), (
            "Learner cannot be both enrolled and waitlisted."
        )

        for learner_id in enrolled:

            learner = self.learners.get(learner_id)

            assert learner is not None, (
                f"Enrolled learner {learner_id} does not exist."
            )

            assert learner.prerequisite_met is True, (
                f"Enrolled learner {learner_id} is ineligible."
            )

        for learner_id in waitlist:
            assert learner_id in self.learners, (
                f"Waitlisted learner {learner_id} does not exist."
            )

    # -------------------------
    # Enrol a learner
    # -------------------------

    def enroll(self, learner_id):

        with self.lock:

            if not self._is_valid_learner_id(learner_id):
                return ServiceResult(
                    False,
                    "INVALID_LEARNER_ID",
                    "Learner ID must be a non-empty string."
                )

            learner = self.learners.get(learner_id)

            if learner is None:
                return ServiceResult(
                    False,
                    "LEARNER_NOT_FOUND",
                    "Learner does not exist."
                )

            if learner_id in self.course.enrolled:
                return ServiceResult(
                    False,
                    "ALREADY_ENROLLED",
                    "Learner is already enrolled."
                )

            if learner_id in self.course.waitlist:
                return ServiceResult(
                    False,
                    "ALREADY_WAITLISTED",
                    "Learner is already on the waitlist."
                )

            if not learner.prerequisite_met:
                return ServiceResult(
                    False,
                    "INELIGIBLE",
                    "Learner does not meet prerequisites."
                )

            if len(self.course.enrolled) < self.course.capacity:

                self.course.enrolled.append(learner_id)

                self._validate_invariants()

                return ServiceResult(
                    True,
                    "ENROLLED",
                    "Learner successfully enrolled."
                )

            self.course.waitlist.append(learner_id)

            self._validate_invariants()

            return ServiceResult(
                True,
                "WAITLISTED",
                "Course is full. Learner added to waitlist."
            )

    # -------------------------
    # Update prerequisite status
    # -------------------------

    def update_prerequisite_status(self, learner_id, new_status):

        with self.lock:

            if not self._is_valid_learner_id(learner_id):
                return ServiceResult(
                    False,
                    "INVALID_LEARNER_ID",
                    "Learner ID must be a non-empty string."
                )

            learner = self.learners.get(learner_id)

            if learner is None:
                return ServiceResult(
                    False,
                    "LEARNER_NOT_FOUND",
                    "Learner does not exist."
                )

            if type(new_status) is not bool:
                return ServiceResult(
                    False,
                    "INVALID_PREREQUISITE_STATUS",
                    "Prerequisite status must be True or False."
                )

            if (
                learner_id in self.course.enrolled
                and new_status is False
            ):
                return ServiceResult(
                    False,
                    "PREREQUISITE_UPDATE_REJECTED",
                    "Cannot make an enrolled learner ineligible."
                )

            learner.prerequisite_met = new_status

            self._validate_invariants()

            return ServiceResult(
                True,
                "PREREQUISITE_UPDATED",
                "Learner prerequisite status updated."
            )

    # -------------------------
    # Promote next eligible learner
    # -------------------------

    def _promote_next_eligible(self):

        # Caller must hold the service lock.
        for learner_id in list(self.course.waitlist):

            learner = self.learners.get(learner_id)

            # Skip ineligible learners but retain them.
            if learner is None or not learner.prerequisite_met:
                continue

            self.course.waitlist.remove(learner_id)
            self.course.enrolled.append(learner_id)

            return learner_id

        return None

    # -------------------------
    # Drop a learner
    # -------------------------

    def drop(self, learner_id):

        with self.lock:

            if not self._is_valid_learner_id(learner_id):
                return ServiceResult(
                    False,
                    "INVALID_LEARNER_ID",
                    "Learner ID must be a non-empty string."
                )

            if learner_id not in self.course.enrolled:
                return ServiceResult(
                    False,
                    "NOT_ENROLLED",
                    "Learner is not currently enrolled."
                )

            self.course.enrolled.remove(learner_id)

            promoted_id = self._promote_next_eligible()

            self._validate_invariants()

            if promoted_id is not None:
                return ServiceResult(
                    True,
                    "DROPPED_AND_PROMOTED",
                    f"Learner dropped. {promoted_id} was promoted."
                )

            return ServiceResult(
                True,
                "DROPPED",
                "Learner dropped. No eligible waitlisted learner found."
            )
