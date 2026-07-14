# PYTHON_ARGCOMPLETE_OK
"""
IPython: tools for interactive and parallel computing in Python.

https://ipython.org
"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2008-2011, IPython Development Team.
#  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import warnings
from typing import TYPE_CHECKING, Any

#-----------------------------------------------------------------------------
# Setup everything
#-----------------------------------------------------------------------------

from .core.getipython import get_ipython
from .core import release
from .utils.sysinfo import sys_info
from .utils.frame import extract_module_locals

if TYPE_CHECKING:
    from .core.application import Application
    from .core.interactiveshell import InteractiveShell
    from .terminal.embed import embed

__all__ = ["start_ipython", "embed", "embed_kernel"]

# Attributes imported lazily on first access (PEP 562). Importing these
# eagerly would pull the whole shell machinery — including the terminal stack
# and prompt_toolkit for `embed` — into every `import IPython`, which is a
# significant startup cost for programs that only use IPython as a library.
_LAZY_IMPORTS = {
    "Application": ".core.application",
    "InteractiveShell": ".core.interactiveshell",
    "embed": ".terminal.embed",
}


def __getattr__(name: str) -> Any:
    source_module = _LAZY_IMPORTS.get(name)
    if source_module is not None:
        from importlib import import_module

        value = getattr(import_module(source_module, __name__), name)
        # cache it so __getattr__ only fires once per name
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_LAZY_IMPORTS))

# Release data
__author__ = '{} <{}>'.format(release.author, release.author_email)
__license__  = release.license
__version__  = release.version
version_info = release.version_info
# list of CVEs that should have been patched in this release.
# this is informational and should not be relied upon.
__patched_cves__ = {"CVE-2022-21699", "CVE-2023-24816"}


def embed_kernel(module=None, local_ns=None, **kwargs):
    """Embed and start an IPython kernel in a given scope.

    If you don't want the kernel to initialize the namespace
    from the scope of the surrounding function,
    and/or you want to load full IPython configuration,
    you probably want `IPython.start_kernel()` instead.

    This is a deprecated alias for `ipykernel.embed.embed_kernel()`,
    to be removed in the future.
    You should import directly from `ipykernel.embed`; this wrapper
    fails anyway if you don't have `ipykernel` package installed.

    Parameters
    ----------
    module : types.ModuleType, optional
        The module to load into IPython globals (default: caller)
    local_ns : dict, optional
        The namespace to load into IPython user namespace (default: caller)
    **kwargs : various, optional
        Further keyword args are relayed to the IPKernelApp constructor,
        such as `config`, a traitlets :class:`Config` object (see :ref:`configure_start_ipython`),
        allowing configuration of the kernel.  Will only have an effect
        on the first embed_kernel call for a given process.
    """

    warnings.warn(
        "import embed_kernel from ipykernel.embed directly (since 2013)."
        " Importing from IPython will be removed in the future",
        DeprecationWarning,
        stacklevel=2,
    )

    (caller_module, caller_locals) = extract_module_locals(1)
    if module is None:
        module = caller_module
    if local_ns is None:
        local_ns = dict(**caller_locals)
    
    # Only import .zmq when we really need it
    from ipykernel.embed import embed_kernel as real_embed_kernel
    real_embed_kernel(module=module, local_ns=local_ns, **kwargs)

def start_ipython(argv: list[str] | None = None, **kwargs: Any) -> Any:
    """Launch a normal IPython instance (as opposed to embedded)

    `IPython.embed()` puts a shell in a particular calling scope,
    such as a function or method for debugging purposes,
    which is often not desirable.

    `start_ipython()` does full, regular IPython initialization,
    including loading startup files, configuration, etc.
    much of which is skipped by `embed()`.

    This is a public API method, and will survive implementation changes.

    Parameters
    ----------
    argv : list or None, optional
        If unspecified or None, IPython will parse command-line options from sys.argv.
        To prevent any command-line parsing, pass an empty list: `argv=[]`.
    user_ns : dict, optional
        specify this dictionary to initialize the IPython user namespace with particular values.
    **kwargs : various, optional
        Any other kwargs will be passed to the Application constructor,
        such as `config`, a traitlets :class:`Config` object (see :ref:`configure_start_ipython`),
        allowing configuration of the instance (see :ref:`terminal_options`).
    """
    from IPython.terminal.ipapp import launch_new_instance
    return launch_new_instance(argv=argv, **kwargs)
