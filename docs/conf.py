import os
import shutil
import sys
from pathlib import Path

import sphinx

# import sphinxcontrib.spelling

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Bigdata Research Tools"
copyright = "2024, RavenPack"
author = "RavenPack"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "alabaster"
html_theme = "furo"
html_static_path = ["_static"]
# Logo not needed here for furo.
# html_logo = "_static/bigdata.svg"
html_theme_options = {
    "light_logo": "bigdata_light.svg",
    "dark_logo": "bigdata_dark.svg",
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#0387FE",
        "color-brand-content": "#0387FE",
    },
    "dark_css_variables": {
        "color-brand-primary": "#00A9FE",
        "color-brand-content": "#00A9FE",
    },
}
pygments_style = "sphinx"
pygments_dark_style = "monokai"


PROJECT_DIRECTORY = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_DIRECTORY))

# version = '.'.join(__version_info__[:2])
# release = __version__

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    # Disabling autosectionlabel because it does strange things in markdown documents
    # "sphinx.ext.autosectionlabel",
    # 'nbsphinx',
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.autodoc_pydantic",
    "sphinxcontrib.spelling",
    "myst_parser",
    "sphinx_new_tab_link",  # Extension that forces every link to open in a new tab. This is a req for the current ones.
    "sphinx_copybutton",  # Extension to provide a copy button in the code samples
    "sphinx_reredirects",
]

# sphinx_reredirects
redirects = {"getting_started/overview.html": "./index.html"}


# suppress_warnings = ['autosectionlabel.*', # nbsphinx and austosectionlabel do not play well together
#                      'app.add_node', # using multiple builders in custom Sphinx objects throws a bunch of these
#                      'app.add_directive',
#                      'app.add_role',]

suppress_warnings = [
    "myst.xref_missing"  # This warning happens whenever links referencing sections are used in rst files. But the links work fine.
]
# -- References (BibTex) -----------------------------------------------------
bibtex_bibfiles = ["wecopttool_refs.bib"]
bibtex_encoding = "utf-8-sig"
bibtex_default_style = "alpha"
bibtex_reference_style = "label"
bibtex_foot_reference_style = "foot"


# -- API documentation -------------------------------------------------------
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
add_module_names = False
html_show_sourcelink = False
autodoc_typehints = "description"
autodoc_type_aliases = {
    "ArrayLike": "ArrayLike",
    "FloatOrArray": "FloatOrArray",
    "TStateFunction": "StateFunction",
    "TWEC": "WEC",
    "TPTO": "PTO",
    "TEFF": "Callable[[ArrayLike, ArrayLike], ArrayLike]",
    "TForceDict": "dict[str, StateFunction]",
    "TIForceDict": "Mapping[str, StateFunction]",
    "DataArray": "DataArray",
    "Dataset": "Dataset",
    "Figure": "Figure",
    "Axes": "Axes",
}
autodoc_class_signature = "separated"
highlight_language = "python3"
rst_prolog = """
.. role:: python(code)
   :language: python
"""
autodoc_default_options = {"exclude-members": "__new__"}
autosummary_ignore_module_all = False
autosummary_imported_members = True
autodoc_pydantic_model_show_config_summary = False

spelling_warning = True
spelling_word_list_filename = "spelling_wordlist.txt"
copybutton_exclude = ".linenos, .gp, .go"
copybutton_prompt_text = "(bigdata_venv) $"
copybutton_prompt_text = ">>> "
