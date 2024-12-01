Facts
-----
This section outlines Fact creation and implementation. See  :ref:`here <fact>` for more information on Facts in logic.

Fact Parameters 
~~~~~~~~~~~~~~~
To create a new **Fact** object in PyReason, use the `Fact` class with the following parameters:

1. ``fact_text`` **(str):** The fact in text format, where bounds can be specified or not. The bounds are optional. If not specified, the bounds are assumed to be [1,1]. The fact can also be negated using the '~' symbol.

    Examples of valid fact_text are:

.. code-block:: text

    1. 'pred(x,y) : [0.2, 1]'
    2. 'pred(x,y)'
    3. '~pred(x,y)'

2. ``name`` **(str):** The name of the fact. This will appear in the trace so that you know when it was applied
3. ``start_time`` **(int):** The timestep at which this fact becomes active (default is 0)
4. ``end_time`` **(int):** The last timestep this fact is active (default is 0)
5. ``static`` **(bool):** If the fact should be active for the entire program. In which case ``start_time`` and ``end_time`` will be ignored. (default is False)


Fact Example 
~~~~~~~~~~~~

To add a fact in PyReason, use the command:

.. code-block:: python
    
   import pyreason as pr
    pr.add_fact(pr.Fact(fact_text='pred(x,y) : [0.2, 1]', name='fact1', start_time=0, end_time=2))
