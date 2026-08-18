# AGENTS.md

## What this is

`aartzzUtils` is a Python plugin for **exteraGram** (an Android Telegram client fork). It restores legacy UI behavior removed in newer Telegram versions by hooking Java methods inside the running app. It is NOT a standalone Python app — the code only executes inside exteraGram's Elyx plugin runtime. GPL v3, alpha-stage (README warns of bugs).

## Project structure

```
plugin/
  metainfo.yml          # plugin id, name, description, version, app_version — bump `version` here before tagging
  .elyxbuilder/
    config.yml          # build config: source dir, zipFormat, compilationIgnore, obfuscation
  locales/
    strings_{en,ru,uk}.yml   # ALL user-facing strings; every key must exist in all three
  src/
    main.py             # entrypoint; excluded from compilation (compilationIgnore); resolves Java classes + registers hooks
    hooks/              # one file per feature, one or more MethodHook classes each
      __init__.py       # must re-export every hook class — not auto-exported
    ui/
      settings.py       # SettingsMixin.create_settings() — every Header/Switch for the plugin UI
refmap.yml              # maps Elyx paths: metainfo, main, strings, elyxbuilder
requirements.txt        # only dependency: ElyxBuilder
builds/                 # elyb output (aartzzutils.elyx) — gitignored
.github/workflows/      # build.yml (push/PR to main) + release.yml (v* tags)
docs/                   # README screenshots
```

`plugin/src/hooks/system_bars.py` (`LaunchActivityNavBarColorHook`) is **not** exported in `hooks/__init__.py` nor registered in `main.py` — treat it as the reference for the "add a feature" wiring below.

## Build & verify

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # only dependency: ElyxBuilder
elyb build -v -nf                 # outputs builds/aartzzutils.elyx
```

- Build config lives in `plugin/.elyxbuilder/config.yml` (not at repo root).
- `plugin/src/main.py` is excluded from compilation (`compilationIgnore`); a compiled variant `aartzzutils-compiled` is also produced.
- **There is no test suite, linter, formatter, or typechecker.** Verification is: build succeeds + manual testing inside the app. `.venv` exists locally (Python 3.14).
- CI (`.github/workflows/`) runs the same `elyb build -v -nf` on push/PR to `main`; `v*` tags trigger the release workflow (builds/*.elyx → GitHub release). Bump `version` in `plugin/metainfo.yml` before tagging.

## External resources

- **`https://github.com/fossSquad/exteraSkill`** is the official `exteragram-plugin-dev` skill for building exteraGram plugins. Load it for the full plugin-dev workflow. Docs live at `https://plugins.exteragram.app/`; SDK builds at `github.com/exteraSquad/plugins-pysdk-builds`; `exteragram-utils` pip package has an `extera` CLI for pushing plugins.
- **Debugging on device**: view `self.log()` / Python / Xposed errors via `adb logcat -d | grep -iE 'Hooked|Failed to hook|Extera Restore|chaquopy'` — match this plugin's own log strings rather than a tag (tags like `re:extera` belong to other plugins). In-app logs: Settings → Plugins → settings icon (top right) → Copy logs. Pushing a plugin requires **Developer Mode** (Settings → Plugins → settings icon → Developer mode).
- **Dev server (fast iteration)**: the app runs a TCP dev server on `127.0.0.1:42690`. Connect with `adb devices` then `adb forward tcp:42690 tcp:42690`, then talk to it with JSON commands over that port — `write_plugin` (plugin_id, content=full Python source) to replace code, `reload_plugin` (single-file only), `enable_plugin`/`disable_plugin`, `remove_plugin`, `ping`, and Elyx multi-file variants (`elyx_ping`, `elyx_compare_folder`, `elyx_changes`). The debugger port (default 5678, `start_debugger`/`stop_debugger`) is separate from 42690.
- **Localization (Elyx)**: `from elyx import strings`; fallback order is selected-locale → `en` → the key itself, so always ship English. Call it to format: `strings("hello", name=...)` / positional `{}`. Don't build sentences by concatenating fragments — use `{named}` placeholders. YAML-quote values containing `:`, `{}`, or leading specials.
- **Settings storage (Elyx)**: `from elyx import settings`; `settings.get("key", default)` / `settings.set("key", value, reload_settings=False)`. `reload_settings=True` only when the value changes which rows render. Settings are keyed by plugin id, survive reloads/updates. Keep big JSON/caches/secrets in files/DB, not settings.

## Runtime model (critical)

- The plugin runtime imports — `base_plugin` (BasePlugin, MethodHook), `hook_utils.find_class`, `android_utils`, `ui.settings` (Header, Switch), `elyx.strings` — are provided by the exteraGram app at load time. They are **not in this repo and cannot be installed**. Do not try to run or import plugin code in a plain Python env; it will fail.
- Java classes are resolved by name via `JavaClass.forName("com.exteragram...")` / `JavaClass.forName("org.telegram...")` in `main.py`.
- You cannot see Java class internals from this repo — rely on `_FieldCache`/`_BoundedState` reflection helpers (see `hooks/dialog_cell.py`) and `param.thisObject` / `param.args` in hooks. `hash(instance)` is used as a Java identity key. Use `AndroidUtilities.dp(...)` for pixel values and `ThemeProxy.getColor(...)` for theme colors.

## Adding a feature (the wiring)

1. **Hook**: one file per feature in `plugin/src/hooks/` (e.g. `blur_glass.py`). Define `MethodHook` subclasses implementing `before_hooked_method(self, param)` / `after_hooked_method(self, param)`. Wrap every hook body in try/except and log via `self.plugin.log(...)` (fallback `print` on failure).
2. **Export**: add each new hook class to `plugin/src/hooks/__init__.py` — it is not exported automatically.
3. **Register**: in `plugin/src/main.py` `on_plugin_load()`, resolve the Java class and call `self.hook_all_methods(Class, "methodName", HookClass(self))`, `self.hook_method(...)`, or `self.hook_all_constructors(...)`, each wrapped in try/except.
4. **Settings**: add `Header(text=strings(...))` / `Switch(key=..., text=strings(...), subtext=strings(...), default=False, icon="msg_...", on_change=lambda v: self.set_setting(key, v))` to `SettingsMixin.create_settings()` in `plugin/src/ui/settings.py`. All defaults are `False`. For settings that need the activity to rebuild (e.g. `rectangular_ui`, `legacy_pin_pos`), pass `reload_settings=True`. Conditional switches are only appended when `self.get_setting("other_key", False)` is set — check before appending.
5. **Localize**: every user-facing string goes through `strings("key")` — the key **must exist in all three** files `plugin/locales/strings_{en,ru,uk}.yml`. Settings use `{key}_title` / `{key}_desc` pairs; `plugin_description` is referenced by `plugin/metainfo.yml`.