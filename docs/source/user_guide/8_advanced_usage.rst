Advanced Usage of PyReason
===========================

PyReason is a powerful tool that can be used to reason over complex systems. This section outlines some advanced usage of PyReason.

Reasoning Convergence
---------------------
PyReason uses a fixed point iteration algorithm to reason over the graph. This means that the reasoning process will continue
until the graph reaches a fixed point, i.e., no new facts can be inferred. The fixed point iteration algorithm is guaranteed to converge for acyclic graphs.
However, for cyclic graphs, the algorithm may not converge, and the user may need to set certain values to ensure convergence.
The reasoner contains a few settings that can be used to control the convergence of the reasoning process, and can be set when calling
``pr.reason(...)``

1. ``convergence_threshold`` **(int, optional)**: The convergence threshold is the maximum number of interpretations that have changed between timesteps or fixed point operations until considered convergent. Program will end at convergence. -1 => no changes, perfect convergence, defaults to -1
2. ``convergence_bound_threshold`` **(float, optional)**: The convergence bound threshold is the maximum difference between the bounds of the interpretations at each timestep or fixed point operation until considered convergent. Program will end at convergence. -1 => no changes, perfect convergence, defaults to -1

Reasoning Multiple Times
-------------------------
PyReason allows you to reason over the graph multiple times. This can be useful when you want to reason over the graph iteratively
and add facts that were not available before. To reason over the graph multiple times, you can set ``again=True`` in ``pr.reason(again=True)``.
To specify additional facts, use the ``facts`` parameter in ``pr.reason(...)``. These parameters allow you to add additional
facts to the graph before reasoning again. The facts are specified as a list of PyReason facts.

.. note::
    When reasoning multiple times, the time continues to increment. Therefore any facts that are added should take this into account.
    The timestep parameter specifies how many additional timesteps to reason. For example, if the initial reasoning converges at
    timestep 5, and you want to reason for 3 more timesteps, you can set ``timestep=3`` in ``pr.reason(timestep=3, again=True, facts=[some_new_fact])``.
