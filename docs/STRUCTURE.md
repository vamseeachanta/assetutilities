# Repository structure

| Path | Purpose | Owner | Rules |
| --- | --- | --- | --- |
| .agent-os/ | Defines Agent OS commands, project context and instructions for planning and executing repository work. |  |  |
| .agent-os/agent_learning/ | Sets thresholds for recognizing task patterns and supplies the agent learning report template. |  |  |
| .agent-os/agent_os/ | Contains Python commands for managing and creating module agents. |  |  |
| .agent-os/agent_os/commands/ | Implements agent management and module-agent creation commands and retains a dated copy of the creation command. |  |  |
| .agent-os/cli/ | Provides the Agent OS command-line entry point, interactive prompts and progress display. |  |  |
| .agent-os/commands/ | Implements commands for specification writing, task execution, Git operations, test automation and environment setup. |  |  |
| .agent-os/context/ | Records domain knowledge, project patterns and team conventions in YAML for agent context. |  |  |
| .agent-os/docs/ | Indexes Agent OS slash commands and their subcommands in a reference table. |  |  |
| .agent-os/instructions/ | Gives step-by-step procedures for product planning, specification writing and task execution. |  |  |
| .agent-os/integration/ | Connects specification generation with context optimization, prompt revision and workflow updates. |  |  |
| .agent-os/modules/ | Implements agent assignment, learning, task progress tracking and prompt refinement. |  |  |
| .agent-os/product/ | Records the product mission, roadmap, technology stack and design decisions. |  |  |
| .agent-os/progress/ | Provides a template for reporting session status, task counts and execution metrics. |  |  |
| .agent-os/resources/ | Catalogs agent definitions and external templates for AI-assisted development. |  |  |
| .agent-os/standards/ | Sets out coding conventions, development practices and technology choices for Agent OS work. |  |  |
| .agent-os/sub-agents/ | Defines the responsibilities of deployment, development and testing agents. |  |  |
| .agent-os/templates/ | Provides templates for repository agent instructions and trunk-based Git configuration. |  |  |
| .claude/ | Holds repository instructions, settings, hooks and skill guides for Claude. |  |  |
| .claude/helpers/ | Provides setup and checkpoint scripts for Claude, GitHub and MCP integration. |  |  |
| .claude/hooks/ | Contains scripts for pre-task readiness checks and recording corrections. |  |  |
| .claude/memory/ | Records session context specific to the assetutilities repository. |  |  |
| .claude/skills/ | Indexes skill guides for tabular data, PDF processing and visualization. |  |  |
| .claude/skills/data-management/ | Explains how to load, filter and transform tabular data using YAML configuration. |  |  |
| .claude/skills/pdf-utilities/ | Explains how to extract tables, edit pages and work with forms and comments in PDFs. |  |  |
| .claude/skills/plotly-visualization/ | Explains how to chart data frames with Plotly and Matplotlib and export the results. |  |  |
| .codex/ | Points Codex to the shared workspace skill collection. |  |  |
| .gemini/ | Points Gemini to the shared workspace skill collection. |  |  |
| .git-commands/ | Implements Git repository management commands and their slash-command interface. |  |  |
| .github/ | Configures dependency updates and repository automation on GitHub. |  |  |
| .github/workflows/ | Defines GitHub Actions jobs for tests, source hygiene, documentation, PDF integration and releases. |  |  |
| .planning/ | Stores planning approval records indexed by issue number. |  |  |
| .planning/plan-approved/ | Records plan approval timestamps for individual issues. |  |  |
| .vscode/ | Configures editor settings, debugging and suggested extensions for Visual Studio Code. |  |  |
| config/ | Holds shell environment settings, repository layout rules, quality baselines and a data validation template. |  |  |
| config/quality/ | Records the Bandit security scan and Python source hygiene baselines. |  |  |
| config/validation/ | Supplies a data validation template with field requirements, quality thresholds and reporting options. |  |  |
| data-manifest/ | Lists the sizes, checksums and storage dispositions of files moved out of the repository or marked for retrieval. |  |  |
| docs/ | Routes readers to the source, tests and documentation for repository issues and collects developer guides. |  |  |
| docs/api/ | Provides the package API reference and instructions for building the demonstration gallery. |  |  |
| docs/commands/ | Documents agent commands, command synchronization and Git trunk workflows. |  |  |
| docs/decisions/ | Records how to synchronize project source files and specify folder-level Git exclusions. |  |  |
| docs/design/ | Describes the proposed registry for dispatching engine requests to module handlers. |  |  |
| docs/evaluations/ | Records the evidence and adoption assessment for the compound engineering plugin trial. |  |  |
| docs/examples/ | Walks through a source hygiene check with a worked example. |  |  |
| docs/maps/ | Maps modules to the source, tests and documentation needed for common issues. |  |  |
| docs/modules/ | Organizes usage guides, diagrams and examples by module or workflow. |  |  |
| docs/modules/agent-os/ | Explains how to set up, use and troubleshoot the Agent OS specification workflow. |  |  |
| docs/modules/ai/ | Collects agent configurations, prompt templates and examples of AI workflows. |  |  |
| docs/modules/ascii_workflows/ | Diagrams how text-based tools support development, documentation and collaboration. |  |  |
| docs/modules/datetime/ | Documents date parsing errors encountered when appending dates to spreadsheets. |  |  |
| docs/modules/documentation/ | Describes report generation, report structure and citation conventions. |  |  |
| docs/modules/excel_utilities/ | Shows how to configure a CSV import into a named Excel worksheet. |  |  |
| docs/modules/file_management/ | Illustrates the file management workflow and documents its input file filters. |  |  |
| docs/modules/gis/ | Introduces geographic data tools and outlines how to create a map from spatial data. |  |  |
| docs/modules/git_utilities/ | Collects Git configuration notes, command examples and troubleshooting cases. |  |  |
| docs/modules/multiprocessing/ | Compares parallel processing on one computer with distributed and cloud computing options. |  |  |
| docs/modules/pandas/ | Collects tips for working with pandas data frames. |  |  |
| docs/modules/repo_management/ | Records the status of Agent OS integration across repositories. |  |  |
| docs/modules/repositories/ | Maps primary and secondary maintenance responsibilities across public repositories. |  |  |
| docs/modules/visualization/ | Diagrams the visualization workflow and illustrates plotting with Plotly. |  |  |
| docs/modules/web_scraping/ | Documents how to troubleshoot a Scrapy reactor compatibility error. |  |  |
| docs/modules/yml_utilities/ | Explains YAML parsing, variable substitution and splitting files for plotting. |  |  |
| docs/modules/zip_utilities/ | Shows how to configure and batch ZIP creation for files with common name prefixes. |  |  |
| docs/pkg_npp/ | Links to a tutorial on finding and replacing text with regular expressions in Notepad++. |  |  |
| docs/plans/ | Collects issue implementation plans and the plan for the compound engineering trial. |  |  |
| docs/registry/ | Defines the module routing and workflow registries and documents their schema. |  |  |
| docs/reports/ | Collects generated module analysis reports and their supporting records. |  |  |
| docs/reports/modules/ | Groups reports on calculations, constants and developer tools with their change records. |  |  |
| docs/solutions/ | Explains how to record unevaluated criteria when a plugin trial lacks observations. |  |  |
| docs/standards/ | Defines the repository layout and the intended locations for project files. |  |  |
| docs/sub_automation/ | Contains an illustration of the returns from automation. |  |  |
| docs/sub_calculation_library_template/ | Diagrams the steps for developing, testing and publishing a calculation library. |  |  |
| docs/sub_ci-cd/ | Collects pipeline and scheduled-task examples with guidance on network tests and Windows scheduling. |  |  |
| docs/sub_data/ | Collects notes on data formats, file formats and nested dictionaries. |  |  |
| docs/sub_data_science/ | Describes and diagrams a proposed architecture for data science libraries. |  |  |
| docs/sub_databases/ | Collects database setup notes, MySQL examples and presentations. |  |  |
| docs/sub_databases/COD/ | Provides SQL table definitions, Python database access examples and environment setup scripts. |  |  |
| docs/sub_databases/PRE/ | Holds slide decks on MySQL setup, connection testing and data flow. |  |  |
| docs/sub_env_files/ | Defines a Conda environment for the Databricks command-line client. |  |  |
| docs/sub_file_edit/ | Explains how file order and newlines affect text file concatenation. |  |  |
| docs/sub_git/ | Collects examples for inspecting Git history, aborting merges and rebasing commits. |  |  |
| docs/sub_gmail/ | Explains how to use Gmail filters to retain and organize messages. |  |  |
| docs/sub_hardware/ | Collects hardware specifications and notes on compute capacity and remote desktop access. |  |  |
| docs/sub_hardware/_ss/ | Holds the source and rendered diagrams of shared server resources during remote desktop use. |  |  |
| docs/sub_hardware/aceengineer/ | Documents workstation resources and Windows hardware compatibility checks. |  |  |
| docs/sub_hardware/compute_server/ | Collects server specifications and a Marp presentation with its analysis inputs and plots. |  |  |
| docs/sub_ide/ | Collects Visual Studio Code shortcuts, debugging tips and troubleshooting notes. |  |  |
| docs/sub_k8_starter/ | Demonstrates how to package and deploy a small Flask application on Kubernetes. |  |  |
| docs/sub_k8_starter/app/ | Contains the Flask example and the files that define its runtime environment. |  |  |
| docs/sub_k8_starter/docker/ | Defines a Docker image that installs Flask and starts the example application. |  |  |
| docs/sub_k8_starter/kubernetes/ | Defines the Kubernetes deployment and service for the Flask example. |  |  |
| docs/sub_latex/ | Compares ways to typeset calculations and equations with Python and LaTeX. |  |  |
| docs/sub_latex/leg/ | Preserves earlier Python and TeX examples for generating equation documents and PDFs. |  |  |
| docs/sub_latex/markdown/ | Shows how to write symbolic equations to Markdown using Python. |  |  |
| docs/sub_latex/matplotlib/ | Demonstrates rendering a LaTeX equation as a Matplotlib figure. |  |  |
| docs/sub_latex/notebook/ | Demonstrates custom SymPy equation printing in a Jupyter notebook. |  |  |
| docs/sub_latex/pdflatex/ | Contains a minimal TeX document that loads the PythonTeX package. |  |  |
| docs/sub_latex/simpy/ | Shows how to print SymPy expressions and render them with Matplotlib. |  |  |
| docs/sub_logging/ | Collects Python logging references and troubleshooting notes for missing log files. |  |  |
| docs/sub_math/ | Demonstrates differentiation, integration and equation solving in Python. |  |  |
| docs/sub_math/latex/ | Collects examples for typesetting symbolic mathematics with Python, LaTeX and Matplotlib. |  |  |
| docs/sub_mathcad/ | Records the problem of extracting reviewable inputs and calculations from proprietary Mathcad files. |  |  |
| docs/sub_meetings/ | Explains how to schedule a Google Meet meeting through Google Calendar. |  |  |
| docs/sub_ms_office/ | Collects Excel and Word workflow notes and an example for generating a photo grid. |  |  |
| docs/sub_plantuml/ | Collects PlantUML guidance and examples for drawing technical diagrams. |  |  |
| docs/sub_plantuml/puml/ | Pairs PlantUML source files with example diagrams for workflows, schedules and system interactions. |  |  |
| docs/sub_presentation/ | Defines file exclusions for third-party presentation PDFs held in a private archive. |  |  |
| docs/sub_programming/ | Collects historical presentations on programming workflows and data architecture. |  |  |
| docs/sub_programming/legacy/ | Preserves draft slides on YAML workflows, data layout, Python interfaces and backups. |  |  |
| docs/sub_project_management/ | Collects guidance on agile work, communication, meetings and software team metrics. |  |  |
| docs/sub_python/ | Collects Python programming notes and examples covering language features, development tools and data handling. |  |  |
| docs/sub_python/Jupyter notebook/ | Contains a sample Jupyter notebook that introduces basic Python operations. |  |  |
| docs/sub_python/cprofile/ | Demonstrates Python performance profiling with cProfile and sample output. |  |  |
| docs/sub_python/error_handling/ | Provides Python exception handling examples for spreadsheets and text files. |  |  |
| docs/sub_python/leg_pycodes/ | Preserves earlier Python examples for databases, file handling and plotting. |  |  |
| docs/sub_python/logging/ | Introduces the Loguru library for Python logging. |  |  |
| docs/sub_release/ | Documents the build, validation and publication steps for PyPI releases. |  |  |
| docs/sub_scripting/ | Shows how to change a PowerShell window title. |  |  |
| docs/sub_shell/ | Collects Git Bash and PowerShell notes and a guide to Git branch maintenance. |  |  |
| docs/sub_utilities/ | Collects standalone utility examples for data analysis, visualization, spreadsheets and reports. |  |  |
| docs/sub_utilities/app_insights/ | UNKNOWN - The only tracked script contains a TODO and defines no behavior. |  |  |
| docs/sub_utilities/assets/ | Contains stylesheets for web interfaces alongside the utility examples. |  |  |
| docs/sub_virtualization/ | Collects environment management guidance and container examples. |  |  |
| docs/sub_virtualization/conda/ | Documents virtual environment management with Conda. |  |  |
| docs/sub_virtualization/docker/ | Provides Docker notes and container examples for two SQL Server ODBC driver versions. |  |  |
| docs/sub_virtualization/poetry/ | Documents Poetry installation, environment creation and command-line use. |  |  |
| docs/sub_virtualization/uv/ | Points readers to the official uv documentation. |  |  |
| docs/sub_visualization/ | Collects plotting examples, visualization architecture diagrams and notes on digitizing scanned plots. |  |  |
| docs/sub_visualization/plotly/ | Collects references for Plotly charts and Dash applications. |  |  |
| docs/sub_web_scraping/ | Compares web scraping tools and includes a CSV example of listing data. |  |  |
| docs/sub_web_scraping/data/ | Stores a CSV of real estate listings alongside the scraping notes. |  |  |
| docs/sub_website_hosting/ | Collects notes and slides on website hosting, GitHub Pages and Python web services. |  |  |
| examples/ | Shows how to configure and run workflows, use the engine registry and check validation rules. |  |  |
| examples/compound-engineering/ | Records the criteria and reasons for deferring the compound engineering plugin trial. |  |  |
| examples/hygiene/ | Compares Python style checker results with hand counts before and after a sample code change. |  |  |
| examples/workflows/ | Supplies example YAML inputs and fixtures for workflows run through the engine. |  |  |
| examples/workflows/csv_utilities/ | Pairs a Latin-1 CSV fixture with a configuration that exercises automatic encoding selection. |  |  |
| examples/workflows/data_exploration/ | Shows how to calculate descriptive statistics for two CSV data sets. |  |  |
| examples/workflows/edit_pdf/ | Specifies the page ranges for splitting the sample PDF supplied by the PDF reading example. |  |  |
| examples/workflows/excel_utilities/ | Demonstrates copying two CSV files into separate sheets of an Excel workbook template. |  |  |
| examples/workflows/file_edit/ | Supplies four input fragments and the configuration for concatenating them in order. |  |  |
| examples/workflows/file_management/ | Demonstrates filtering sample YAML filenames with a regular expression. |  |  |
| examples/workflows/gitpython/ | Configures a read-only search for the Git repository containing the input directory. |  |  |
| examples/workflows/read_pdf/ | Pairs a four-page synthetic PDF with a configuration for reading its first and last pages. |  |  |
| examples/workflows/reportgen/ | Shows how to generate a report from configured sections and document-specific citations. |  |  |
| examples/workflows/text_analytics/ | Provides two lists of words for the text matching and subset operations. |  |  |
| examples/workflows/visualization/ | Defines the data, axes and styles for an XY line chart. |  |  |
| examples/workflows/word_utilities/ | Shows how to convert a sample CSV table into a Word document. |  |  |
| examples/workflows/yaml_utilities/ | Shows how to reuse YAML values through variable placeholders. |  |  |
| examples/workflows/zip_utilities/ | Demonstrates grouping CSV files into ZIP archives by matching filename stems. |  |  |
| examples/yaml_split_plot/ | Demonstrates splitting YAML by top-level key and plotting a synthetic curve from its coordinate arrays. |  |  |
| modules/ | Contains reporting code for building HTML charts and locating their data. |  |  |
| modules/reporting/ | Pairs a Plotly report generator with helpers for finding input data and output files. |  |  |
| modules/reporting/templates/ | Provides a Python template for building interactive HTML reports from CSV data with Plotly. |  |  |
| modules/reporting/utils/ | Resolves project-relative paths for data files and reports. |  |  |
| results/ | Retains workflow outputs including descriptive statistics, transposed CSV tables and YAML results. |  |  |
| scripts/ | Provides repository commands for environment setup, Git operations, testing, reporting and releases. |  |  |
| scripts/au_git_sync/ | Automates recurring Git operations across repositories, including branch selection, conflict resolution and stale-branch cleanup. |  |  |
| scripts/bash/ | Groups Bash helpers for Git operations and Conda or Poetry environments. |  |  |
| scripts/bash/conda/ | Provides shell commands for managing Conda environments, installing the package locally and running tests. |  |  |
| scripts/bash/git/ | Provides Bash commands for scheduled commits, monthly branch selection and stale-branch cleanup. |  |  |
| scripts/bash/poetry/ | Creates standard and developer environments with Poetry. |  |  |
| scripts/bat/ | Provides Windows batch files for daily Git updates, commits and pushes. |  |  |
| scripts/ci/ | Maps changed paths to pytest targets for continuous integration and records quarantined tests. |  |  |
| scripts/cli/ | Contains Agent OS and slash-command launchers and Bash completion definitions. |  |  |
| scripts/context/ | Checks agent context files, analyzes usage patterns and schedules routine context checks. |  |  |
| scripts/dev/ | Provides developer commands for setting up a uv environment and executing planned tasks. |  |  |
| scripts/diagnostics/ | Explains which pytest targets continuous integration selects for a given set of changed paths. |  |  |
| scripts/enforcement/ | Checks staged files for unresolved Git conflict markers. |  |  |
| scripts/evaluation/ | Summarizes the evaluation record for the compound engineering plugin trial. |  |  |
| scripts/git/ | Provides Git utilities for branch maintenance and daily repository operations. |  |  |
| scripts/hygiene/ | Checks the source tree for layout and Python style violations. |  |  |
| scripts/maintenance/ | Verifies the repository structure and checks package data in built wheels. |  |  |
| scripts/monitoring/ | Provides scripts for checking Claude usage and suggesting a model. |  |  |
| scripts/powershell/ | Contains a PowerShell script that checks multiple Git repositories for changes. |  |  |
| scripts/release/ | Builds Python distributions and validates release artifacts. |  |  |
| scripts/reporting/ | Builds the developer tools HTML report and its change data from public API calls. |  |  |
| scripts/reports/ | Builds calculation and constants reference reports using HTML templates and stylesheets. |  |  |
| scripts/review/ | Holds review findings for repository changes. |  |  |
| scripts/review/results/ | Preserves the combined review findings for the repository structure plan. |  |  |
| scripts/tools/ | Provides a command-line tool for managing the web resources used by module agents. |  |  |
| slash_commands/ | Implements a slash command for trunk-based Git development and branch cleanup. |  |  |
| src/ | Contains the assetutilities Python package and separate Agent OS workflow modules. |  |  |
| src/assetutilities/ | Provides the engine that runs configured workflows, engineering calculations and shared utility APIs. |  |  |
| src/assetutilities/agent_os/ | Implements Agent OS commands for creating module agents, managing specifications and distributing commands across repositories. |  |  |
| src/assetutilities/base_configs/ | Supplies default YAML configurations for workflows such as spreadsheet processing, plotting and PDF extraction. |  |  |
| src/assetutilities/calculations/ | Implements engineering calculations for offshore risers, pipelines, wells and lifecycle costs. |  |  |
| src/assetutilities/cli/ | Provides command-line scripts for creating agents and specifications and distributing slash commands. |  |  |
| src/assetutilities/common/ | Provides shared routines for file handling, data processing, configuration, logging and visualization. |  |  |
| src/assetutilities/constants/ | Defines unit conversions and reference values for casing grades, materials and seawater. |  |  |
| src/assetutilities/devtools/ | Provides repository maintenance commands for modernizing dependencies, organizing directories and distributing commands. |  |  |
| src/assetutilities/line_dynamics_report/ | Reproduces workbook formulas for line bending reports and layback summaries in Python. |  |  |
| src/assetutilities/modules/ | Groups workflow implementations for tabular data, spreadsheets, PDF documents, YAML, Git and ZIP archives. |  |  |
| src/assetutilities/tests/ | Contains package-side tests for engineering calculations such as pipeline, riser and wellhead fatigue analyses. |  |  |
| src/assetutilities/units/ | Parses engineering quantities, applies unit policies and formats calculated values for output. |  |  |
| src/assetutilities/workflow_api/ | Defines how workflows accept inputs, run, record results and publish artifacts. |  |  |
| src/modules/ | Holds Agent OS extensions for specification creation, cross-repository integration and web resource processing. |  |  |
| src/modules/agent-os/ | Provides configuration, templates and workflow components for creating enhanced specifications across repositories. |  |  |
| src/modules/agent_os/ | Implements and demonstrates saving specifications and using them across repositories. |  |  |
| src/modules/web-contextualization/ | Fetches and caches web resources, extracts PDF content and indexes it for search. |  |  |
| tests/ | Contains automated checks and fixtures for package behavior, engineering calculations and repository workflows. |  |  |
| tests/agent_os/ | Tests Agent OS configuration, commands and interactions between workflow components. |  |  |
| tests/agent_os/cli/ | Tests interactive command-line sessions, progress indicators and error handling. |  |  |
| tests/agent_os/commands/ | Tests module-agent creation and command handling for context, documentation, specifications and templates. |  |  |
| tests/agent_os/integration/ | Tests enhanced specification workflows and the retention of engineering values in learning records. |  |  |
| tests/bash-setup/ | Tests project detection and how the Git Bash setup script configures a shell. |  |  |
| tests/bash-setup/bash-tests/ | Runs shell tests for backing up and modifying Bash startup files. |  |  |
| tests/benchmarks/ | Measures execution time for two functions used in steel catenary riser fatigue calculations. |  |  |
| tests/ci/ | Tests changed-file test selection and the policy governing tests that require network access. |  |  |
| tests/common/ | Checks configuration, logging and output paths when the engine runs inside another application. |  |  |
| tests/data_store/ | Tests manifest-based file restoration and checks that compact archive fixtures preserve table rows. |  |  |
| tests/devtools/ | Tests how the diagnostic command explains test selection for changed paths. |  |  |
| tests/docs/ | Checks that the documentation index, operator map and module registry direct readers to existing code. |  |  |
| tests/evaluation/ | Tests how the compound trial evaluator validates evidence and determines readiness for review. |  |  |
| tests/governance/ | Checks that repository hooks are self-contained and retired identifier checks stay disabled. |  |  |
| tests/hygiene/ | Checks repository hygiene rules for backup artifacts, personal references and YAML fixture headers. |  |  |
| tests/modules/ | Groups workflow and calculation tests with their module-specific configurations, inputs and expected results. |  |  |
| tests/modules/agent-os/ | Tests enhanced specification workflows, documentation templates and integration with the Agent OS framework. |  |  |
| tests/modules/agent_os/ | Tests persistence and cross-repository integration in the Python specification workflow. |  |  |
| tests/modules/all_yml_tests/ | Runs YAML configurations found in the test tree and records the outcomes in a CSV file and a text summary. |  |  |
| tests/modules/calculations/ | Checks engineering calculations and their reports, including riser fatigue, pipeline design and lifecycle cost. |  |  |
| tests/modules/csv_utilities/ | Tests CSV input routing, encoding selection, delimiters and row limits. |  |  |
| tests/modules/data_exploration/ | Uses tabular fixtures to test descriptive statistics and their addition to data frames. |  |  |
| tests/modules/devtools/ | Tests dependency modernization, repository discovery and regeneration of the developer tools report. |  |  |
| tests/modules/download_data/ | Tests ZIP downloads and offline handling with a configured archive input. |  |  |
| tests/modules/edit_pdf/ | Tests splitting PDFs into files for specified inclusive page ranges. |  |  |
| tests/modules/excel_utilities/ | Tests CSV imports, custom calculations and image export with spreadsheet fixtures. |  |  |
| tests/modules/file_edit/ | Provides input decks, configurations and tests for splitting and concatenating files. |  |  |
| tests/modules/file_management/ | Tests file selection by name, size and regular expression against fixture files. |  |  |
| tests/modules/gallery/ | Verifies example calculations, artifact discovery and generation of the self-contained HTML gallery. |  |  |
| tests/modules/git_utilities/ | Checks that Git utilities inspect repository states without changing files or the Git index. |  |  |
| tests/modules/line_dynamics_report/ | Checks bending reports and layback summaries against formula results and workbook-derived fixtures. |  |  |
| tests/modules/pipeline_ci_cd/ | Compares the successful YAML run count in the status CSV with the count in the text summary. |  |  |
| tests/modules/read_pdf/ | Tests extraction of PDF page text, handling of page selections and routing to optional table readers. |  |  |
| tests/modules/reportgen/ | Provides report configurations and sample Word and Markdown output for report generation tests. |  |  |
| tests/modules/tests_wip/ | Collects work-in-progress cases for PDF reading and polar plots. |  |  |
| tests/modules/visualization/ | Tests plot generation with CSV data and YAML configurations for polar, time-series and XY plots. |  |  |
| tests/modules/web_scraping/ | Tests scraper selection and workflows that use Beautiful Soup and Scrapy. |  |  |
| tests/modules/word_utilities/ | Tests searching Word documents and converting tabular data to Word tables. |  |  |
| tests/modules/yml_utilities/ | Tests splitting, reshaping and reassembling YAML data and plotting values from YAML files. |  |  |
| tests/modules/zip_utilities/ | Tests grouping files into archives by stem and reading archived tabular data into data frames. |  |  |
| tests/release/ | Tests release tag validation, distribution builds and publishing workflow permissions. |  |  |
| tests/repo_structure/ | Tests the repository structure checker against root directory rules and tracked artifact exceptions. |  |  |
| tests/reports/ | Checks the arithmetic, cited sources and offline regeneration of the engineering constants report. |  |  |
| tests/unit/ | Contains focused tests for shared data utilities, command-line parsing, units and other package behavior. |  |  |
| tests/workflow_api/ | Tests workflow inputs, execution records, metrics, artifacts and publication behavior. |  |  |
| tests/workflows/ | Checks workflow registry entries, command-line examples and continuous integration triggers. |  |  |
