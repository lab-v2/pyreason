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
To specify additional facts or rules, you can add them as you normally would using ``pr.add_fact`` and ``pr.add_rule``.

You can also clear the rules to use completely different ones with ``pr.clear_rules()``. This can be useful when you
want to reason over the graph with a new set of rules.

When reasoning multiple times, the time is reset to zero. Therefore any facts that are added should take this into account.
It is also possible to continue incrementing the time by running ``pr.reason(again=True, restart=False)``

.. note::
    When reasoning multiple times with ``restart=False``, the time continues to increment. Therefore any facts that are added should take this into account.
    The timestep parameter specifies how many additional timesteps to reason. For example, if the initial reasoning converges at
    timestep 5, and you want to reason for 3 more timesteps, you can set ``timestep=3`` in ``pr.reason(timestep=3, again=True)``.
    If you are specifying new facts, take this into account when setting their ``start_time`` and ``end_time``.

Interpretation Engines
----------------------

PyReason provides two interchangeable interpretation backends. The fixed-point (FP) engine mirrors the canonical numerical semantics
exactly, while the optimised engine implements the same convergence behaviour using an incremental execution strategy that trades a bit
of transparency for speed and lower memory usage. Both engines honour the same convergence criteria and, under identical rules and
settings, reach equivalent results. The difference lies in the way the fixed-point operator works. In the original version, the fixed-point
operator runs till convergence in each timestep, whereas in the FP version, the fixed-point runs till convergence on all timesteps at once.

.. list-table::
   :header-rows: 1

   * - Engine
     - Module
     - Primary characteristics
   * - Optimised interpretation
     - ``pyreason.scripts.interpretation.interpretation``
     - Default engine focused on runtime and memory efficiency. Updates the current interpretation in-place and maintains only the
       information required for the final trace utilities.
   * - Fixed point interpretation (FP)
     - ``pyreason.scripts.interpretation.interpretation_fp``
     - Classical fixed-point semantics that materialise each timestep explicitly. Easier to audit when validating rules or porting
       existing fixed-point workflows.

Choosing the engine
~~~~~~~~~~~~~~~~~~~

The engine is selected through ``settings.fp_version`` prior to calling ``pr.reason``:

.. code:: python

    import pyreason as pr

    pr.reset_settings()
    pr.settings.fp_version = False  # Optimised engine (default)
    interpretation = pr.reason(timesteps=3)

    pr.reset()
    pr.reset_settings()
    pr.settings.fp_version = True   # Switch to the FP engine
    interpretation_fp = pr.reason(timesteps=3)

Shared behaviour
~~~~~~~~~~~~~~~~

* Rule grounding, thresholds, annotation functions, and head functions behave identically.
* Convergence controls (perfect convergence, ``delta_bound``, ``delta_interpretation``) produce the same stop conditions.
* The public ``Interpretation`` API—including ``query()``, ``get_dict()``, filtering helpers, and trace utilities—remains compatible.

Key differences
~~~~~~~~~~~~~~~

* **State retention**: the optimised engine retains only the latest timestep plus trace results; the FP engine stores every timestep in
  memory. Prefer FP for small or audit-heavy programs; rely on the optimised mode for large graphs.
* **Reason again support**: FP mode **does not support** reasoning again with ``reason(..., again=True, restart=...)``
* **Performance**: the optimised engine leverages incremental updates which typically makes it faster. The FP
  engine keeps track of every timestep in memory which can make it slower and more memory-intensive.

Pick the FP interpreter when you need exhaustive visibility into each timestep or when validating logic against a canonical fixed-point
reference. Stick with the default optimised engine for production workloads or any scenario where throughput and memory usage are the
primary concerns.
