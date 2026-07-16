# Deprecation / modernization / performance triage — July 2026

Survey of the IPython codebase at 9.16.0.dev (Python floor: 3.11), done alongside
the cleanup batch that this file was committed with. Items marked **done** were
addressed in that batch; everything else is recorded here for later triage.

## Deprecated APIs

### Removed in this batch (done)

| Item | Deprecated in |
|---|---|
| `IPCompleter.limit_to__all__` trait | 5.0 |
| `IPCompleter.python_matches` | 8.27 |
| `OInfo.get()` | 8.13 |
| `pylabtools.backends` / `backend2gui` module `__getattr__` | 8.24 |
| `run_cell_async` / `should_run_async` auto-transform fallback (now `TypeError`) | 7.17 |

### Deliberately kept

- **`Completer.greedy` trait** (deprecated 8.8): removal was attempted in this
  batch but reverted — pyflyby's test suite (run in this repo's downstream CI)
  still sets `%config IPCompleter.greedy=True`, and removing the trait makes
  traitlets print "Config option not recognized", breaking their
  expected-output tests. Remove once pyflyby (and likely others) migrate to
  `Completer.evaluation`/`auto_close_dict_keys`.
- **Matcher-v1 `.. deprecated:: 8.6` methods** (`magic_config_matches`,
  `python_func_kw_matches`, `dict_key_matches`, `dispatch_custom_completer` in
  `IPython/core/completer.py`): they are the implementations that their v2
  `*_matcher` wrappers delegate to. Removing them means inlining each body into
  its wrapper — churn with no behavior change. Revisit only if the v1 API is
  dropped wholesale.
- **`debugger.BdbQuit_excepthook`** (deprecated 5.1): ipdb still imports it.
  Coordinate with ipdb before removal.
- **`utils/coloransi.py`**: kept for older ipyparallel (see comment in file,
  gated on ipyparallel PR #924).
- **`IPython.embed_kernel` alias** in `IPython/__init__.py`: public top-level
  name, warning only says "deprecated since 2013"; needs an explicit decision.
- **`lib/lexers.py`** re-export of `ipython_pygments_lexers`: public import
  path relied upon by downstreams.
- **9.0-and-later deprecations** — too recent to remove yet. Inventory with
  deprecated-in versions: `ColorTB` class alias (9.0), `VerboseTB`
  `color_scheme` kwarg (9.0), `tbtools.set_colors`/`color_scheme` (9.0),
  `debugger.set_colors` (9.0), `oinspect.set_active_scheme` (9.0),
  `history.name_session` (9.0), `DisplayPublisher.publish` `source` param
  (warning added 9.0), `encoding.getdefaultencoding(prefer_stream=)` (9.0),
  `splitinput.LineInfo.ofind` (9.9), `utils/data.uniq_stable` (9.8),
  `utils/generics.inspect_object` (9.15). These become candidates roughly two
  years after their deprecation release.
- **`pylabtools._deprecated_backends` / `_deprecated_backend2gui` dicts**: still
  back the `find_gui_and_backend` fallback for Matplotlib < 3.9. Whole fallback
  (and `_matplotlib_manages_backends`) can go when Python 3.12 reaches EOL
  (late 2028) per the note in the file.

### Bookkeeping

- `utils/io.py`, `utils/encoding.py`, `utils/frame.py`, `utils/strdispatch.py`,
  `utils/wildcard.py`, `utils/dir2.py`, `utils/importstring.py` look like
  py2-era shims but are all live, internally-used modules — do not delete.

## Modernization

### Done in this batch

- Dropped the `decorator` runtime dependency (3 uses rewritten with
  `functools.wraps`; `types-decorator` removed from extras and mypy CI).
  Note: `tests/test_oinspect.py` previously exercised `oinspect.find_file`
  through decorator-package wrappers (exec-generated); it now uses
  `functools.wraps` wrappers, which exercise the same `__wrapped__` chain but
  not the exec-generated-source edge case.
- Collapsed the `typing_extensions` conditional import in `completer.py`
  (everything there is stdlib `typing` on 3.11). `typing_extensions` is still
  genuinely needed on 3.11 for `TypeAliasType` in `guarded_eval.py`.
- Deleted dead `setup.cfg` (black config in INI syntax that black never read);
  the exclusion now lives in `[tool.black]` in `pyproject.toml`.
- Fixed `LineInfo.ofind` docstring/warning version mismatch (both 9.9 now).

### Remaining opportunities

- **mypy strictness**: the top-level config is close to strict, but
  (a) a large `ignore_errors = true` module list remains, (b) ~26 modules still
  allow untyped defs, (c) `core/application.py`, `core/profileapp.py`,
  `lib/deepreload.py`, `sphinxext/ipython_directive.py`, `terminal/ipapp.py`,
  `utils/path.py`, `core/debugger_backport.py` are excluded from checking
  entirely, and (d) `disallow_any_generics` / `warn_return_any` /
  `disallow_subclassing_any` are only enabled for the four "strictest" modules.
  Incremental promotion is the highest-value ongoing typing work.
- **String formatting**: ~94 `%`-format and ~189 `.format()` call sites in
  non-test source. Ruff rules UP031/UP032 are deliberately commented out in
  `pyproject.toml` — enabling them is a large mechanical diff best done as a
  dedicated no-logic-change PR (or via `ruff --fix` + darker).
- `setupbase.py` `execfile()` re-implementation could use `runpy.run_path`;
  `setup.py`'s version gate duplicates `requires-python`. Cosmetic.
- No six/py2 leftovers, no `imp`/`distutils`/`pkg_resources` usage — already
  clean. `match` statements and further dataclass conversion offer no clear
  wins at present.

## Performance

### Done in this batch

- **Lazy jedi import** (the headline win): `completer.py` imported jedi (and
  transitively parso, which compiles grammars) at module import time, i.e. on
  every `import IPython`. Now deferred to first completion via `_get_jedi()`;
  `JEDI_INSTALLED` uses `importlib.util.find_spec`. Measured warm (median of
  3 runs in the dev container): `import IPython` ~340ms → ~277ms (~60ms,
  ~17%); cold-cache and first-run savings are larger.
- Hoisted per-call `re.compile` to module level: `global_matches` snake-case
  regex (ran on every completion request), two colder completer regexes, five
  `format_latex` regexes in `magic.py`.
- Fixed memory retention in `debugger.py`: `@lru_cache(1024)` on instance
  methods keyed by frame objects kept every Pdb instance and up to 1024 frames
  (with locals and back-chains) alive for the process lifetime. Now
  per-instance, size-bounded caches cleared on each `interaction`.
- Bounded the unbounded `count_lines_in_py_file` lru_cache in `tbtools.py`.

- **Lazy top-level attributes — attempted, then reverted.** Making
  `IPython.embed`/`InteractiveShell`/`Application` PEP 562 lazy attributes
  took `import IPython` from ~277ms (post lazy-jedi) to ~17ms warm, but broke
  pyflyby in the downstream CI: after a bare `import IPython`, its
  `_interactive.py` accesses `IPython.terminal.ipapp.TerminalIPythonApp` and
  `IPython.core.application.BaseIPythonApplication`, attribute chains that
  only resolve via the eager imports' side effects (and its `except
  AttributeError` turns this into a hard RuntimeError). The change was
  reverted; a patch making pyflyby import those submodules explicitly was
  prepared for upstream. Once that (and a survey of similar patterns in other
  downstreams) lands, the lazification is worth retrying — the attempt did
  leave behind a fix for a latent import cycle (`terminal/debugger` →
  `terminal/embed` → `terminal/interactiveshell` → `terminal/debugger`) that
  the root package's import order had been masking, which was kept.

### Investigated, deliberately not changed

- **`history.py` `db_cache_size` default of 0** flags the background save
  thread after every command → one sqlite transaction per cell (off the main
  thread, so latency is unaffected). Raising the default (e.g. 8–16) would cut
  disk/WAL churn ~10x at the cost of losing the last few commands on a hard
  crash. Durability-vs-churn tradeoff — maintainer call.
- Deferring `runpy` (86µs) and `PickleShareDB` imports in
  `interactiveshell.py`: measured, negligible — their dependencies are already
  imported by other modules. Deferring `bdb` is pointless while
  `IPython.core.debugger` (→ `pdb` → `bdb`) is imported eagerly.
- `run_cell` per-cell path looks tight: no per-cell regex compilation, history
  writes are batched off-thread.
