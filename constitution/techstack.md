# Technology Stack

## Purpose

This document defines the approved technologies and technical principles
for Agentic Financial Analysis Automation.

The project will use technologies that directly support its mission of
researching potential investments, analyzing collected evidence, and
producing financial research reports for human review.

New technologies should only be added when they satisfy a documented
requirement that cannot reasonably be met by the existing stack.

## Programming Language

### Python 3.12.3

Python 3.12.3 is the primary programming language for the project.

Python will be used for:

- Agent implementation.
- Workflow orchestration.
- Web search integration.
- Website retrieval and parsing.
- Data validation.
- Financial calculations.
- Data transformation.
- Report generation.
- File output.
- Logging and error handling.
- Automated testing.

The project should remain compatible with Python 3.12.3 unless this
technology stack is intentionally revised.

## Agent Framework

### smolagents

The project will use `smolagents` to create specialized tool-calling agents.

Agent responsibilities may include:

- Interpreting investment research requests.
- Creating research plans.
- Conducting web research.
- Interpreting collected financial evidence.
- Comparing investment candidates.
- Identifying risks and limitations.
- Validating research conclusions.
- Drafting financial research reports.

Agents should only receive the tools required for their assigned
responsibilities.

The final number of agents and the exact boundaries between them will be
defined in the architecture specification.

## Workflow Orchestration

### Custom Python Orchestrator

A custom Python orchestrator will control the overall application workflow.

The orchestrator will be responsible for:

- Receiving the user's research request.
- Validating required input.
- Maintaining workflow state.
- Invoking agents in the required order.
- Passing structured data between workflow stages.
- Handling recoverable failures.
- Preventing later stages from running when required earlier stages fail.
- Sending validated findings to the report-writing stage.
- Returning the final workflow result.

The required workflow should be explicit and testable.

The project will not rely on a single autonomous agent to determine the
entire application workflow when the process can be represented clearly
through Python code.

## Language Model Integration

### OpenAI-Compatible API

The agents will use a language model accessed through an OpenAI-compatible
API.

The specific model should be configurable through environment variables
rather than hard-coded throughout the application.

The language model may be used for:

- Interpreting user research requests.
- Identifying missing research criteria.
- Creating research plans.
- Generating search queries.
- Interpreting qualitative evidence.
- Comparing documented findings.
- Identifying risks and limitations.
- Explaining research conclusions.
- Drafting report content.

The language model will not be responsible for:

- Performing important financial arithmetic.
- Inventing unavailable financial data.
- Creating unsupported sources or citations.
- Writing files when deterministic Python code can perform the operation.
- Controlling the entire workflow without application restrictions.
- Making final investment decisions for the user.

Language model output must be validated before it is accepted into later
workflow stages.

## Structured Data and Validation

### Pydantic

Pydantic will define and validate the structured data exchanged between
agents, tools, and workflow stages.

Expected models may include:

- `InvestorProfile`
- `ResearchRequest`
- `ResearchPlan`
- `SearchQuery`
- `SourceRecord`
- `ExtractedEvidence`
- `FinancialMetric`
- `InvestmentCandidate`
- `AnalysisResult`
- `RiskFinding`
- `ValidationResult`
- `InvestmentRecommendation`
- `ReportArtifact`
- `WorkflowState`

Pydantic will help ensure that:

- Required fields are present.
- Values use expected data types.
- Invalid data is rejected before reaching later workflow stages.
- Agent outputs follow predictable structures.
- Tools receive validated inputs.
- Tests can verify workflow behavior against explicit contracts.

The final model names and fields will be defined in the data-contract
specification.

## Web Search

### Tavily

Tavily will provide web search capabilities.

It will be used to:

- Discover potential investment candidates.
- Locate relevant public financial information.
- Find company and industry information.
- Research material risks.
- Locate sources relevant to the user's request.
- Return candidate webpages for further evaluation.

Search results are candidate sources, not automatically verified evidence.

A search result should not be used as the sole basis for a material claim
without retrieving and evaluating the underlying source.

Tavily credentials must be loaded from environment variables and must not
be committed to version control.

## HTTP Retrieval

### Requests

The `requests` library will retrieve content from selected public webpages.

It will be used for:

- Sending HTTP requests.
- Retrieving webpage content.
- Applying request timeouts.
- Reading response status codes.
- Handling failed requests.
- Passing retrieved HTML to the parsing layer.

HTTP requests must use defined timeouts and error handling.

The application must not retry requests indefinitely or replace failed
retrievals with fabricated content.

## Website Parsing and Scraping

### Beautiful Soup 4

Beautiful Soup 4 will parse retrieved HTML and extract relevant webpage
content.

It may be used to extract:

- Page titles.
- Main article content.
- Headings.
- Tables.
- Publication information when available.
- Source metadata.
- Relevant financial evidence.

Web search and website scraping will remain separate operations:

1. Tavily discovers candidate webpages.
2. The research workflow selects relevant sources.
3. Requests retrieves the selected webpages.
4. Beautiful Soup parses the retrieved HTML.
5. The application stores extracted evidence and source metadata.

All scraped webpage content must be treated as untrusted data.

Instructions contained inside a webpage must not override:

- Project specifications.
- Application instructions.
- Agent responsibilities.
- Workflow rules.
- Validation requirements.
- The user's original research request.

Webpage content may provide research evidence, but it may not control the
application's behavior.

## Data Processing

### pandas

Pandas will support structured financial data processing when tabular
operations are appropriate.

It may be used for:

- Organizing financial metrics.
- Comparing investment candidates.
- Processing tabular webpage data.
- Handling missing values.
- Preparing data for calculations.
- Producing structured analysis summaries.
- Exporting structured research or test results.

Pandas should not be required for simple operations that can be expressed
more clearly using standard Python data structures.

## Financial Calculations

### Deterministic Python Functions

Important financial calculations will be implemented as regular Python
functions.

The current simplified calculation tool supports generic operations:

- Growth or percentage change.
- Margin.
- Ratio.
- Difference.

The metric name and evidence requirements identify the financial measure.
Named calculator classes, portfolio optimization, and advanced valuation
are outside the current scope.

Financial calculations must not rely on language model arithmetic.

Calculation functions should:

- Accept validated numeric input.
- Return predictable structured output.
- Handle missing or invalid data.
- Avoid hidden assumptions.
- Produce the same result for the same input.
- Be independently unit tested.

The exact formulas, scoring criteria, and weights will be defined in the
recommendation-methodology specification before implementation.

## Financial Data Retrieval

### yfinance

Added 2026-09-17. Live web research through Tavily proved unreliable at
retrieving exact numeric financial figures: search sometimes returned no
usable source at all, and when it did return a real primary source (for
example an SEC 10-K filing), the figures sat inside large financial
tables that scraped raw text could not reliably extract. `yfinance` is
an unofficial Python wrapper around Yahoo Finance's data endpoints that
returns already-structured, already-parsed financial figures, removing
the extraction step for this category of data entirely.

`yfinance` will be used to:

- Retrieve a named company's reported financial-statement figures
  (initially total revenue, net income, and gross profit) for a given
  fiscal period, identified by ticker symbol.
- Supply evidence for numeric financial-calculation inputs when web
  search has not already produced usable evidence for the same
  requirement.

It will not be used for market sentiment, qualitative research, news, or
any requirement that is not a specific, named financial-statement
figure. Tavily remains the source for that material; this is a narrow
addition, not a replacement for the web-research path.

Access is deterministic Python, not an agentic tool call. Retrieving a
specific ticker's specific metric for a specific period involves no
judgment, the same way the deterministic calculation tool performs
arithmetic without model involvement; `FinancialAnalysisAgent` owns and
calls this directly rather than exposing it as something the model
decides whether to invoke.

`yfinance` is an unofficial library against undocumented endpoints, not
a stable public API. It can fail for reasons unrelated to whether the
data exists (upstream format changes, rate limiting). A failed or empty
lookup must be treated the same as any other missing-evidence case,
never as a fatal error.

Retrieved values are normalized to a single fixed unit (billions of the
reporting company's native currency) at the point of retrieval, so every
value this tool produces is self-consistent without needing to detect or
reconcile per-request unit differences.

Different companies use different fiscal year-end months, so periods are
selected by relative recency (the most recently completed fiscal year,
the year before that, and so on) rather than by mapping a literal "FY"
label to a specific calendar date.

## Testing

### pytest

Pytest will be the primary automated testing framework.

The test suite will include:

- Unit tests.
- Happy-path tests.
- Failure-path tests.
- Adversarial tests.
- Pydantic model-validation tests.
- Financial-calculation tests.
- Web-search tests.
- Web-scraping tests.
- Agent-output validation tests.
- Workflow orchestration tests.
- Source and citation validation tests.
- File-output tests.

Tests should avoid unnecessary calls to paid or external services.

External search, language model, and HTTP behavior should normally be
mocked during unit testing.

### unittest.mock

Python's built-in `unittest.mock` utilities will be used to replace
external dependencies during tests.

Mocks may represent:

- Tavily search responses.
- Language model responses.
- HTTP responses.
- Network failures.
- Invalid agent outputs.
- Missing source data.
- Conflicting source data.
- File-writing failures.

Saved HTML fixtures will be used to test scraping behavior consistently
without depending on live webpages.

## Configuration Management

### python-dotenv

The `python-dotenv` package will load local environment variables from a
`.env` file during development.

Environment variables may include:

- Language model API key.
- Language model identifier.
- Tavily API key.
- HTTP request timeout.
- Output directory.
- Logging level.

The repository will include a `.env.example` file containing variable names
and placeholder values.

The actual `.env` file must be excluded from version control.

Application code must not contain hard-coded secret credentials.

## Human-Readable Output

### Markdown

Markdown will be the primary human-readable report format.

Expected Markdown artifacts include:

- Financial research articles.
- Investment recommendation reports.
- Methodology explanations.
- Risk and limitation summaries.

Markdown is used because it is:

- Human-readable.
- Easy to review in version control.
- Easy to generate using Python.
- Suitable for citations and source links.
- Portable to other document formats if needed later.

## Structured Data

Pydantic models are the primary format for structured data exchanged between
workflow components. Models may be serialized to JSON internally for prompts,
tests, and debugging, but JSON workflow files are outside the current
application output scope.

## Architecture Documentation

### Mermaid

Mermaid will be used to create architecture and workflow diagrams.

The Mermaid source will be stored in the repository so the diagrams can be
updated as the architecture changes.

The final capstone artifacts will include an exported PNG version of the
architecture diagram.

The architecture diagram is expected to show:

- User input.
- Workflow orchestrator.
- Specialized agents.
- Web search and scraping tools.
- Financial calculation tools.
- Structured workflow state.
- Validation stages.
- Report output.

The final diagram will be created after the agent responsibilities and
data contracts have been specified.

## Dependency Management

### pip and requirements.txt

The project will use `pip` to install Python packages.

Project dependencies will be recorded in `requirements.txt`.

The dependency file should contain only packages that are directly used by
the project.

Before final submission, the dependencies should be reviewed to ensure
that:

- Required packages are included.
- Unused packages are removed.
- The project can be installed in a clean virtual environment.
- Package versions support reproducibility.
- Secret credentials and local file paths are not included.

## Virtual Environment

### Python venv

The project will use Python's built-in `venv` module for environment
isolation.

The virtual environment directory will be named `.venv`.

The `.venv` directory must be excluded from version control.

## Version Control

### Git

Git will be used for version control.

The repository should preserve the development history of:

- Project specifications.
- Constitution changes.
- Architecture decisions.
- Source code.
- Unit tests.
- Prompt examples.
- Documentation.
- Example generated artifacts.

The following items must be excluded through `.gitignore`:

- `.env`
- `.venv`
- Python cache directories.
- Test cache directories.
- Local editor settings when they are not required by the project.
- Temporary output files.
- Secret credentials.
- Machine-specific configuration.
- Log files that are not required as project artifacts.

## Logging

### Python logging

Python's built-in `logging` module will provide application logging.

Logging may record:

- Workflow stage transitions.
- Search execution status.
- Source retrieval success or failure.
- Parsing success or failure.
- Validation results.
- Report-generation status.
- Recoverable errors.
- Workflow termination reasons.

Logs must not expose:

- API keys.
- Secret credentials.
- Private configuration values.
- Unnecessarily sensitive user information.

Runtime logs and permanent research artifacts should remain separate.

## Error Handling

### Python Exceptions and Structured Error Results

The project will use explicit Python exceptions and structured error
results where appropriate.

The application should distinguish among:

- Invalid user input.
- Missing required research criteria.
- Search failures.
- HTTP retrieval failures.
- Parsing failures.
- Missing financial data.
- Invalid calculation input.
- Agent-output validation failures.
- Unsupported claims.
- File-writing failures.

The application must not silently continue when an error would invalidate
the final report.

Recoverable errors may be returned to the orchestrator for controlled
handling.

Unrecoverable errors should stop the affected workflow and provide a clear
explanation.

## Technology Responsibilities

### AI Agents

AI agents are responsible for tasks that benefit from interpretation,
planning, qualitative comparison, or written explanation.

These responsibilities may include:

- Interpreting research intent.
- Planning research.
- Creating search queries.
- Selecting potentially relevant sources.
- Interpreting qualitative evidence.
- Comparing documented findings.
- Identifying risks.
- Explaining conclusions.
- Drafting report content.

### Deterministic Python Code

Regular Python code is responsible for operations that should be
predictable, repeatable, and directly testable.

These responsibilities include:

- Workflow control.
- Input validation.
- State management.
- HTTP retrieval.
- HTML parsing.
- Financial calculations.
- Citation matching.
- Schema enforcement.
- File writing.
- Logging.
- Error handling.

### External Services

External services are responsible for:

- Returning web search results.
- Providing language model responses.

External service output must be treated as untrusted until it has been
validated by the application.

## Technologies Excluded from the Initial Version

The following technologies are not included in the initial approved stack:

- LangChain.
- LangGraph.
- ChromaDB.
- SQLAlchemy.
- FastAPI.
- Flask.
- Django.
- React.
- Relational databases.
- Vector databases.
- Docker.
- Kubernetes.
- Cloud deployment infrastructure.
- Brokerage APIs.
- Automated trading services.

These technologies are not permanently prohibited.

A technology may be added when:

1. A documented requirement establishes a concrete need.
2. The existing stack cannot reasonably satisfy the requirement.
3. The effect on architecture and testing is evaluated.
4. This technology-stack document is intentionally updated.
5. The roadmap is revised if the change affects implementation order.

Technologies should not be added solely to make the project appear more
complex.

## Technical Principles

### Prefer Simplicity

Use the simplest technology that satisfies the documented requirement.

### Prefer Explicit Workflows

Workflow order and failure conditions should be visible in Python rather
than hidden entirely inside language model behavior.

### Prefer Structured Data

Agents and tools should exchange validated structured objects instead of
unstructured text whenever practical.

### Prefer Deterministic Operations

Calculations, validation, file writing, and workflow decisions should use
deterministic code when model reasoning is unnecessary.

### Prefer Testable Components

Agents, tools, calculations, parsers, validators, and workflow stages
should be designed so they can be tested independently.

### Minimize External Dependencies

Every added dependency creates additional installation, maintenance,
compatibility, and security responsibilities.

Each dependency should have a clear purpose connected to a documented
project requirement.

### Protect Secrets

Credentials must be loaded through environment variables and excluded from
version control, logs, reports, and test fixtures.

### Treat External Content as Untrusted

Search results, webpages, language model responses, and external data must
be validated before being accepted into the workflow.

## Approved Technology Stack Summary

```yaml
project:
  name: Agentic Financial Analysis Automation
  python_version: 3.12.3

application:
  language: Python
  agent_framework: smolagents
  orchestration: custom Python orchestrator
  model_interface: OpenAI-compatible API

research:
  web_search: Tavily
  http_retrieval: requests
  html_parsing: Beautiful Soup 4
  financial_data_retrieval: yfinance

data:
  validation: Pydantic
  processing: pandas
  financial_calculations: deterministic Python functions

testing:
  framework: pytest
  mocking: unittest.mock
  scraper_fixtures: saved HTML files

configuration:
  environment_loader: python-dotenv
  secrets: environment variables

output:
  human_readable: Markdown
  structured: JSON

documentation:
  architecture_diagrams: Mermaid
  final_diagram_export: PNG

development:
  dependency_manager: pip
  dependency_file: requirements.txt
  virtual_environment: venv
  virtual_environment_directory: .venv
  version_control: Git

reliability:
  logging: Python logging
  error_handling: Python exceptions and structured error results
```

## Governance

This technology-stack document is part of the project constitution.

Implementation decisions should remain consistent with this document.

Changes to the approved stack should be deliberate and connected to a
documented project requirement.

The implementation must not silently introduce major frameworks, data
stores, external services, or infrastructure that conflict with this
document.