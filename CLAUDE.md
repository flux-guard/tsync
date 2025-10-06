# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**tsync** is a toolkit synchronization system that allows consumer projects to synchronize files, configurations, and templates from a central provider repository (toolkit). It supports multiple synchronization strategies (policies) and variable-based templating.

### Core Concepts

- **Provider**: A Git repository containing the toolkit (`.toolkit.yml`) with reusable files, components, and aliases
- **Consumer**: A project that uses the toolkit (`.project.toolkit.yml`) to synchronize specific components
- **Policy**: The synchronization strategy for a file (sync-strict, init, template, merge)
- **Component**: A logical group of files with a common purpose (e.g., 'dockerfile', 'linters')
- **Alias**: A named set of components that can be requested as a unit (e.g., 'python-service')
- **Context**: An execution context object passed to strategies containing all necessary sync information

## Architecture

### Strategy Pattern Implementation

The codebase uses the Strategy pattern for file synchronization. Each policy has its own handler:

- **SyncStrictStrategy** (`handlers/sync_strict.py`): Forcibly overwrites files in the consumer project
- **InitStrategy** (`handlers/init.py`): Copies files only if they don't exist
- **TemplateStrategy** (`handlers/template.py`): Renders Jinja2 templates with variables
- **MergeStrategy** (`handlers/merge.py`): Intelligently merges content based on file type

All strategies inherit from `BaseStrategy` (`handlers/base.py`) and implement the `apply(context: Context)` method.

### Service Layer

Three core services orchestrate the sync process:

- **SyncService** (`services/sync.py`): Main orchestrator managing the entire sync lifecycle
- **GitService** (`services/git.py`): Handles Git operations (clone, fetch, checkout)
- **FileSystemService** (`services/fs.py`): Encapsulates all file I/O operations
- **TemplateService** (`services/template.py`): Handles Jinja2 template rendering

### Data Models

Pydantic models in `models/` define contracts for:

- **provider.py**: Toolkit manifest structure (`.toolkit.yml`)
- **consumer.py**: Project manifest structure (`.project.toolkit.yml`)
- **policy.py**: Enum defining all sync policies
- **merge.py**: Merge types and priority settings
- **context.py**: Context object passed to strategies

### Variable Resolution Hierarchy

Variables are resolved with the following priority (highest to lowest):

1. File-level vars (consumer override) - `ComponentOverride.files[].vars`
2. File-level vars (provider default) - `File.vars`
3. Component-level vars (consumer override) - `ComponentOverride.vars`
4. Component-level vars (provider default) - `Component.vars`
5. Alias-level vars (provider default) - `Alias.vars`
6. Global vars (consumer `.project.toolkit.yml`) - Includes variant defaults!

**Note**: In the code implementation (from lowest to highest priority), variables are applied in reverse order: global vars → alias vars → component (provider) vars → component (consumer) vars → file (provider) vars → file (consumer) vars. This means file-level consumer overrides have the highest priority and will overwrite all other values.

## Development Commands

The project uses a standard Python structure with `src/` layout and setuptools for packaging.

```bash
# Install in development mode with dependencies
pip install -e .

# Install with development dependencies (includes pytest, black, ruff, mypy)
pip install -e ".[dev]"

# Run tsync CLI
tsync --help
tsync --project-dir /path/to/project --cache-dir ~/.tsync/cache
tsync --verbose  # Enable debug logging

# Run tests (when available)
pytest

# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## Key Implementation Notes

- The `SyncService._process_sync_items()` method iterates through sync items from the consumer manifest
- Each file gets a `Context` object built in `SyncService._process_component()`
- Strategies are instantiated once in `SyncService.__init__()` and reused
- **Mergers are cached**: MergeStrategy creates merger instances once in `__init__()` for better performance
- Git repositories are cached locally in `~/.tsync/cache` by default to avoid repeated clones
- **SSH security**: Git operations use `BatchMode=yes` to prevent interactive password prompts
- File operations go through `FileSystemService` for testability and proper error handling
- **Path traversal protection**: All destination paths validated via `validate_path_within_directory()`
- Merge handlers are in `handlers/mergers/` (yaml.py, json.py, text.py)
- **Code deduplication**: `_deep_merge_dicts` moved to `BaseMerger` to eliminate duplication
- **Tag-based filtering** is implemented in `SyncService._should_include_file()` (sync.py:~343)
- **Variable override hierarchy** is fully implemented in `SyncService._resolve_variables()` (sync.py:~370)
- **Variant support**: Implemented in `_get_variant_variables()` and integrated into variable resolution
- **Schema validation**: Required variables validated in `_validate_component_schema()` (sync.py:~294)
- **File-level destination override**: Implemented in `_build_destination_path()` (sync.py:~265)
- **Template rendering**: Uses Jinja2 Environment with StrictUndefined for better error detection
- Logging is used throughout instead of print statements for proper output control
- Error handling with custom exceptions: `FileSystemError`, `GitServiceError`
- All type hints use `typing` module types (Dict, List, Optional) for Python 3.10+ compatibility

## CLI Entry Point

The main CLI is defined in `cli.py` with the following options:
- `--project-dir`: Path to consumer project (default: current directory)
- `--cache-dir`: Path to toolkit cache (default: ~/.tsync/cache)
- `--verbose/-v`: Enable debug logging
- `--version`: Show version

The application flow: CLI → TsyncApp → SyncService → Strategies

## Error Handling

- `FileSystemError`: Raised for file I/O issues (missing files, invalid YAML, permission errors)
- `GitServiceError`: Raised for git operations failures
- All errors propagate up with descriptive messages
- Validation checks exist for config file existence before attempting to load
- MergePriority defaults to TOOLKIT if not specified in provider config

## Code Comments

All module docstrings and many inline comments are in Russian, describing the purpose and functionality of each component.

## Recent Improvements

### Security Enhancements
- ✅ **Path Traversal Protection**: All destination paths validated to prevent `../../etc/passwd` attacks
- ✅ **SSH Security**: Git operations configured with `BatchMode=yes` to prevent hanging on password prompts
- ✅ **Strict Template Validation**: Jinja2 uses `StrictUndefined` to catch undefined variables early

### New Features
- ✅ **Variant Support**: Consumers can select variants to apply preset variable defaults
- ✅ **Schema Validation**: Required variables are validated against component schema
- ✅ **File-level Destination Override**: Override destination path per file, not just per component

### Code Quality Improvements
- ✅ **Eliminated Code Duplication**: `_deep_merge_dicts` moved to `BaseMerger` (removed 30+ duplicate lines)
- ✅ **Performance Optimization**: Mergers cached in MergeStrategy (no repeated instantiation)
- ✅ **Better Template Service**: Removed incorrect FileSystemLoader, now uses proper string-based templates
- ✅ **Comprehensive Tests**: Added 50+ new tests covering security, variants, schema validation, and merge priority

### Architecture Refinements
- ✅ **Cleaner Path Building**: Extracted to `_build_destination_path()` with clear priority logic
- ✅ **Improved Variable Resolution**: Now includes alias vars and variant defaults in hierarchy
- ✅ **Better Error Messages**: Validation errors include variable descriptions and component context

## Quick Reference

### Project Structure
```
src/tsync/
├── models/           # Pydantic data models
│   ├── provider.py   # .toolkit.yml structure
│   ├── consumer.py   # .project.toolkit.yml structure
│   ├── policy.py     # Policy enum (sync-strict, init, template, merge)
│   ├── merge.py      # MergeType, MergePriority
│   └── context.py    # Context passed to strategies
├── services/         # Business logic layer
│   ├── sync.py       # Main orchestrator (SyncService)
│   ├── git.py        # Git operations (GitService)
│   ├── fs.py         # File I/O (FileSystemService)
│   └── template.py   # Jinja2 rendering (TemplateService)
├── handlers/         # Strategy pattern implementations
│   ├── base.py       # BaseStrategy abstract class
│   ├── sync_strict.py
│   ├── init.py
│   ├── template.py
│   ├── merge.py
│   └── mergers/      # Merge type handlers
│       ├── base.py
│       ├── yaml.py
│       ├── json.py
│       └── text.py
├── app.py            # Application entry point (TsyncApp)
└── cli.py            # CLI argument parsing

tests/
├── test_models/
├── test_services/
├── test_handlers/
│   └── test_mergers/
└── integration/
```

### Key Files to Check First

When debugging or adding features, start with these files:

1. **Understanding data flow**: `services/sync.py` - contains the main orchestration logic
2. **Data structures**: `models/provider.py` and `models/consumer.py` - understand manifest schemas
3. **Strategy execution**: `handlers/base.py` - strategy interface, then specific strategy files
4. **Variable resolution**: `services/sync.py:_resolve_variables()` at line ~370
5. **Tag filtering**: `services/sync.py:_should_include_file()` at line ~343
6. **Path building**: `services/sync.py:_build_destination_path()` at line ~265
7. **Schema validation**: `services/sync.py:_validate_component_schema()` at line ~294
8. **Variant support**: `services/sync.py:_get_variant_variables()` at line ~175

### Common Patterns

**Error Handling**:
- Custom exceptions: `FileSystemError`, `GitServiceError`
- All errors propagate with descriptive messages
- Use logging instead of print statements

**Type Hints**:
- Use `typing` module types: `Dict`, `List`, `Optional` (Python 3.10+ compatible)
- All public methods should have type hints
- Pydantic models handle validation automatically

**Service Instantiation**:
- Services instantiated once in `TsyncApp.run()` or `SyncService.__init__()`
- Pass services via dependency injection
- Strategies reused across multiple files

**Testing**:
- Unit tests for each module in `tests/test_<module>/`
- Integration tests in `tests/integration/`
- Use pytest fixtures from `conftest.py`

### Critical Implementation Details

1. **Variable Priority** (highest to lowest):
   - File-level vars (consumer override)
   - File-level vars (provider default)
   - Component-level vars (consumer override)
   - Component-level vars (provider default)
   - Alias-level vars (provider default)
   - Global vars (consumer `.project.toolkit.yml`) - includes variant defaults

2. **Tag Filtering Logic**:
   - `include_tags`: File must have AT LEAST ONE tag from the list
   - `exclude_tags`: File is excluded if it has ANY tag from the list
   - `exclude_tags` takes precedence over `include_tags`

3. **Merge Priority**:
   - `MergePriority.TOOLKIT` (default): toolkit values overwrite project values
   - `MergePriority.PROJECT`: project values are preserved

4. **Git Caching**:
   - Repos cached in `~/.tsync/cache` by default
   - Clone once, fetch on subsequent runs
   - Checkout specified version (branch/tag/commit)

### Performance Considerations

- File operations go through `FileSystemService` for proper error handling and testability
- Git repos are cached locally to avoid repeated clones
- Strategies instantiated once and reused for all files
- Jinja2 templates rendered on-demand with variable context

### When Adding New Features

**New Policy/Strategy**:
1. Add enum value to `models/policy.py`
2. Create handler in `handlers/<policy_name>.py` inheriting from `BaseStrategy`
3. Register strategy in `SyncService.__init__()`
4. Add tests in `tests/test_handlers/test_<policy_name>.py`

**New Merge Type**:
1. Add enum value to `models/merge.py`
2. Create merger in `handlers/mergers/<type>.py` inheriting from `BaseMerger`
3. Register merger in `MergeStrategy.__init__()`
4. Add tests in `tests/test_handlers/test_mergers/test_<type>.py`

**New Service**:
1. Create service file in `services/<name>.py`
2. Initialize in `TsyncApp.run()` or appropriate service
3. Inject as dependency where needed
4. Add tests in `tests/test_services/test_<name>.py`

## Usage Examples

### Using Variants

**Provider (`.toolkit.yml`):**
```yaml
toolkit_version: "1.0.0"
aliases:
  python-service:
    description: "Python service configuration"
    variants:
      poetry:
        description: "Use Poetry for dependency management"
        defaults:
          package_manager: "poetry"
          lock_file: "poetry.lock"
      pip:
        description: "Use pip for dependency management"
        defaults:
          package_manager: "pip"
          lock_file: "requirements.txt"
    components:
      - id: dependencies
        var_schema:
          package_manager:
            description: "Package manager to use"
            required: true
        files:
          - source: "templates/deps.txt.j2"
            destination: "requirements.txt"
            policy: template
```

**Consumer (`.project.toolkit.yml`):**
```yaml
provider:
  url: "git@github.com:company/toolkit.git"
  version: "v1.0.0"

sync:
  - alias: python-service
    variant: poetry  # Applies poetry defaults
    # No need to specify package_manager manually!
```

### File-level Destination Override

**Consumer:**
```yaml
sync:
  - alias: docker
    overrides:
      - id: dockerfile
        destination_root: "build"  # Component-level
        files:
          - source: "templates/Dockerfile"
            destination: "docker/Dockerfile.custom"  # File-level (highest priority!)
```

### Schema Validation

**Provider:**
```yaml
components:
  - id: app
    var_schema:
      app_name:
        description: "Application name"
        required: true  # Will error if not provided!
      app_port:
        description: "Application port"
        required: false
        default: 8080
```

**Consumer (will fail):**
```yaml
# ERROR: Missing required variable 'app_name'
sync:
  - alias: my-app
    overrides:
      - id: app
        vars:
          app_port: 3000  # Optional var provided, but required 'app_name' missing!
```
