# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Pyreason'
copyright = '2024, LabV2'
author = 'LabV2'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx_rtd_theme', 'sphinx.ext.autosummary', 'sphinx.ext.doctest',
              'sphinx.ext.todo', 'sphinx.ext.coverage', 'sphinx.ext.mathjax', 'sphinx.ext.ifconfig',
              'sphinx.ext.viewcode', 'sphinx.ext.napoleon', 'autoapi.extension']

autosummary_generate = True
autoapi_dirs = ['../../pyreason']
autoapi_template_dir = '_templates/autoapi'

autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]



templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'pyreason.examples.rst',
                    'pyreason.scripts.numba_wrapper.numba_types.rst',
                    'pyreason.scripts.numba_wrapper.rst', 'pyreason.scripts.program.rst',
                    'pyreason.scripts.interpretation.rst']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_css_files = [
    "css/custom.css",
]

add_module_names = False
