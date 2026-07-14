``import IPython`` is now much faster (lazy top-level attributes)
------------------------------------------------------------------

``IPython.embed``, ``IPython.InteractiveShell`` and ``IPython.Application``
are now imported lazily on first attribute access (:pep:`562`), instead of
eagerly at ``import IPython`` time. Previously, merely importing the
``IPython`` package pulled in the whole shell machinery, including the
terminal stack and ``prompt_toolkit``. With this change (and jedi now also
being imported lazily on first completion), ``import IPython`` went from
roughly 340ms to under 20ms of pure import time on a warm cache.

All regular usage — ``IPython.embed()``, ``from IPython import embed``,
``from IPython import *`` — behaves exactly as before. The only observable
difference is that ``import IPython`` no longer *transitively* imports
submodules such as ``IPython.terminal.interactiveshell`` or third-party
packages such as ``prompt_toolkit`` as a side effect; code that relied on
those being present in ``sys.modules`` without importing them should import
what it uses explicitly.
