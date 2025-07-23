# KIRO Methodology

## Introduction

KIRO is a specification methodology designed to ensure clear, testable, and implementable software requirements. It emphasizes structured documentation with clear introductions, hierarchical requirements, user stories, and EARS-formatted acceptance criteria.

## Directory Structure

```
.kiro/
├── README.md                    # This file
└── specs/                       # All project specifications
    ├── ingest_book_prod/       # Book ingestion crew specs
    │   ├── analysis.md         # Current state analysis
    │   ├── requirements.md     # Formal requirements
    │   └── tasks.md           # Implementation tasks
    ├── book-ingestion-improvement/
    ├── book-ingestion-crew-enhancement/
    └── memory-maker-crew-production-ready/
```

## KIRO Format Guidelines

### 1. Clear Introduction

Every specification must begin with a clear introduction that:
- States the purpose of the component
- Provides context for why it's needed
- Summarizes key capabilities
- Sets expectations for the reader

Example:
```markdown
## Introduction

This specification defines the requirements for a production-ready book ingestion crew 
that processes handwritten manuscript images from Google Drive, performs OCR using 
GPT-4o, and stores the transcribed text in a PostgreSQL database. The system must 
follow CrewAI standards and the KISS principle for maintainable, reliable operation.
```

### 2. Hierarchical Numbered Requirements

Requirements must be:
- Numbered hierarchically (Requirement 1, 1.1, 1.2, etc.)
- Grouped by functional area
- Written in clear, testable language
- Independent and atomic

Example:
```markdown
### Requirement 1: Google Drive Processing

### Requirement 2: OCR Quality

### Requirement 3: Database Storage
```

### 3. User Story Format

Each requirement must include a user story following the format:
```
As a [role], I want [feature], so that [benefit].
```

Example:
```markdown
**User Story:** As a content manager, I want to process manuscript images from 
Google Drive, so that I can digitize handwritten books into searchable text format.
```

### 4. EARS-Formatted Acceptance Criteria

EARS (Easy Approach to Requirements Syntax) format ensures testable criteria:
- **WHEN** [trigger] **THEN** [system response]
- Use SHALL for mandatory requirements
- Number each criterion
- Make them specific and measurable

Example:
```markdown
#### Acceptance Criteria

1. WHEN a Google Drive folder URL is provided THEN the system SHALL list all image files
2. WHEN processing begins THEN the system SHALL download files one at a time sequentially
3. WHEN an image is downloaded THEN the system SHALL support PNG, JPG, JPEG formats
4. WHEN processing completes THEN the system SHALL store pages in BookIngestions table
```

## Creating a New Specification

1. **Create directory**: `.kiro/specs/your-feature-name/`

2. **Create requirements.md** with this template:
```markdown
# Requirements Document

## Introduction
[Clear introduction explaining the feature/component]

## Requirements

### Requirement 1
**User Story:** As a [role], I want [feature], so that [benefit].

#### Acceptance Criteria
1. WHEN [trigger] THEN the system SHALL [response]
2. WHEN [condition] THEN the system SHALL [behavior]

### Requirement 2
[Continue pattern...]
```

3. **Create analysis.md** for current state analysis:
```markdown
# Current State Analysis

## Overview
[Summary of current implementation]

## Issues Found
[List of problems/gaps]

## What's Working
[Existing functionality that works]

## Next Steps Required
[Actions needed to meet requirements]
```

4. **Create tasks.md** for implementation planning:
```markdown
# Implementation Tasks

## Phase 1: Foundation
- [ ] Task 1 description
- [ ] Task 2 description

## Phase 2: Core Features
- [ ] Task 3 description
- [ ] Task 4 description

## Phase 3: Testing & Polish
- [ ] Task 5 description
```

## Benefits of KIRO

1. **Clarity**: Clear structure makes requirements easy to understand
2. **Testability**: EARS format creates directly testable criteria
3. **Traceability**: User stories link features to business value
4. **Completeness**: Structured format helps identify missing requirements
5. **Communication**: Standard format improves team communication

## Examples in This Project

- **Book Ingestion Crew**: See `.kiro/specs/ingest_book_prod/` for a complete example
- **Memory Maker Crew**: See `.kiro/specs/memory-maker-crew-production-ready/`

## Best Practices

1. **Keep it simple**: Don't over-specify; focus on what matters
2. **Be specific**: Vague requirements lead to implementation confusion
3. **Think testing**: If you can't test it, rewrite it
4. **User focus**: Always tie requirements back to user needs
5. **Iterate**: Requirements evolve; update specs as you learn

## Tools and Integration

KIRO specifications can be:
- Tracked in version control alongside code
- Linked to issue tracking systems
- Used to generate test cases
- Referenced in code reviews
- Included in deployment checklists