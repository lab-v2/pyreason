
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
| verbose                       | True             | Returns whether verbose mode is on                                                       |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| output to file                | False            | Returns whether output is going to be printed to file                                    |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| output file name              | 'pyreason_output'| Returns the name the file output will be saved as.                                       |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| graph attribute parsing       | True             | Returns whether graph will be parsed for attributes.                                     |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| abort on inconsistency        | False            | Returns whether program will abort on encountering an inconsistency.                     |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| memory profile                | False            | Returns whether the program will profile maximum memory usage.                           |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| reverse digraph               | False            | Returns whether the graph will be reversed.                                              |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| atom trace                    | False            | Returns whether to keep track of all atoms responsible for firing rules.                 |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| save graph attributes to trace| False            | Returns whether to save graph attribute facts to the rule trace.                         |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| canonical                     | False            | Returns whether the interpretation is canonical.                                         |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| inconsistency check           | True             | Returns whether to check for inconsistencies in the interpretation.                      |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| static graph facts            | True             | Returns whether to make graph facts static.                                              |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| store interpretation changes  | True             | Returns whether to track changes in the interpretation.                                  |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| parallel computing            | False            | Returns whether to use multiple CPU cores for inference.                                 |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| update mode                   | 'intersection'   | Returns the mode for updating interpretations. Options are 'intersection' or 'override'. |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+
| allow ground rules            | False            | Returns whether rules can have ground atoms.                                             |
+-------------------------------+------------------+------------------------------------------------------------------------------------------+


