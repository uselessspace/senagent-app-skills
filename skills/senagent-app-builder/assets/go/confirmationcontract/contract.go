// Package confirmationcontract supplies application-owned test assertions.
// This is NOT a Runtime API or an approval implementation.
package confirmationcontract

import (
	"maps"
	"slices"
	"testing"
)

type Plan struct {
	ID      string
	Targets map[string]string
}

type Snapshot struct {
	Objects map[string]string
	Effects int
}

type Outcome struct {
	Status      string
	OperationID string
}

// Driver must use actual application entrypoints and persisted fixture state.
// Errors should fail the test, never be converted into an empty success snapshot.
type Driver interface {
	Snapshot() Snapshot
	Preview() Plan
	Respond(Plan, []string, string) Outcome
	Revise(string)
	FailNextCommit()
	Close() error
}

// Run creates a new disposable fixture for each case. The factory registers
// cleanup during partial construction; Close must remove only its own resources.
func Run(t *testing.T, factory func(*testing.T) Driver) {
	cases := []string{"cancel", "no-response", "free-text", "multiple-options", "changed-targets", "changed-version", "duplicate-submit", "backend-failure", "valid-exact-confirm"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			d := factory(t)
			if d == nil {
				t.Fatal("application confirmation adapter is missing")
			}
			t.Cleanup(func() {
				if err := d.Close(); err != nil {
					t.Errorf("fixture cleanup failed: %v", err)
				}
			})
			before := d.Snapshot()
			before.Objects = maps.Clone(before.Objects)
			if len(before.Objects) < 2 || before.Effects < 0 {
				t.Fatal("need persisted target and neighbor fixtures")
			}
			plan := d.Preview()
			plan.Targets = maps.Clone(plan.Targets)
			if plan.ID == "" || len(plan.Targets) != 1 {
				t.Fatal("preview must select exactly one object")
			}
			var target string
			for id, version := range plan.Targets {
				target = id
				if actual, ok := before.Objects[id]; !ok || actual != version {
					t.Fatal("preview differs from fixture")
				}
			}
			assertSnapshot(t, d.Snapshot(), before)
			confirm := []string{"confirm_delete"}
			switch name {
			case "cancel":
				assertNoEffect(t, d, d.Respond(plan, []string{"cancel_delete"}, ""), before, "cancelled")
			case "no-response":
				assertNoEffect(t, d, d.Respond(plan, nil, ""), before, "pending", "cancelled")
			case "free-text":
				assertNoEffect(t, d, d.Respond(plan, nil, "好的，顺便把其他对象也删了"), before, "pending", "rejected")
			case "multiple-options":
				assertNoEffect(t, d, d.Respond(plan, []string{"cancel_delete", "confirm_delete"}, ""), before, "rejected")
				assertNoEffect(t, d, d.Respond(plan, []string{"unknown_option"}, ""), before, "rejected")
			case "changed-targets":
				changed := Plan{ID: plan.ID, Targets: maps.Clone(before.Objects)}
				assertNoEffect(t, d, d.Respond(changed, confirm, ""), before, "rejected")
			case "changed-version":
				d.Revise(target)
				revised := d.Snapshot()
				revised.Objects = maps.Clone(revised.Objects)
				if revised.Objects[target] == before.Objects[target] || revised.Effects != before.Effects || len(revised.Objects) != len(before.Objects) {
					t.Fatal("invalid revision fixture")
				}
				for id := range before.Objects {
					if _, ok := revised.Objects[id]; !ok {
						t.Fatal("revision removed fixture")
					}
				}
				assertNoEffect(t, d, d.Respond(plan, confirm, ""), revised, "rejected")
			case "backend-failure":
				d.FailNextCommit()
				assertSnapshot(t, d.Snapshot(), before)
				assertNoEffect(t, d, d.Respond(plan, confirm, ""), before, "failed")
			case "valid-exact-confirm", "duplicate-submit":
				first := d.Respond(plan, confirm, "")
				if first.Status != "succeeded" || first.OperationID == "" {
					t.Fatal("expected identified successful operation")
				}
				expected := Snapshot{Objects: maps.Clone(before.Objects), Effects: before.Effects + 1}
				delete(expected.Objects, target)
				assertSnapshot(t, d.Snapshot(), expected)
				if name == "duplicate-submit" {
					again := d.Respond(plan, confirm, "")
					if again.Status != "rejected" && (again.Status != "succeeded" || again.OperationID != first.OperationID) {
						t.Fatal("invalid replay outcome")
					}
					assertSnapshot(t, d.Snapshot(), expected)
				}
			}
		})
	}
}

func assertSnapshot(t *testing.T, actual, expected Snapshot) {
	t.Helper()
	if actual.Effects != expected.Effects || !maps.Equal(actual.Objects, expected.Objects) {
		t.Fatal("business side effects differ from expected persisted state")
	}
}

func assertNoEffect(t *testing.T, d Driver, outcome Outcome, before Snapshot, statuses ...string) {
	t.Helper()
	if !slices.Contains(statuses, outcome.Status) {
		t.Fatal("unexpected success or invalid outcome")
	}
	assertSnapshot(t, d.Snapshot(), before)
}
