# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

#sys.path.insert(0, os.path.abspath('../..'))
#sys.path.insert(0, os.path.abspath('pyreason/pyreason.py'))
# Calculate the absolute path to the pyreason directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'pyreason'))
# Add the pyreason directory to sys.path
sys.path.insert(0, project_root)


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyReason'
copyright = '2024, LabV2'
author = 'LabV2'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx_rtd_theme', 'sphinx.ext.autosummary', 'sphinx.ext.doctest',
              'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.mathjax', 'sphinx.ext.ifconfig',
              'sphinx.ext.viewcode', 'sphinx.ext.napoleon', 'autoapi.extension',]  # Just this line

autosummary_generate = True
#autoapi_template_dir = '_templates/autoapi'
# Ensure autoapi_dirs points to the folder containing pyreason.py
#autoapi_dirs = [project_root]
autoapi_dirs = [os.path.join(project_root)]  # Only include the pyreason directory 

#autoapi_dirs = [os.path.join(project_root)]  # Include only 'pyreason.pyreason'
#autoapi_dirs = ['../pyreason/pyreason']

autoapi_root = 'pyreason'
autoapi_ignore = ['*/scripts/*', '*/examples/*', '*/pyreason.pyreason/*']

# Ignore modules in the 'scripts' folder
# autoapi_ignore_modules = ['pyreason.scripts']


autoapi_options = [
    "members",               # Include all class members (functions)
    "undoc-members",         # Include undocumented members
    "show-inheritance",      # Show inheritance tree for methods/functions
   # "private-members",       # Include private members (e.g., _method)
]

templates_path = ['_templates']

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = [
    "css/custom.css",
]

add_module_names = False
