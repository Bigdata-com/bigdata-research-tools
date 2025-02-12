# Contributing to Bigdata Research Tools

First off, thanks for taking the time to contribute! ❤️

### Your First Code Contribution

First of all, before you start implementing anything that will be time consuming,
**make sure that what you are going to implement is agreed with the maintainers
of the project**, to avoid wasting your time. Open a new issue if
necessary to discuss it before you implement your solution. Of course, for most
bug fixes or even very minor features, you can trust your instinct and submit a
_Pull Request_ directly. Check {ref}`"Suggesting Enhancements"<suggesting
enhancements>` for more info.

In order make any contribution to the code you will have to make sure to have
your development environment working. Clone the repo, install the dependencies
and run the tests, to make sure that everything is setup properly. Check
{ref}`"Setting up the Development Environment"<setting up the development
environment>` for more info. If you have any issues, fix them first before
continuing, asking in through the appropriate channels if needed. Please, never
send a _Pull Request_ without first checking that the change actually works.

While implementing your change, **don't forget about the tests**. Tests are
very important for the project and changes that are not tested will not be
included in general, so make sure you add as many tests as needed for your
changes, and that you update the existing ones. Changes that _break_ the test
suite will never me merged.

Also, make sure that you **follow the style in the project**, formatting with
black, etc. If possible, install the pre-commit hooks, which will help you make
sure you don't make any mistakes. Please read our
{ref}`"Style Guides"<styleguides>`.

When applies, please **update the documentation** accordingly to make sure that
it's always in line with the code. If the change is a new feature, it should be
added the documentation, and if it's just a change on an existing feature,
probably some text may need to be updated too. If the existing feature was not
documented, please consider documenting it regardless, it will be really
helpful. For more info, check the section on {ref}`"Improving The
Documentation"<improving the documentation>`

Finally, **open a _Pull Request_** for review, where we will discuss the changes.
Make sure that all the tests pass to make sure you didn't break anything else.
And expect some comments on the code and requests for changes.

If everything goes fine, your pull request will be merged 🚀


(styleguides)=
## Style Guides

(commit messages)=
### Commit Messages
To ensure that our commit messages are both concise and informative, all
committers are asked to follow the git commit message format outlined below.
For reference, Linus Torvalds provides a description of a good commit message
[here](https://github.com/torvalds/subsurface-for-dirk/blob/a48494d2fbed58c751e9b7e8fbff88582f9b2d02/README#L88).

A good commit message looks like this:

	Header line: explain the commit in one line (use the imperative)

	Body of commit message is a few lines of text, explaining things
	in more detail, possibly giving some background about the issue
	being fixed, etc etc.

	The body of the commit message can be several paragraphs, and
	please do proper word-wrap and keep columns shorter than about
	74 characters or so. That way "git log" will show things
	nicely even when it's indented.

	Make sure you explain your solution and why you're doing what you're
	doing, as opposed to describing what you're doing. Reviewers and your
	future self can read the patch, but might not understand why a
	particular solution was implemented.

where that header line really should be meaningful, and really should be just
one line. It should summarize the change in one readable line of text,
independently of the longer explanation. Please use verbs in the imperative in
the commit message, as in "Fix bug that ...", "Add file/feature ...", or "Bump
version number ...".

(python code style)=
### Python Code Style

In general we follow the rules of PEP-8 as most python project, but we will try
to list here all the rules that we follow that are not described by PEP-8:

(formatting)=
#### Formatting

The whole codebase is formatted with [black](https://github.com/psf/black).
There is a pre-commit hook that you can install, and there is a check in the
pipeline on top of that, so if your code has bad format won't get anywhere.

Additionally, imports should be sorted with
[isort](https://github.com/PyCQA/isort), and both pre-commit and checks in the
pipeline are available like with black

(imports)=
#### Imports

* _Never_ do a _star import_ `from X import *`.
* Avoid doing a local import unless there is a very big reason to do that.
* Avoid aliases on imports (`from x import y as z`) as this makes finding
  references more difficult.

(naming)=
#### Naming

Enums are considered constants, so they should be written IN_ALL_CAPS, as the
[BDFL dictates](https://mail.python.org/pipermail/python-ideas/2016-September/042340.html):

```python
class MyEnum(Enum):
    ITEM_ONE = "item1"
    ITEM_TWO = "item2"
```

Global _"constants"_ are all upper case:

```python
PI = 3.14159
```

(docstrings)=
#### Docstrings

Docstrings in this project are not just to be viewed from the editor/IDE, they
are also used to auto-generate the documentation in Sphinx, so it's very
important to follow a specific [format supported by
Sphinx](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html).
Specifically, the format that we follow for docstrings is [the one from
google](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):

```python
def func(arg1, arg2):
    """
    Summary line.

    Extended description of function.

    Args:
        arg1 (int): Description of arg1
        arg2 (str): Description of arg2

    Returns:
        bool: Description of return value
    """
```


See [more examples of google
docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html)

It's also possible to add examples to these docstrings, but note that we run
doctests in the CI pipeline, so the examples you write should be executable and
correct and reliable:

```python
def func(t):
  """
  >>> func("This is a good example")
  18
  >>> func("This example is incorrect and will cause the pipeline to fail")
  0
  """
  return len(t)
```

Sometimes you may want to have examples in your docstrings, but you may not
want them to get executed as a test (for example if the function is actually
calling an API). In those cases you should disable each line with `doctest:
+SKIP`:

```python
def func(p):
  """
  >>> result = func(p) # doctest: +SKIP
  >>> result.id        # doctest: +SKIP
  123
  """
  requests.post("/my/api", {"payload": p})
```


(tests style)=
### Tests Style

Tests are contained in the `tests/` folder, which mirrors the same tree
structure as the sources directory in `src/`. This makes tests very easy to find. 


(setting up the development environment)=
## Setting up the Development Environment

(installing dependencies)=
### Installing dependencies

Clone the repository. Then make sure uv is installed and install the requirements.

```sh
pipx install uv

uv sync
```


Then, install the pre-commit hooks:

```sh
uv run pre-commit install
```


(running the tests)=
### Running the tests

To run the unit tests:

```sh
uv run pytest
```

Also, there is a convenient command that will run the unit tests, generating
some coverage information:

```sh
uv run task coverage
```

(releasing)=
## Releasing

Not available yet.
