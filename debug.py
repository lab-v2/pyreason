"""Debug script for test_annotation_function parallel mode issue."""
import pyreason as pr
from pyreason import Threshold
import numba
import numpy as np
from pyreason.scripts.numba_wrapper.numba_types.interval_type import closed


@numba.njit
def probability_func(annotations, weights):
    prob_A = annotations[0][0].lower
    prob_B = annotations[1][0].lower
    union_prob = prob_A + prob_B
    union_prob = np.round(union_prob, 3)
    return union_prob, 1


def main():
    # Setup parallel mode
    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.verbose = False  # Disable verbose to speed up
    pr.settings.parallel_computing = True
    pr.settings.allow_ground_rules = True

    print("Settings configured:")
    print(f"  parallel_computing: {pr.settings.parallel_computing}")
    print(f"  allow_ground_rules: {pr.settings.allow_ground_rules}")

    print("=" * 80)
    print("PARALLEL MODE DEBUG")
    print("=" * 80)

    # Add facts
    pr.add_fact(pr.Fact('P(A) : [0.01, 1]'))
    pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))

    # Add annotation function
    pr.add_annotation_function(probability_func)

    # Add rule
    pr.add_rule(pr.Rule('union_probability(A, B):probability_func <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))

    # Run reasoning
    print("\nRunning reasoning for 1 timestep...")
    interpretation = pr.reason(timesteps=1)

    # Display results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    dataframes = pr.filter_and_sort_edges(interpretation, ['union_probability'])
    for t, df in enumerate(dataframes):
        print(f'\nTIMESTEP - {t}')
        print(df)
        print()

    # Check what we actually got
    print("\n" + "=" * 80)
    print("QUERY RESULTS")
    print("=" * 80)

    # Try to query the actual value
    query_result = interpretation.query(pr.Query('union_probability(A, B) : [0.21, 1]'))
    print(f"\nQuery for [0.21, 1]: {query_result}")

    # Let's also try to see what value we actually got
    # Query with a wider range to see if it exists at all
    wider_query = interpretation.query(pr.Query('union_probability(A, B) : [0, 1]'))
    print(f"Query for [0, 1] (wider range): {wider_query}")

    # Get the actual edge data
    print("\n" + "=" * 80)
    print("DETAILED EDGE INSPECTION")
    print("=" * 80)

    # Access the interpretation's internal data to see actual values
    if hasattr(interpretation, 'get_dict'):
        edge_dict = interpretation.get_dict()
        print(f"\nEdge dictionary keys: {edge_dict.keys()}")
        if ('A', 'B') in edge_dict:
            print(f"\nEdge ('A', 'B') data:")
            for key, value in edge_dict[('A', 'B')].items():
                print(f"  {key}: {value}")

    # Alternative: inspect atoms directly
    if hasattr(interpretation, 'atoms'):
        print(f"\nAtoms available: {interpretation.atoms}")

    print("\n" + "=" * 80)
    print("EXPECTED vs ACTUAL")
    print("=" * 80)
    print(f"Expected: union_probability(A, B) with bounds [0.21, 1]")
    print(f"Actual: See dataframe above")


if __name__ == "__main__":
    main()
