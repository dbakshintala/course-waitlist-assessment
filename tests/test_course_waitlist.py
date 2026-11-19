
import unittest
from threading import Thread

from src.course_waitlist import (
    Learner,
    CourseOffering,
    EnrollmentService,
)


class TestEnrollmentService(unittest.TestCase):

    def setUp(self):
        self.learners = {
            "L1": Learner("L1", "Alice", True),
            "L2": Learner("L2", "Bob", True),
            "L3": Learner("L3", "Charlie", True),
            "L4": Learner("L4", "David", False),
        }

        self.course = CourseOffering(
            "C1",
            "Python Programming",
            2
        )

        self.service = EnrollmentService(
            self.course,
            self.learners
        )

    def test_successful_enrollment(self):
        result = self.service.enroll("L1")

        self.assertTrue(result.success)
        self.assertEqual(result.code, "ENROLLED")
        self.assertIn("L1", self.course.enrolled)

    def test_full_course_adds_learner_to_waitlist(self):
        self.course.enrolled = ["L1", "L2"]

        result = self.service.enroll("L3")

        self.assertTrue(result.success)
        self.assertEqual(result.code, "WAITLISTED")
        self.assertEqual(self.course.waitlist, ["L3"])

    def test_ineligible_learner_cannot_enroll(self):
        result = self.service.enroll("L4")

        self.assertFalse(result.success)
        self.assertEqual(result.code, "INELIGIBLE")
        self.assertNotIn("L4", self.course.enrolled)
        self.assertNotIn("L4", self.course.waitlist)

    def test_prevents_duplicate_enrollment(self):
        self.service.enroll("L1")

        result = self.service.enroll("L1")

        self.assertFalse(result.success)
        self.assertEqual(result.code, "ALREADY_ENROLLED")
        self.assertEqual(self.course.enrolled.count("L1"), 1)

    def test_prevents_duplicate_waitlist_requests(self):
        self.course.enrolled = ["L1", "L2"]

        first_result = self.service.enroll("L3")
        second_result = self.service.enroll("L3")

        self.assertEqual(first_result.code, "WAITLISTED")
        self.assertEqual(second_result.code, "ALREADY_WAITLISTED")
        self.assertEqual(self.course.waitlist.count("L3"), 1)

    def test_drop_promotes_first_waitlisted_learner(self):
        self.course.enrolled = ["L1", "L2"]
        self.course.waitlist = ["L3"]

        result = self.service.drop("L1")

        self.assertTrue(result.success)
        self.assertEqual(result.code, "DROPPED_AND_PROMOTED")
        self.assertEqual(self.course.enrolled, ["L2", "L3"])
        self.assertEqual(self.course.waitlist, [])

    def test_skips_ineligible_learner_and_promotes_next_eligible(self):
        self.course.enrolled = ["L1", "L2"]
        self.course.waitlist = ["L4", "L3"]

        result = self.service.drop("L1")

        self.assertTrue(result.success)
        self.assertEqual(result.code, "DROPPED_AND_PROMOTED")
        self.assertEqual(self.course.enrolled, ["L2", "L3"])
        self.assertEqual(self.course.waitlist, ["L4"])

    def test_drop_learner_who_is_not_enrolled(self):
        result = self.service.drop("L3")

        self.assertFalse(result.success)
        self.assertEqual(result.code, "NOT_ENROLLED")
        self.assertEqual(self.course.enrolled, [])

    def test_repeated_drop_request_does_not_corrupt_state(self):
        self.service.enroll("L1")

        first_result = self.service.drop("L1")
        second_result = self.service.drop("L1")

        self.assertTrue(first_result.success)
        self.assertFalse(second_result.success)
        self.assertEqual(second_result.code, "NOT_ENROLLED")
        self.assertEqual(self.course.enrolled, [])

    def test_allows_prerequisite_update_for_waitlisted_learner(self):
        self.course.enrolled = ["L1", "L2"]
        self.course.waitlist = ["L4"]

        result = self.service.update_prerequisite_status(
            "L4",
            True
        )

        self.assertTrue(result.success)
        self.assertTrue(self.learners["L4"].prerequisite_met)

    def test_rejects_ineligible_update_for_enrolled_learner(self):
        self.course.enrolled = ["L1"]

        result = self.service.update_prerequisite_status(
            "L1",
            False
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.code,
            "PREREQUISITE_UPDATE_REJECTED"
        )
        self.assertTrue(self.learners["L1"].prerequisite_met)

    def test_rejects_invalid_prerequisite_status_update(self):
        original_status = self.learners["L1"].prerequisite_met

        result = self.service.update_prerequisite_status(
            "L1",
            "yes"
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.code,
            "INVALID_PREREQUISITE_STATUS"
        )
        self.assertEqual(
            self.learners["L1"].prerequisite_met,
            original_status
        )

    def test_rejects_prerequisite_update_for_unknown_learner(self):
        result = self.service.update_prerequisite_status(
            "UNKNOWN",
            True
        )

        self.assertFalse(result.success)
        self.assertEqual(result.code, "LEARNER_NOT_FOUND")

    def test_rejects_empty_learner_id(self):
        with self.assertRaises(ValueError):
            Learner("", "Alice", True)

    def test_rejects_non_string_learner_id(self):
        with self.assertRaises(ValueError):
            Learner(123, "Alice", True)

    def test_rejects_empty_learner_name(self):
        with self.assertRaises(ValueError):
            Learner("L5", "", True)

    def test_rejects_invalid_prerequisite_value(self):
        with self.assertRaises(ValueError):
            Learner("L5", "Eve", "yes")

    def test_rejects_initial_state_exceeding_capacity(self):
        self.course.enrolled = ["L1", "L2", "L3"]

        with self.assertRaises(AssertionError):
            EnrollmentService(self.course, self.learners)

    def test_detects_duplicate_enrolled_learners(self):
        self.course.enrolled = ["L1", "L1"]

        with self.assertRaises(AssertionError):
            EnrollmentService(self.course, self.learners)

    def test_concurrent_enrollment_respects_capacity(self):
        course = CourseOffering(
            "C2",
            "Concurrency Test",
            1
        )

        learners = {
            "L1": Learner("L1", "Alice", True),
            "L2": Learner("L2", "Bob", True),
            "L3": Learner("L3", "Charlie", True),
            "L4": Learner("L4", "David", True),
        }

        service = EnrollmentService(course, learners)

        threads = [
            Thread(target=service.enroll, args=(learner_id,))
            for learner_id in learners
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(course.enrolled), 1)
        self.assertEqual(len(course.waitlist), 3)
        self.assertEqual(len(set(course.enrolled)), 1)
        self.assertEqual(len(set(course.waitlist)), 3)

    # -------------------------
    # Additional service-boundary validation tests
    # -------------------------

    def test_enroll_rejects_invalid_learner_ids_without_changing_state(self):
        invalid_ids = [None, [], "", "   "]

        for learner_id in invalid_ids:
            with self.subTest(learner_id=repr(learner_id)):
                enrolled_before = list(self.course.enrolled)
                waitlist_before = list(self.course.waitlist)

                result = self.service.enroll(learner_id)

                self.assertFalse(result.success)
                self.assertEqual(result.code, "INVALID_LEARNER_ID")
                self.assertEqual(self.course.enrolled, enrolled_before)
                self.assertEqual(self.course.waitlist, waitlist_before)

    def test_prerequisite_update_rejects_invalid_learner_ids_without_changing_state(self):
        invalid_ids = [None, [], "", "   "]

        for learner_id in invalid_ids:
            with self.subTest(learner_id=repr(learner_id)):
                original_status = self.learners["L1"].prerequisite_met

                result = self.service.update_prerequisite_status(
                    learner_id,
                    False
                )

                self.assertFalse(result.success)
                self.assertEqual(result.code, "INVALID_LEARNER_ID")
                self.assertEqual(
                    self.learners["L1"].prerequisite_met,
                    original_status
                )
                self.assertEqual(self.course.enrolled, [])
                self.assertEqual(self.course.waitlist, [])

    def test_drop_rejects_invalid_learner_ids_without_changing_state(self):
        self.course.enrolled = ["L1"]
        self.course.waitlist = ["L2"]

        invalid_ids = [None, [], "", "   "]

        for learner_id in invalid_ids:
            with self.subTest(learner_id=repr(learner_id)):
                enrolled_before = list(self.course.enrolled)
                waitlist_before = list(self.course.waitlist)

                result = self.service.drop(learner_id)

                self.assertFalse(result.success)
                self.assertEqual(result.code, "INVALID_LEARNER_ID")
                self.assertEqual(self.course.enrolled, enrolled_before)
                self.assertEqual(self.course.waitlist, waitlist_before)


if __name__ == "__main__":
    unittest.main()
