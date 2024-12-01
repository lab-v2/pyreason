
Average Annotation Function Example
=====================================

.. code:: python

    # Test if annotation functions work
    import pyreason as pr
    import numba
    import numpy as np
    import networkx as nx




    @numba.njit
    def avg_ann_fn(annotations, weights):
        # annotations contains the bounds of the atoms that were used to ground the rule. It is a nested list that contains a list for each clause
        # You can access for example the first grounded atom's bound by doing: annotations[0][0].lower or annotations[0][0].upper

        # We want the normalised sum of the bounds of the grounded atoms
        sum_upper_bounds = 0
        sum_lower_bounds = 0
        num_atoms = 0
        for clause in annotations:
            for atom in clause:
                sum_lower_bounds += atom.lower
                sum_upper_bounds += atom.upper
                num_atoms += 1

        a = sum_lower_bounds / num_atoms
        b = sum_upper_bounds / num_atoms
        return a, b



    #Annotation function that returns average of both upper and lower bounds
    def average_annotation_function():
        # Reset PyReason
        pr.reset()
        pr.reset_rules()

        pr.settings.allow_ground_rules = True

        pr.add_fact(pr.Fact('P(A) : [0.01, 1]'))
        pr.add_fact(pr.Fact('P(B) : [0.2, 1]'))
        pr.add_annotation_function(avg_ann_fn)
        pr.add_rule(pr.Rule('average_function(A, B):avg_ann_fn <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))

        interpretation = pr.reason(timesteps=1)

        dataframes = pr.filter_and_sort_edges(interpretation, ['average_function'])
        for t, df in enumerate(dataframes):
            print(f'TIMESTEP - {t}')
            print(df)
            print()

        assert interpretation.query('average_function(A, B) : [0.105, 1]'), 'Average function should be [0.105, 1]'

    average_annotation_function()

