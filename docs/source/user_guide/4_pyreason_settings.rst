
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


+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| Setting                       | Default          | Description                                                                              |
+===============================+==================+==========================================================================================+
| verbose                       | True             | Whether verbose mode is on                                                               |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| output to file                | False            | Whether output is going to be printed to file                                            |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| output file name              | 'pyreason_output'| The name the file output will be saved as.                                               |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| graph attribute parsing       | True             | Whether graph will be parsed for attributes.                                             |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| abort on inconsistency        | False            | Whether program will abort on encountering an inconsistency.                             |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| memory profile                | False            | Whether the program will profile maximum memory usage.                                   |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| reverse digraph               | False            | Whether the graph will be reversed.                                                      |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| atom trace                    | False            | Whether to keep track of all atoms responsible for firing rules.                         |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| save graph attributes to trace| False            | Whether to save graph attribute facts to the rule trace.                                 |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| canonical                     | False            | Whether the interpretation is canonical.                                                 |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| inconsistency check           | True             | Whether to check for inconsistencies in the interpretation.                              |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| static graph facts            | True             | Whether to make graph facts static.                                                      |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| store interpretation changes  | True             | Whether to track changes in the interpretation.                                          |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| parallel computing            | False            | Whether to use multiple CPU cores for inference.                                         |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| update mode                   | 'intersection'   | The mode for updating interpretations. Options are 'intersection' or 'override'.         |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| allow ground rules            | False            | Whether rules can have ground atoms.                                                     |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+


