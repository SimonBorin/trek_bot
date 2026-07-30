# Plan

1. Add an AST helper that reads assignments, function calls, and handler
   registrations without importing application modules.
2. Cover menu requirements with
   `test_main_menu_exposes_plot_and_about_actions`.
3. Cover handler registration with
   `test_plot_callback_handler_is_registered` and
   `test_about_callback_handler_is_registered`.
4. Cover centralized metadata and About content with
   `test_about_text_uses_centralized_version_author_and_repository_metadata`.
5. Run the narrow pytest target, review every assertion against the acceptance
   checklist, and record the clean result in `.testagent/status.md`.

