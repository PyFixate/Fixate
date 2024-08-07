==================================
Welcome to Fixate!
==================================

`Fixate <http://www.pyfixate.com>`_ is a python library for testing real stuff.


Fixate is designed from the ground up to work with testing electronics.


Whether you are trying to help do complete repetitive tests on your workbench to creating fully automated factory testing, this library is for you.



.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   quickstart
   example_walkthrough
   fixate/fixate
   release-notes

.. comment ..
   Fixate API docs generated with: 
      sphinx-apidoc -o fixate --no-toc --remove-old --module-first ../src/fixate
   https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html
   So all the files in the fixate directory are autogenerated, but we may want to tweak them
   or move them to this parent directory once we understand what's being generated

   useful args:
   --module-first: since the modules have the more useful stuff?
   --no-toc: don't generate modules.rst since it's a full package
   --remove-old: since we have source control, just delete superseded files
   
   # TODO: do we autogen the API RST on every docs build? would be better to capture any changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
