Fact
~~~~

-  A fact is a statement that is true in the graph. It is a basic unit
   of knowledge that is used to derive new information.
-  Facts are used to initialize the graph and are the starting point for
   reasoning.


Adding a Fact
~~~~~~~~~~~~~
In the graph we have created, suppose we want to set `Mary` to be
`popular` initially.

.. code:: python

   import pyreason as pr
   pr.add_fact(pr.Fact(name='popular-fact', component='Mary', attribute='popular', bound=[1, 1], start_time=0, end_time=2))

The fact indicates that `Mary` is `popular` at time `0` and will
remain so until time `2`.


In the graph we have created, suppose we want to set `Mary` to be
`popular` initially.

We add a fact to our graph with the following code: 

.. code:: python

   import pyreason as pr
   pr.add_fact(pr.Fact(name='popular-fact', component='Mary', attribute='popular', bound=[1, 1], start_time=0, end_time=2))

The fact indicates that `Mary` is `popular` at time `0` and will
remain so until time `2`.

Fact parameters
~~~~~~~~~~~~~~~
To create a new **Fact** object in PyReason, use the `Fact` class with the following parameters:

1. *fact_text:* The fact in text format 
    i. example:   
    .. code:: text

        `'pred(x,y) : [0.2, 1]'` or `'pred(x,y) : True'` 


        :param fact_text: The fact in text format. Example: `'pred(x,y) : [0.2, 1]'` or `'pred(x,y) : True'`
        :type fact_text: str
        :param name: The name of the fact. This will appear in the trace so that you know when it was applied
        :type name: str
        :param start_time: The timestep at which this fact becomes active
        :type start_time: int
        :param end_time: The last timestep this fact is active
        :type end_time: int
        :param static: If the fact should be active for the entire program. In which case `start_time` and `end_time` will be ignored
        :type static: bool

