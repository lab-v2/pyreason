Installation
==========

PyReason is currently compatible with Python 3.9 and 3.10. To install PyReason, you can use pip:

.. code:: bash

    pip install pyreason


Make sure you're using the correct version of Python. You can create a conda environment with the correct version of Python using the following command:

.. code:: bash

    conda create -n pyreason-env python=3.10

PyReason uses a JIT compiler called `Numba <https://numba.pydata.org/>`_ to speed up the reasoning process. This means that
the first time PyReason is imported it will have to compile certain functions which will result in faster runtimes later on.
You will see a message like this when you import PyReason for the first time:

.. code:: text

    Imported PyReason for the first time. Initializing caches for faster runtimes ... this will take a minute