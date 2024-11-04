Facts
-----
This section outlines Fact creation and implementation. See  :ref:`here <fact>` for more information on Facts in logic.

Fact Parameters 
~~~~~~~~~~~~~~~
To create a new **Fact** object in PyReason, use the `Fact` class with the following parameters:

1. ``fact_text`` **(str):** The fact in text format
   
.. code-block:: text

    'pred(x,y) : [0.2, 1]' or 'pred(x,y) : True'

2. ``name`` **(str):** The name of the fact. This will appear in the trace so that you know when it was applied
3. ``start_time`` **(int):** The timestep at which this fact becomes active
4. ``end_time`` **(int):** The last timestep this fact is active
5. ``static`` **(bool):** If the fact should be active for the entire program. In which case ``start_time`` and ``end_time`` will be ignored


Fact Example 
~~~~~~~~~~~~

To add a fact in PyReason, use the command:

.. code-block:: python
    
   import pyreason as pr
   pr.add_fact(pr.Fact(name='fact1', component='node/edge name', attribute='attribute name', bound=[1, 1], start_time=0, end_time=2))
