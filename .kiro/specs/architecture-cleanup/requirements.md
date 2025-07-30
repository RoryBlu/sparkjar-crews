# Architecture Cleanup Requirements

## Introduction

The SparkJAR platform underwent a monorepo split that was partially completed. This has resulted in code duplication, confusion about where components belong, and a mismatch between the intended architecture and current reality. This document outlines the requirements for completing the architecture cleanup.

## Current State Problems

### Problem 1: Duplicate Crew Locations

**User Story:** As a developer, I need to know definitively where each crew belongs so I can make changes in the correct location without confusion or duplication.

#### Current Issues
- Crews exist in TWO places:
  - `_reorg/sparkjar-crew-api/src/crews/` (multiple crews including book_translation_crew)
  - `_reorg/sparkjar-crews/crews/` (production crews from the split)
- No clear guidance on which location is authoritative
- Risk of divergent implementations

### Problem 2: Incomplete Monorepo Split

**User Story:** As a platform architect, I need the monorepo split completed so that services can be deployed and scaled independently.

#### Current Issues
- MONOREPO_SPLIT_COMPLETE.md shows intended architecture but reality differs
- Some crews never migrated to the dedicated crews service
- Database connections still tightly coupled to API service
- Inter-service communication not implemented

### Problem 3: Inconsistent Documentation

**User Story:** As a new developer, I need accurate documentation that reflects the actual system architecture so I can understand how components interact.

#### Current Issues
- README files contradict each other about model names (gpt-4.1 vs gpt-4o)
- No single source of truth for architecture
- Discovery process required to understand system structure
- CLAUDE.md says gpt-4.1 models exist, other docs say they don't

## Requirements

### Requirement 0: Clean Up Root Repository Chaos

**User Story:** As a developer, I need a clean, organized repository structure without random scripts scattered everywhere so I can find what I need without archaeological excavation.

#### Current Issues
- Root directory littered with test scripts (test_*.py files)
- Random execution scripts (run_*.py, execute_*.py, resume_*.py)
- Multiple baron-related files with no clear purpose
- Configuration files mixed with test files mixed with utilities
- No clear organization or naming convention

**Acceptance Criteria:**
1. WHEN a developer looks at the root directory THEN they SHALL see only essential files (README, setup.py, requirements.txt, etc.)
2. WHEN test scripts are needed THEN they SHALL be in appropriate tests/ directories
3. WHEN utility scripts exist THEN they SHALL be in scripts/ or utils/ directories
4. WHEN temporary or experimental files exist THEN they SHALL be in sandbox/ or removed
5. WHEN configuration files exist THEN they SHALL be in config/ directories

### Requirement 1: Single Location for Each Crew

**Acceptance Criteria:**
1. WHEN a developer looks for a crew THEN there SHALL be exactly one location where it exists
2. WHEN new crews are created THEN they SHALL go in the designated crews repository
3. WHEN the API needs to execute a crew THEN it SHALL communicate via defined service interfaces
4. WHEN crews need database access THEN they SHALL use sparkjar-shared connections

### Requirement 2: Complete Service Separation

**Acceptance Criteria:**
1. WHEN sparkjar-crew-api is deployed THEN it SHALL NOT contain crew implementations
2. WHEN sparkjar-crews is deployed THEN it SHALL be independently scalable
3. WHEN services communicate THEN they SHALL use HTTP/gRPC interfaces, not direct imports
4. WHEN a service fails THEN other services SHALL continue operating

### Requirement 3: Unified Architecture Documentation

**Acceptance Criteria:**
1. WHEN a developer joins the project THEN they SHALL find a single ARCHITECTURE.md explaining the system
2. WHEN documentation conflicts exist THEN they SHALL be resolved with a single source of truth
3. WHEN the architecture is documented THEN it SHALL include:
   - Service boundaries and responsibilities
   - Communication patterns between services
   - Data flow and storage patterns
   - Deployment architecture

### Requirement 4: Model Name Consistency

**Acceptance Criteria:**
1. WHEN configuring LLM models THEN there SHALL be consistent naming across all services
2. WHEN documentation references models THEN it SHALL use the correct names
3. WHEN CLAUDE.md and other docs conflict THEN there SHALL be a resolution
4. WHEN new models are added THEN they SHALL be documented in a central location

### Requirement 5: Migration Path Safety

**Acceptance Criteria:**
1. WHEN migrating crews THEN production SHALL NOT be disrupted
2. WHEN moving code THEN there SHALL be a rollback plan
3. WHEN updating imports THEN all dependent code SHALL be updated atomically
4. WHEN deploying changes THEN they SHALL be tested in staging first

## Success Criteria

The architecture cleanup will be considered complete when:

1. **No Duplicate Code**: Each crew exists in exactly one location
2. **Clear Boundaries**: Services have well-defined responsibilities
3. **Independent Operation**: Services can be deployed and scaled separately
4. **Consistent Documentation**: Single source of truth for architecture
5. **Production Stability**: No disruption to existing deployments
6. **Developer Clarity**: New developers can understand the system in < 30 minutes

## Constraints

1. **Backwards Compatibility**: Existing API contracts must be maintained
2. **Zero Downtime**: Migration must not cause service interruptions
3. **Railway Compatibility**: Changes must work with current Railway deployment
4. **Authentication Preservation**: JWT token validation must continue working
5. **Database Integrity**: No data loss during migration

## Dependencies

1. **sparkjar-shared**: Must be properly configured for all services
2. **Railway Environment**: Must support multi-repo deployments
3. **Testing Infrastructure**: Must be updated for new architecture
4. **CI/CD Pipelines**: Must be created for each repository

## Timeline Expectations

- **Phase 1** (1 week): Document current state and create migration plan
- **Phase 2** (2 weeks): Implement inter-service communication
- **Phase 3** (2 weeks): Migrate crews to dedicated service
- **Phase 4** (1 week): Update documentation and testing
- **Phase 5** (1 week): Production deployment and monitoring