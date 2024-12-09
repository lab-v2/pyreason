
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
   - | Whether to print extra information
     | to screen during the reasoning process.
 * - ``output_to_file``
   - False
   - | Whether to output print statements
     | into a file.
 * - ``output_file_name``
   - 'pyreason_output'
   - | The name the file output will be saved as
     | (only if ``output_to_file = True``).
 * - ``graph_attribute_parsing``
   - True
   - | Whether graph will be
     | parsed for attributes.
 * - ``reverse_digraph``
   - False
   - | Whether the directed edges in the graph
     | will be reversed before reasoning.
 * - ``atom_trace``
   - False
   - | Whether to keep track of all ground atoms
     | which make the clauses true. **NOTE:** For large graphs
     | this can use up a lot of memory and slow down the runtime.
 * - ``save_graph_attributes_to_trace``
   - False
   - | Whether to save graph attribute facts to the
     | rule trace. This might make the trace files large because
     | there are generally many attributes in graphs.
 * - ``persistent``
   - False
   - | Whether the bounds in the interpretation are reset
     | to uncertain ``[0,1]`` at each timestep or keep
     | their value from the previous timestep.
 * - ``inconsistency_check``
   - True
   - | Whether to check for inconsistencies in the interpretation,
     | and resolve them if found. Inconsistencies are resolved by
     | resetting the bounds to ``[0,1]`` and making the atom static.
 * - ``static_graph_facts``
   - True
   - | Whether to make graph facts static. In other words, the
     | attributes in the graph remain constant throughout
     | the reasoning process.
 * - ``parallel_computing``
   - False
   - | Whether to use multiple CPU cores for inference.
     | This can greatly speed up runtime if running on a
     | cluster for large graphs.
 * - ``update_mode``
   - 'intersection'
   - | The mode for updating interpretations. Options are ``'intersection'``
     | or ``'override'``. When using ``'intersection'``, the resulting bound
     | is the intersection of the new bound and the old bound. When using
     | ``'override'``, the resulting bound is the new bound.


Notes on Parallelism
~~~~~~~~~~~~~~~~~~~~
PyReason is parallelized over rules, so for large rulesets it is recommended that this setting is used. However, for small rulesets,
the overhead might be more than the speedup and it is worth checking the performance on your specific use case.
When possible we recommend using the same number of cores (or a multiple) as the number of rules in the program.