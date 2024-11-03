
PyReason Settings
=================

                        
+------------------------------+------------------+-------------------------------------------------------+
| Setting                      | Default          | Description                                           |
+==============================+==================+=======================================================+
| verbose                      | True             | Returns whether verbose mode is on                    |
+------------------------------+------------------+-------------------------------------------------------+
| output to file               | False            | Returns whether output is going to be printed to file |
+------------------------------+------------------+-------------------------------------------------------+
| output file name             | 'pyreason_output'| Returns the name the file output will be saved as.    |
+------------------------------+------------------+-------------------------------------------------------+
| graph attribute parsing       | True             | Returns whether graph will be parsed for attributes.  |
+------------------------------+------------------+-------------------------------------------------------+
| abort on inconsistency        | False            | Returns whether program will abort on encountering an inconsistency. |
+------------------------------+------------------+-------------------------------------------------------+
| memory profile               | False            | Returns whether the program will profile maximum memory usage. |
+------------------------------+------------------+-------------------------------------------------------+
| reverse digraph              | False            | Returns whether the graph will be reversed.           |
+------------------------------+------------------+-------------------------------------------------------+
| atom trace                   | False            | Returns whether to keep track of all atoms responsible for firing rules. |
+------------------------------+------------------+-------------------------------------------------------+
| save graph attributes to trace| False            | Returns whether to save graph attribute facts to the rule trace. |
+------------------------------+------------------+-------------------------------------------------------+
| canonical                    | False            | Returns whether the interpretation is canonical.      |
+------------------------------+------------------+-------------------------------------------------------+
| inconsistency check           | True             | Returns whether to check for inconsistencies in the interpretation. |
+------------------------------+------------------+-------------------------------------------------------+
| static graph facts           | True             | Returns whether to make graph facts static.           |
+------------------------------+------------------+-------------------------------------------------------+
| store interpretation changes   | True             | Returns whether to track changes in the interpretation.|
+------------------------------+------------------+-------------------------------------------------------+
| parallel computing            | False            | Returns whether to use multiple CPU cores for inference. |
+------------------------------+------------------+-------------------------------------------------------+
| update mode                  | 'intersection'   | Returns the mode for updating interpretations. Options are 'intersection' or 'override'. |
+------------------------------+------------------+-------------------------------------------------------+
| allow ground rules           | False            | Returns whether rules can have ground atoms.          |
+------------------------------+------------------+-------------------------------------------------------+
