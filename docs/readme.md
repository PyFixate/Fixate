# Fixate Documentation

To actually _read_ the docs, head to https://fixate.readthedocs.io. 

This document is about how to add to and improve the existing docs, and the setup for building them.

# Docs Structure

## Theory of Documentation

See [Documentation Quadrants](https://dunnhq.com/posts/2023/documentation-quadrants/). tl;dr - documentation falls into one of these categories, and it's good to both: 1. keep them separate and 2. ensure there is a good quantity/quality of each type

- tutorials
- how-to guides
- discussions
- reference

Currently we have the following:

   - quickstart (tutorial)
   - example_walkthrough (tutorial)
   - example projects (how-to)
   - fixate/fixate (reference in-depth API docs, see below)
   - release-notes (reference)

# Building

The documentation build uses the Python-standard [Sphinx](https://www.sphinx-doc.org/), with configuration contained in `docs/conf.py`.

`tox -e docs` will run the docs build. See the `[testenv:docs]` section in `tox.ini` for configuration. Under the hood, it's essentially running `fixate/docs > sphinx-build <doc_src> <doc_dest>` in a venv with the requirements from docs/requirements.

# Docs from code

API docs are built automatically using [autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html), which pulls from the docstrings in the source.

The best "how-tos" at the moment are the example projects. Ideally these should have good explanations in their docstrings, then they can be pulled out at a higher level of the docs' table of contents.

## API reference structure: `sphinx-apidoc`

The _structure_ of the API reference is done separately, via [sphix-apidoc](https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html) which was from a manual run of:

```
sphinx-apidoc -o fixate --no-toc --remove-old --module-first ../src/fixate
```

This placed the API reference structure in the `docs/fixate` subdirectory. In there, `fixate.rst` has the top level, then there is a separate file for each subpackage, eg `fixate.core.rst` and `fixate.drivers.dmm.rst`.

I ran it with these args:

- `--module-first` since the modules have the more useful stuff
- `--no-toc` don't generate modules.rst since it's a full package
- `--remove-old` since we have source control, just delete superseded files

If the package structure changes, then the sphinx-apidocs call above will need to be re-run with `-f`, which will overwrite the old files.

While the apidoc potentially could be re-run on every build, at least for now I think better to commit in the original run, and then the structure of the api reference can be tweaked to best surface the most important info.

Note: The auto-generated template has been manually modified. Re-running sphinx-apidoc in the future will need to preserve those changes, or incorporate them into the source somehow.

## docstring style

Autodoc originally used ReStructured Text docstring style, but the [sphix.ext.napoleon](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html) extension allows [Google](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html#example-google)/NumPy style.

We can mix-and-match, so we can transition from one to the other as required.

tl;dr instead of rst's:

```
:param path: The path of the file to wrap
:type path: str
:param field_storage: The :class:`FileStorage` instance to wrap
:returns: A buffered writable file descriptor
:rtype: BufferedFileStorage
```

the docstrings will look like:

```
Args:
    path (str): The path of the file to wrap
    field_storage (FileStorage): The :class:`FileStorage` instance to wrap

Returns:
    BufferedFileStorage: A buffered writable file descriptor
```

Note improved readability. From the reference,

> Google style tends to be easier to read for short and simple docstrings, whereas NumPy style tends be easier to read for long and in-depth docstrings.
> Note all standard reStructuredText formatting still works as expected.

For now we'll go with Google.
For examples I've been using code blocks:

```
This is an example::

    This will go into a code block in the docs.
```



# References
- [An idiot’s guide to Python documentation with Sphinx and ReadTheDocs](https://samnicholls.net/2016/06/15/how-to-sphinx-readthedocs/)
- [Software documentation guide - Write the Docs](https://www.writethedocs.org/guide/)
- [Docs as Code](https://www.writethedocs.org/guide/docs-as-code/)