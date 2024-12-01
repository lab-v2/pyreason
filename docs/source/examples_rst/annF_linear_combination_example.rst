Linear Combination Annotation Function Example
===================================================

.. code:: python

    # Test if annotation functions work
    import pyreason as pr
    import numba
    import numpy as np
    import networkx as nx



    @numba.njit
        def map_to_unit_interval(value, lower, upper):
            """
            Map a value from the interval [lower, upper] to the interval [0, 1].
            The formula is f(t) = c + ((d - c) / (b - a)) * (t - a),
            where a = lower, b = upper, c = 0, and d = 1.
            """
            if upper == lower:
                return 0  # Avoid division by zero if upper == lower
            return (value - lower) / (upper - lower)


        @numba.njit
        def lin_comb_ann_fn(annotations, weights):
            sum_lower_comb = 0
            sum_upper_comb = 0
            num_atoms = 0
            constant = 0.2
            
            # Iterate over the clauses in the rule
            for clause in annotations:
                for atom in clause:
                    # Map the atom's lower and upper bounds to the interval [0, 1]
                    mapped_lower = map_to_unit_interval(atom.lower, 0, 1)
                    mapped_upper = map_to_unit_interval(atom.upper, 0, 1)

                    # Apply the weights to the lower and upper bounds, and accumulate
                    sum_lower_comb += constant * mapped_lower
                    sum_upper_comb += constant * mapped_upper
                    num_atoms += 1

            # Return the weighted linear combination of the lower and upper bounds
            return sum_lower_comb, sum_upper_comb



        # Function to run the test
        def linear_combination_annotation_function():

            # Reset PyReason before starting the test
            pr.reset()
            pr.reset_rules()

            pr.settings.allow_ground_rules = True


            # Add facts (P(A) and P(B) with bounds)
            pr.add_fact(pr.Fact('P(A) : [.3, 1]'))
            pr.add_fact(pr.Fact('P(B) : [.2, 1]'))
            

            # Register the custom annotation function with PyReason
            pr.add_annotation_function(lin_comb_ann_fn)
            
            # Define a rule that uses this linear combination function
            pr.add_rule(pr.Rule('linear_combination_function(A, B):lin_comb_ann_fn <- P(A):[0, 1], P(B):[0, 1]', infer_edges=True))

            # Perform reasoning for 1 timestep
            interpretation = pr.reason(timesteps=1)

            # Filter the results for the computed 'linear_combination_function' edges
            dataframes = pr.filter_and_sort_edges(interpretation, ['linear_combination_function'])

            # Print the resulting dataframes for each timestep
            for t, df in enumerate(dataframes):
                print(f'TIMESTEP - {t}')
                print(df)
                print()

            # Assert that the linear combination function gives the expected result (adjusted for weights)
            # Example assertion based on weights and bounds; adjust the expected result based on the weights
            assert interpretation.query('linear_combination_function(A, B) : [0.1, 0.4]'), 'Linear combination function should be [0.105, 1]'

        # Run the test function
        linear_combination_annotation_function()