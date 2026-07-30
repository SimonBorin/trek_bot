# Research

## Bounded target inventory

- `keyboards.py`: `menu_keyboard()` declares the main menu buttons.
- `trek.py`: declares `plot()` and `about()` and registers callback handlers at
  module scope. Importing it would initialize Telegram and MongoDB clients.
- `game_metadata.py`: central source for the game version, author, repository,
  and composed About text.
- `scripts/next_version.py`: resolves a release tag at `HEAD`, or increments the
  latest stable SemVer tag for an unreleased commit.
- `.github/workflows/release.yml`: automatically tags commits merged into
  `master`.
- `tests/test_menu_about.py`: source-based tests added for this request.
- `tests/test_release_version.py`: isolated Git/CLI and workflow contract tests.

## Existing conventions

- The repository previously had no test directory, pytest configuration, or
  representative tests.
- Runtime dependencies are listed in a plain `requirements` file.
- Tests therefore use pytest's built-in assertion style and Python's `ast`
  module, with no Telegram, MongoDB, environment, or network dependency.

## Acceptance checklist

- [x] Main menu has `Plot` with callback data `plot`.
- [x] Main menu has `About` with callback data `about`.
- [x] A callback handler registers `plot` for the Plot callback.
- [x] A callback handler registers `about` for the About callback.
- [x] About content is centralized outside `trek.py`.
- [x] `game_metadata.py` has no hardcoded `0.1.0`.
- [x] `GAME_VERSION` honors the environment override.
- [x] With latest stable tag `v0.1.2`, an unreleased commit resolves to `0.1.3`.
- [x] At a `HEAD` tagged `v0.1.2`, the current release remains `0.1.2`.
- [x] About content displays the centralized automatic version.
- [x] About content exposes author `Simon Borin (@blooomberg)`.
- [x] About content exposes `https://github.com/SimonBorin/trek_bot`.
- [x] Release workflow automatically tags merged `master` commits.
- [x] Tests do not import or run Telegram or MongoDB.
