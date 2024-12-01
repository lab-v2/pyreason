Installing PyReason
===================

This guide details the process of installing Pyreason in an isolated
environment using pyenv and pip. It is particularly useful when managing
projects that require different versions of Python.

Prerequisites
-------------

-  Familiarity with terminal or command prompt commands.
-  Basic knowledge of Python and its package ecosystem.

.. note::

    Use python version 3.9 or 3.10 .


Step-by-Step Guide
------------------

1. Install pyenv
-  Ensure your system has the necessary dependencies installed. The installation steps vary by operating system:
    
    -   **Linux/Unix/macOS**
    .. code-block:: bash

        brew update brew install pyenv
        sudo apt-get update sudo apt-get install make build-essential libssl-dev zlib1g-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl
        git curl -L  https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer \| bash

2. Configure Environment Variables
    - Add pyenv to your profile script to automatically use it in your shell
    - **For bash users**:
    .. code-block:: bash

       echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bash_profile
       echo 'eval "$(pyenv init --path)"' >> ~/.bash_profile
       echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile
    -  For zsh users:
    .. code-block:: bash

        echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.zshrc
        echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
        echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc``

   -  Restart your shell so the path changes take effect.

3. Install Python using `pyenv`

.. code-block:: bash

  pyenv install 3.8

4. Create a Virtual Environment

.. code-block:: bash

    pyenv virtualenv 3.8 pyreason_venv_3.8

5. Activate the Virtual Environment

.. code-block:: bash

    pyenv activate pyreason_venv_3.8

6. Install pyreason Using `pip`

.. code-block:: bash

    pip install pyreason

7. Install requirements.txt

.. code-block:: bash

    pip install -r requirements.txt

8. Deactivate the Virtual Environment

.. code-block:: bash

    pyenv deactivate
