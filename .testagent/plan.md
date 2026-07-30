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
5. Cover automatic versioning with
   `test_next_version_increments_latest_stable_v0_1_2_tag_to_0_1_3`,
   `test_version_at_v0_1_2_tagged_head_reports_0_1_2`,
   `test_game_metadata_has_no_hardcoded_0_1_0_version`, and
   `test_game_metadata_derives_next_repository_version`.
6. Cover automatic tagging after merge with
   `test_release_workflow_tags_merged_master_commits_automatically`.
7. Cover GHCR and build/runtime version propagation with
   `test_release_workflow_pushes_semver_and_latest_images_with_same_build_version`,
   `test_dockerfile_promotes_build_version_to_runtime_environment`, and
   `test_about_displays_same_v_prefixed_release_tag_from_environment`.
8. Run the narrow test target, review every assertion against the acceptance
   checklist, and record the clean result in `.testagent/status.md`.
