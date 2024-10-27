Fact
~~~~

-  A fact is a statement that is true in the graph. It is a basic unit
   of knowledge that is used to derive new information.
-  Facts are used to initialize the graph and are the starting point for
   reasoning.


Fact Parameters *add asumptions maybe???
~~~~~~~~~~~~~~~
To create a new **Fact** object in PyReason, use the `Fact` class with the following parameters:

1. **fact_text (str):** The fact in text format 
   
.. code:: text

    `'pred(x,y) : [0.2, 1]'` or `'pred(x,y) : True'` 

2. **name (str):** The name of the fact. This will appear in the trace so that you know when it was applied
3. **start_time (int):** The timestep at which this fact becomes active
4. **end_time (int):** The last timestep this fact is active
5. **static (bool):** If the fact should be active for the entire program. In which case `start_time` and `end_time` will be ignored


Fact Parsing
~~~~~~~~~~~~
Fact parser takes in fact_text as input and then reads fact

**add info about fact parser function!**


Then add the fact the Pyreason with the following command:
.. code:: python

   import pyreason as pr
   pr.add_fact(pr.Fact(name='fact1', component='', attribute='popular', bound=[1, 1], start_time=0, end_time=2))

