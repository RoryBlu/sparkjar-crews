# Requirements Document

## Introduction

The Memory Maker Crew and Memory Service have a critical interface mismatch that prevents the crew from creating memories. The crew expects an `upsert_entity` action that exists in the Memory Service API but is not exposed through the memory tool wrapper. This integration aims to provide an intelligent upsert capability that not only aligns interfaces but also introduces memory consolidation - analyzing the entire memory graph within a contextual realm to optimize storage, update statistics, and create meaningful associations similar to human memory consolidation.

## Requirements

### Requirement 1

**User Story:** As a memory maker crew agent, I want to use an intelligent `upsert_entity` action that analyzes the memory graph before adding information, so that memories remain consolidated and don't bloat the database with redundant data.

#### Acceptance Criteria

1. WHEN the crew calls `upsert_entity` action THEN the memory tool SHALL load the entire memory graph for the contextual realm
2. WHEN analyzing the memory graph THEN the system SHALL identify statistics to update, observations to merge, and relationships to create
3. WHEN an entity doesn't exist THEN the system SHALL create a new entity with the provided observations
4. WHEN an entity already exists THEN the system SHALL intelligently consolidate new information rather than blindly appending
5. WHEN updating statistics THEN the system SHALL replace the value rather than creating duplicate observations
6. WHEN the upsert completes THEN the tool SHALL return the consolidated entity state

### Requirement 2

**User Story:** As a developer, I want the memory tool interface to match what the crew configuration expects, so that the system works without manual intervention or workarounds.

#### Acceptance Criteria

1. WHEN examining the tool's action list THEN `upsert_entity` SHALL be included as a supported action
2. WHEN calling `upsert_entity` THEN the parameters SHALL match the crew's expected format: `name`, `entity_type`, `observations`, and `metadata`
3. WHEN the tool description is generated THEN it SHALL include clear documentation for the `upsert_entity` action
4. WHEN validation occurs THEN the tool SHALL validate all required parameters according to the memory service API schema

### Requirement 3

**User Story:** As a system architect, I want the memory tool to implement intelligent consolidation patterns from the start, so that the system is designed for optimal memory management.

#### Acceptance Criteria

1. WHEN the tool is initialized THEN consolidation features SHALL be enabled by default
2. WHEN memory graph loading fails THEN the system SHALL provide clear error messages
3. WHEN sequential thinking is unavailable THEN the system SHALL fallback to basic upsert
4. WHEN the tool is used hierarchically THEN the `upsert_entity` action SHALL respect hierarchical context settings

### Requirement 4

**User Story:** As a QA engineer, I want comprehensive testing of the memory tool integration, so that I can verify the upsert functionality works correctly in all scenarios.

#### Acceptance Criteria

1. WHEN unit tests run THEN they SHALL cover the new `upsert_entity` action with at least 90% code coverage
2. WHEN integration tests run THEN they SHALL verify end-to-end upsert functionality with the memory service
3. WHEN testing edge cases THEN tests SHALL cover entity creation, updates, validation errors, and service failures
4. WHEN testing with the Vervelyn policy THEN the system SHALL successfully create all expected memory entities

### Requirement 5

**User Story:** As a memory service maintainer, I want the tool to properly handle all response formats and error conditions from the upsert endpoint, so that the system gracefully handles all scenarios.

#### Acceptance Criteria

1. WHEN the memory service returns a successful response THEN the tool SHALL parse and return the entity data correctly
2. WHEN the memory service returns validation errors THEN the tool SHALL provide clear error messages to the crew
3. WHEN the memory service is unavailable THEN the tool SHALL implement retry logic with exponential backoff
4. WHEN rate limits are hit THEN the tool SHALL handle 429 responses appropriately

### Requirement 6

**User Story:** As a crew developer, I want clear documentation and examples of using the upsert functionality, so that I can create new crews that leverage this capability.

#### Acceptance Criteria

1. WHEN reviewing tool documentation THEN examples SHALL show how to use `upsert_entity` for different entity types
2. WHEN examining the crew configuration THEN the tasks.yaml SHALL have accurate examples of the upsert action
3. WHEN troubleshooting THEN error messages SHALL clearly indicate what parameters are missing or invalid
4. WHEN learning the tool THEN the description SHALL explain when to use upsert vs create actions

### Requirement 7

**User Story:** As a system operator, I want the memory tool to properly log all upsert operations, so that I can monitor and debug memory creation workflows.

#### Acceptance Criteria

1. WHEN an upsert operation starts THEN the tool SHALL log the entity name and type being processed
2. WHEN an upsert succeeds THEN the tool SHALL log the number of observations added or updated
3. WHEN an upsert fails THEN the tool SHALL log the error details without exposing sensitive content
4. WHEN debugging is enabled THEN the tool SHALL log the full request and response payloads

### Requirement 8

**User Story:** As a performance engineer, I want the upsert operation to be efficient and not create duplicate API calls, so that the system performs well under load.

#### Acceptance Criteria

1. WHEN upserting an entity THEN the tool SHALL make exactly one API call to the memory service
2. WHEN processing multiple observations THEN they SHALL be batched in a single upsert request
3. WHEN caching is available THEN the tool SHALL use appropriate caching strategies for entity lookups
4. WHEN monitoring performance THEN upsert operations SHALL complete within 2 seconds for typical entity sizes

### Requirement 9

**User Story:** As a memory system architect, I want the upsert process to maintain strict contextual realm isolation while performing intelligent consolidation, so that memories never leak across client boundaries.

#### Acceptance Criteria

1. WHEN loading the memory graph THEN the system SHALL only access memories within the current contextual realm
2. WHEN consolidating memories THEN no information SHALL cross realm boundaries (client to client, synth to synth, etc.)
3. WHEN using sequential thinking THEN the analysis SHALL be scoped to the specific realm
4. WHEN errors occur THEN the system SHALL never expose information from other realms

### Requirement 10

**User Story:** As a data scientist, I want the memory consolidation to use sequential thinking for intelligent analysis, so that the system can identify patterns and optimize memory storage like human cognition.

#### Acceptance Criteria

1. WHEN sequential thinking is enabled THEN the system SHALL analyze the memory graph before consolidation
2. WHEN identifying statistics THEN the system SHALL recognize numeric patterns like "performance: X%"
3. WHEN merging observations THEN the system SHALL combine semantically similar content
4. WHEN creating relationships THEN the system SHALL detect implicit connections in the data
5. WHEN consolidation fails THEN the system SHALL fallback to standard upsert behavior