.. _inconsistent_predicate_list:

Inconsistent Predicate List
===========================

In this section we detail how we can use inconsistent predicate lists to identify inconsistencies in the graph during reasoning.
For more information on Inconsistencies and the Inconsistent Predicates list, see :ref:`here <inconsistent_predicate>`.

For this example, assume we have two inconsistent predicates, "sick" and "healthy". To be able to model this in PyReason
such that when one predicate has a certain bound ``[l, u]``, the other predicate is given a bound ``[1-u, 1-l]`` automatically,
we add the predicates to the **inconsistent predicate list**.

This can be done by using the following code:

.. code-block:: python

    import pyreason as pr
    pr.add_inconsistent_predicate('sick', 'healthy')

This allows PyReason to automatically update the bounds of the predicates in the inconsistent predicate list to the
negation of a predicate that is updated.