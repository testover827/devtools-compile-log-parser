# Changelog

- perf: precompile regexes with LRU cache (DEVTOOLS_REGEX_CACHE_SIZE, default 5000)
- perf: add scripts/build_module_groups.py to emit group-specific JSON files
- perf: add scripts/mark_mvc_for_deletion.py to locate and optionally remove MVC-related files
- tests: add unit tests for regex cache and module-group builder
