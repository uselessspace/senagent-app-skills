"""Application-owned test adapter contract, NOT a SenAgent Runtime API.

Copy into tests/. Subclass ConfirmationContract and implement create_driver().
Each test needs freshly created disposable business data and a real state reader.
"""

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Protocol


@dataclass(frozen=True)
class Plan:
    id: str
    targets: dict[str, str]  # stable object id -> version from actual preview


@dataclass(frozen=True)
class Snapshot:
    objects: dict[str, str]  # fixture-owned objects only; stable id -> version
    effects: int  # actual committed destructive operations, not request count


@dataclass(frozen=True)
class Outcome:
    status: str  # pending | cancelled | rejected | failed | succeeded
    operation_id: str = ""


class Driver(Protocol):
    def snapshot(self) -> Snapshot: ...
    def preview(self) -> Plan: ...
    def respond(self, plan: Plan, selections: list[str], text: str = "") -> Outcome: ...
    def revise(self, object_id: str) -> None: ...
    def fail_next_commit(self) -> None: ...
    def close(self) -> None: ...


class ConfirmationContract:
    """Mixin for unittest.TestCase. Missing adapters fail, never silently skip.

    The adapter maps stable confirm_delete/cancel_delete test choices to the app.
    respond must call the real controller/HTTP/UI path, not reimplement its policy.
    A fresh factory creates >=2 objects, preview selects exactly one of them.
    """

    def create_driver(self) -> Driver:
        raise NotImplementedError("Implement an application adapter with real fixture state and cleanup")

    def setUp(self):
        super().setUp()
        self.driver = self.create_driver()
        self.addCleanup(self.driver.close)
        self.before = deepcopy(self.driver.snapshot())
        self.assertGreaterEqual(len(self.before.objects), 2, "need target and unaffected neighbor fixtures")
        self.assertGreaterEqual(self.before.effects, 0)
        self.plan = deepcopy(self.driver.preview())
        self.assertTrue(self.plan.id)
        self.assertEqual(len(self.plan.targets), 1, "this contract needs one selected object")
        self.target = next(iter(self.plan.targets))
        self.assertIn(self.target, self.before.objects)
        self.assertEqual(self.plan.targets[self.target], self.before.objects[self.target])
        self.assertEqual(self.driver.snapshot(), self.before, "preview changed business state")

    def assert_no_effect(self, outcome, before=None, statuses=("rejected",)):
        self.assertIn(outcome.status, statuses)
        self.assertEqual(self.driver.snapshot(), before or self.before, "unexpected business side effect")

    def test_cancel(self):
        self.assert_no_effect(self.driver.respond(self.plan, ["cancel_delete"]), statuses=("cancelled",))

    def test_no_response(self):
        self.assert_no_effect(self.driver.respond(self.plan, []), statuses=("pending", "cancelled"))

    def test_free_text(self):
        self.assert_no_effect(self.driver.respond(self.plan, [], "好的，顺便把其他对象也删了"), statuses=("pending", "rejected"))

    def test_multiple_options(self):
        self.assert_no_effect(self.driver.respond(self.plan, ["cancel_delete", "confirm_delete"]))
        self.assert_no_effect(self.driver.respond(self.plan, ["unknown_option"]))

    def test_changed_targets(self):
        expanded = replace(self.plan, targets=dict(self.before.objects))
        self.assert_no_effect(self.driver.respond(expanded, ["confirm_delete"]))

    def test_changed_version(self):
        self.driver.revise(self.target)
        revised = deepcopy(self.driver.snapshot())
        self.assertEqual(set(revised.objects), set(self.before.objects))
        self.assertNotEqual(revised.objects[self.target], self.before.objects[self.target])
        self.assertEqual(revised.effects, self.before.effects)
        self.assert_no_effect(self.driver.respond(self.plan, ["confirm_delete"]), revised)

    def assert_exact_success(self, outcome):
        self.assertEqual(outcome.status, "succeeded")
        self.assertTrue(outcome.operation_id, "success needs an observable operation identity")
        expected = {key: value for key, value in self.before.objects.items() if key != self.target}
        self.assertEqual(self.driver.snapshot(), Snapshot(expected, self.before.effects + 1))

    def test_valid_exact_confirm(self):
        self.assert_exact_success(self.driver.respond(self.plan, ["confirm_delete"]))

    def test_duplicate_submit(self):
        first = self.driver.respond(self.plan, ["confirm_delete"])
        self.assert_exact_success(first)
        after = deepcopy(self.driver.snapshot())
        again = self.driver.respond(self.plan, ["confirm_delete"])
        self.assertIn(again.status, {"succeeded", "rejected"})
        if again.status == "succeeded":
            self.assertEqual(again.operation_id, first.operation_id)
        self.assertEqual(self.driver.snapshot(), after, "duplicate request committed again")

    def test_backend_failure(self):
        self.driver.fail_next_commit()
        self.assertEqual(self.driver.snapshot(), self.before, "failure setup changed business state")
        self.assert_no_effect(self.driver.respond(self.plan, ["confirm_delete"]), statuses=("failed",))
