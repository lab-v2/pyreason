"""Reproduce the behavioral difference between regular and parallel reasoning
modes when combining minimized predicates with negated clauses.

Scenario:
  - Graph: A -> B (edge predicate stepFrom)
  - hackerControl is registered as a minimized predicate
  - hackerControl(A) = [1,1], hackerControl(B) = [0,1] (unknown)
  - Rule: blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)

Expected behavior (regular & fp modes):
  - hackerControl(B) bounds [0,1] are "minimized" to [0,0] in satisfaction checks
  - [0,0] satisfies ~hackerControl (which requires [0,0])
  - blocked(B) fires -> [1,1]

Observed behavior (parallel mode):
  - blocked(B) does NOT fire
  - This script runs the same setup under all three modes and prints results
    side-by-side so the discrepancy can be investigated.
"""
import pyreason as pr
import networkx as nx


def build_graph():
    g = nx.DiGraph()
    g.add_nodes_from(['A', 'B'])
    g.add_edge('A', 'B', stepFrom=1)
    return g


def run_mode(mode):
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.verbose = False
    pr.settings.atom_trace = True

    if mode == "fp":
        pr.settings.fp_version = True
    elif mode == "parallel":
        pr.settings.parallel_computing = True

    pr.load_graph(build_graph())

    pr.add_minimized_predicate('hackerControl')

    # Minimized predicate: hackerControl(B) unknown [0,1] should be treated as [0,0]
    pr.add_fact(pr.Fact('hackerControl(A)', 'hc_a'))
    pr.add_fact(pr.Fact('hackerControl(B):[0,1]', 'hc_b_unknown'))

    # Non-minimized control predicate for comparison
    # pr.add_fact(pr.Fact('otherPred(A)', 'op_a'))
    # pr.add_fact(pr.Fact('otherPred(B):[0,1]', 'op_b_unknown'))

    # Rule using negation on the minimized predicate:
    #   ~hackerControl(Y) requires [0,0]; minimized [0,1] -> [0,0] so this should fire.
    pr.add_rule(pr.Rule(
        'blocked(Y) <-1 stepFrom(X,Y), hackerControl(X), ~hackerControl(Y)',
        'minimized_rule',
    ))
    # Same rule, but on the NON-minimized predicate — should not fire in any mode.
    pr.add_rule(pr.Rule(
        'notBlocked(Y) <-1 stepFrom(X,Y), otherPred(X), ~otherPred(Y)',
        'non_minimized_rule',
    ))

    # A rule that only uses the non-negated minimized predicate (sanity check):
    #   hackerControl(Y) is [0,1] and the clause requires [1,1], so it should NOT fire.
    pr.add_rule(pr.Rule(
        'infected(Y) <-1 stepFrom(X,Y), hackerControl(X), hackerControl(Y)',
        'infected_rule',
    ))

    interpretation = pr.reason(timesteps=1)

    def extract(label):
        rows = []
        for t, df in enumerate(pr.filter_and_sort_nodes(interpretation, [label])):
            if len(df) > 0:
                for _, row in df.iterrows():
                    rows.append((t, row['component'], row[label]))
        return rows

    return {
        'blocked (minimized + neg)': extract('blocked'),
        'notBlocked (non-min + neg)': extract('notBlocked'),
        'infected (minimized + pos)': extract('infected'),
        'hackerControl': extract('hackerControl'),
        'otherPred': extract('otherPred'),
    }


def print_results(mode, results):
    header = f"=== MODE: {mode} ==="
    print(header)
    for label, rows in results.items():
        print(f"  {label}:")
        if not rows:
            print("    (no rows)")
        else:
            for t, comp, bnd in rows:
                print(f"    t={t}  {comp}  {bnd}")
    print()


if __name__ == "__main__":
    all_results = {}
    for mode in ("regular", "fp", "parallel"):
        all_results[mode] = run_mode(mode)

    print()
    print("#" * 70)
    print("# Results summary")
    print("#" * 70)
    print()
    for mode, results in all_results.items():
        print_results(mode, results)

    # Side-by-side diff for the key query: blocked(B)
    print("=" * 70)
    print("KEY DIFFERENCE: blocked(B) (expected [1,1] — minimized ~hackerControl)")
    print("=" * 70)
    for mode, results in all_results.items():
        rows = results['blocked (minimized + neg)']
        b_rows = [r for r in rows if r[1] == 'B']
        status = b_rows[0][2] if b_rows else "NOT FIRED"
        print(f"  {mode:10s} -> blocked(B) = {status}")
