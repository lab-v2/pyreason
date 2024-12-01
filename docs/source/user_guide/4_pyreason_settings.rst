
Settings
=================
In this section, we detail the settings that can be used to configure PyReason. These settings can be used to control the behavior of the reasoning process.

Settings can be accessed using the following code:

.. code-block:: python

    import pyreason as pr
    pr.settings.setting_name = value

Where ``setting_name`` is the name of the setting you want to change, and ``value`` is the value you want to set it to.
Below is a table of all the settings that can be changed in PyReason using the code above.

.. note::
    All settings need to be modified **before** the reasoning process begins, otherwise they will not take effect.

To reset all settings to their default values, use the following code:

.. code-block:: python
    
    import pyreason as pr
    pr.reset_settings()


.. list-table::

 * - **Setting**
   - **Default**
   - **Description**
 * - ``verbose``
   - True
   - | Print extra information to
     | screen during the reasoning process.
 * - ``output_to_file``
   - False
   - | Output print statements
     | into a file.
 * - ``output_file_name``
   - 'pyreason_output'
   - | Name the file output will
     | be saved as (only if ``output_to_file = True``).
 * - ``graph_attribute_parsing``
   - True
   - | Parse the graph for
     | attributes.
 * - ``reverse_digraph``
   - False
   - | Reverse the directed edges
     | in the graph before reasoning.
 * - ``atom_trace``
   - False
   - | Keep track of ground atoms
     | making the clauses true. **NOTE:** May use significant memory
     | and slow down runtime for large graphs.
 * - ``save_graph_attributes_to_trace``
   - False
   - | Save graph attribute facts
     | to the rule trace. Trace files may become large
     | due to many attributes in graphs.
 * - ``persistent``
   - False
   - | Reset bounds in the interpretation
     | to uncertain ``[0,1]`` at each timestep or
     | retain their value from the previous timestep.
 * - ``inconsistency_check``
   - True
   - | Check for inconsistencies in the interpretation
     | and resolve by resetting bounds to ``[0,1]`` and
     | making the atom static.
 * - ``static_graph_facts``
   - True
   - | Make graph facts static,
     | keeping graph attributes constant during reasoning.
 * - ``parallel_computing``
   - False
   - | Use multiple CPU cores for inference
     | to speed up runtime, especially for large graphs.
 * - ``update_mode``
   - 'intersection'
   - | Update interpretations via ``'intersection'`` (new
     | and old bounds overlap) or ``'override'`` (use new bound).
 * - ``allow_ground_rules``
   - False
   - | Allow rules to include ground atoms.
     | Ground atoms should match graph components or
     | be treated as variables.


Notes on Parallelism
~~~~~~~~~~~~~~~~~~~~
PyReason is parallelized over rules, so for large rulesets it is recommended that this setting is used. However, for small rulesets,
the overhead might be more than the speedup and it is worth checking the performance on your specific use case.
When possible we recommend using the same number of cores (or a multiple) as the number of rules in the program.