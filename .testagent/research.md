# Research

## Bounded target inventory

- `keyboards.py`: `menu_keyboard()` declares the main menu buttons.
- `trek.py`: declares `plot()` and `about()` and registers callback handlers at
  module scope. Importing it would initialize Telegram and MongoDB clients.
- `game_metadata.py`: central source for the game version, author, repository,
  and composed About text.
- `tests/test_menu_about.py`: source-based tests added for this request.

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
- [x] Centralized game version is `0.1.0`.
- [x] About content exposes author `Simon Borin (@blooomberg)`.
- [x] About content exposes `https://github.com/SimonBorin/trek_bot`.
- [x] Tests do not import or run Telegram or MongoDB.
