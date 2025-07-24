# Design Document

## Introduction

This design document outlines the technical approach for implementing an intelligent `upsert_entity` action in the memory tool. The Memory Maker Crew expects this action to create memories with built-in consolidation capabilities that analyze the entire memory graph within a contextual realm to optimize storage, update statistics, and create meaningful associations - similar to how human memory consolidates information during sleep.

## System Architecture

### Current State

```
Memory Maker Crew
    |
    v
SJMemoryToolHierarchical (missing upsert_entity)
    |
    v
Memory Service API (has /memory/entities/upsert endpoint)
```

### Target State

```
Memory Maker Crew (with LLM reasoning)
    |
    v
SJMemoryToolHierarchical (with intelligent upsert_entity)
    |
    +-- Sequential Thinking Service (memory graph analysis)
    |
    +-- Memory Graph Analyzer (consolidation logic)
    |
    v
Memory Service API (/memory/entities/upsert endpoint)
```

## Data Flow

### Intelligent Upsert Entity Flow

1. **Crew Request**: The Memory Maker Crew sends a request with action `upsert_entity`
2. **Memory Graph Analysis**: Tool fetches the entire memory graph for the contextual realm
3. **Sequential Thinking**: Analyzes existing memories to identify:
   - Related entities and observations
   - Consolidation opportunities
   - Statistics to update
   - Redundant information to merge
4. **Intelligent Processing**: 
   - Consolidates similar observations
   - Updates statistical values instead of adding duplicates
   - Creates new relationships between entities
   - Transforms data for optimal storage
5. **Optimized API Call**: Sends consolidated upsert request to `/memory/entities/upsert`
6. **Result Return**: Returns the intelligently processed memory state

## Memory Consolidation Design

### Core Principles

1. **Contextual Realm Isolation**: Each upsert operates strictly within its contextual realm (client, synth_class, skill_module, or synth) with no cross-realm contamination.

2. **Graph-Aware Processing**: Before adding new information, the system analyzes the entire memory graph within the realm to understand existing knowledge structure.

3. **Intelligent Consolidation**: Similar to human memory consolidation during sleep, the system:
   - Merges redundant observations
   - Updates statistics rather than duplicating
   - Strengthens important connections
   - Prunes outdated information

### Memory Graph Analysis

The upsert process begins by loading the contextual realm's memory graph:

```python
# Load entire memory graph for the contextual realm
memory_graph = await self._load_memory_graph(
    client_id=self.client_id,
    actor_type=self.actor_type,
    actor_id=self.actor_id
)

# Analyze using sequential thinking
analysis = await sequential_thinking.analyze_memory_graph(
    graph=memory_graph,
    new_data=params["observations"],
    consolidation_strategy="intelligent"
)
```

### Consolidation Strategies

1. **Statistical Update**: When new observation contains metrics
   ```python
   # Instead of: "Blog performance: 85% engagement"
   # Update existing: "Blog performance: {value}%" → "Blog performance: 85%"
   ```

2. **Observation Merging**: Combine similar observations
   ```python
   # Existing: "Use clear headings for SEO"
   # New: "Headers should be descriptive for search"
   # Merged: "Use clear, descriptive headings for SEO optimization"
   ```

3. **Relationship Enhancement**: Strengthen entity connections
   ```python
   # Detect implicit relationships in new content
   # Create explicit relationship entities
   ```

4. **Redundancy Elimination**: Remove duplicate information
   ```python
   # Identify semantically similar observations
   # Keep the most comprehensive version
   ```

### Request Format

```python
{
    "action": "upsert_entity",
    "params": {
        "name": "synth_disclosure_policy",
        "entity_type": "policy",
        "observations": [
            {
                "observation": "When a synthetic human is the author...",
                "observation_type": "policy_statement",
                "metadata": {
                    "source": "Vervelyn Corporate Policy",
                    "importance": "high"
                }
            }
        ],
        "metadata": {
            "created_by": "memory_maker_crew",
            "version": "1.0"
        }
    }
}
```

### API Request Mapping

The tool will map the crew's request to the Memory Service API format:

```python
{
    "client_id": self.client_id,  # From tool context
    "actor_type": self.actor_type,  # From tool context
    "actor_id": self.actor_id,      # From tool context
    "entity": {
        "name": params["name"],
        "entity_type": params["entity_type"],
        "metadata": params.get("metadata", {})
    },
    "observations": params.get("observations", [])
}
```

## Implementation Details

### File Structure

```
/tools/
  sj_memory_tool_hierarchical.py  # Main tool implementation
  
/tests/
  test_memory_tool_hierarchical.py  # Unit tests
  
/crews/memory_maker_crew/
  tasks.yaml  # Already configured for upsert_entity
```

### Code Changes

#### 1. Add Intelligent Upsert Entity Action

Location: `tools/sj_memory_tool_hierarchical.py`

```python
async def _handle_upsert_entity(self, params: Dict[str, Any]) -> str:
    """Handle intelligent upsert_entity with memory consolidation."""
    try:
        # Validate required parameters
        required = ["name", "entity_type"]
        self._validate_params(params, required)
        
        # Load memory graph for contextual realm
        memory_graph = await self._load_realm_memory_graph()
        
        # Analyze with sequential thinking if available
        if self.enable_consolidation and hasattr(self, 'thinking_client'):
            consolidation_result = await self._analyze_for_consolidation(
                memory_graph, 
                params
            )
            
            # Apply consolidation strategies
            if consolidation_result.should_consolidate:
                params = await self._apply_consolidation(
                    params, 
                    consolidation_result
                )
        
        # Construct optimized API request
        payload = self._build_upsert_payload(params)
        
        # Make API call
        response = await self._make_request(
            "POST",
            "/memory/entities/upsert",
            json=payload
        )
        
        return self._format_entity_response(response)
        
    except Exception as e:
        return f"Error upserting entity: {str(e)}"

async def _load_realm_memory_graph(self) -> Dict[str, Any]:
    """Load all memories within the contextual realm."""
    # Fetch all entities for this actor
    entities = await self._make_request(
        "GET",
        f"/memory/entities",
        params={
            "client_id": self.client_id,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "include_observations": True,
            "include_relationships": True
        }
    )
    
    return self._build_graph_structure(entities)

async def _analyze_for_consolidation(
    self, 
    memory_graph: Dict[str, Any],
    new_params: Dict[str, Any]
) -> ConsolidationResult:
    """Use sequential thinking to analyze consolidation opportunities."""
    
    thinking_prompt = f"""
    Analyze this memory graph and new observations for consolidation:
    
    Existing Memory Graph:
    {json.dumps(memory_graph, indent=2)}
    
    New Data to Add:
    {json.dumps(new_params, indent=2)}
    
    Identify:
    1. Statistics that should be updated (not duplicated)
    2. Similar observations that can be merged
    3. New relationships to create
    4. Redundant information to remove
    
    Return a consolidation strategy.
    """
    
    result = await self.thinking_client.create_thought(
        session_id=f"consolidation_{self.actor_id}",
        content=thinking_prompt,
        thought_type="memory_consolidation"
    )
    
    return self._parse_consolidation_result(result)

async def _apply_consolidation(
    self,
    params: Dict[str, Any],
    consolidation: ConsolidationResult
) -> Dict[str, Any]:
    """Apply the consolidation strategy to optimize the upsert."""
    
    # Update statistics instead of adding new observations
    if consolidation.statistics_to_update:
        params = self._update_statistics(params, consolidation)
    
    # Merge similar observations
    if consolidation.observations_to_merge:
        params = self._merge_observations(params, consolidation)
    
    # Add relationship creation
    if consolidation.relationships_to_create:
        params["create_relationships"] = consolidation.relationships_to_create
    
    return params
```

#### 2. Add Memory Graph Builder

```python
def _build_graph_structure(self, entities: List[Dict]) -> Dict[str, Any]:
    """Build a graph representation of the memory realm."""
    graph = {
        "entities": {},
        "relationships": [],
        "statistics": {},
        "observation_clusters": {}
    }
    
    for entity in entities:
        # Index by entity name for quick lookup
        graph["entities"][entity["name"]] = entity
        
        # Extract statistics from observations
        for obs in entity.get("observations", []):
            if self._is_statistical_observation(obs):
                graph["statistics"][entity["name"]] = obs
        
        # Group similar observations
        self._cluster_observations(graph, entity)
    
    return graph
```

#### 3. Update Tool Description

```python
def _get_enhanced_description(self) -> str:
    base_desc = super()._get_enhanced_description()
    upsert_desc = """
    - upsert_entity: {"action": "upsert_entity", "params": {"name": "policy_name", "entity_type": "policy", "observations": [{"observation": "content", "observation_type": "type"}], "metadata": {}}}
      Intelligently creates or updates entities with memory consolidation:
      * Analyzes existing memory graph in the contextual realm
      * Updates statistics rather than duplicating
      * Merges similar observations
      * Creates meaningful relationships
      * Maintains optimal memory size
    """
    return base_desc + upsert_desc
```

#### 4. Add Configuration Options

```python
class HierarchicalMemoryConfig(BaseModel):
    # ... existing config ...
    
    # Memory consolidation settings
    enable_consolidation: bool = Field(
        default=True,
        description="Enable intelligent memory consolidation during upsert"
    )
    consolidation_threshold: float = Field(
        default=0.8,
        description="Similarity threshold for merging observations (0-1)"
    )
    max_graph_size: int = Field(
        default=1000,
        description="Maximum entities to load for graph analysis"
    )
    use_sequential_thinking: bool = Field(
        default=True,
        description="Use sequential thinking service for analysis"
    )
        self._validate_params(params, required)
        
        # Construct API request
        payload = {
            "client_id": self.client_id,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "entity": {
                "name": params["name"],
                "entity_type": params["entity_type"],
                "metadata": params.get("metadata", {})
            },
            "observations": params.get("observations", [])
        }
        
        # Make API call
        response = await self._make_request(
            "POST",
            "/memory/entities/upsert",
            json=payload
        )
        
        # Format response
        return self._format_entity_response(response)
        
    except Exception as e:
        return f"Error upserting entity: {str(e)}"
```

#### 2. Update Action Registry

```python
self.actions = {
    "create_entity": self._handle_create_entity,
    "upsert_entity": self._handle_upsert_entity,  # New action
    "add_observation": self._handle_add_observation,
    # ... other actions
}
```

#### 3. Update Tool Description

```python
def _get_enhanced_description(self) -> str:
    base_desc = super()._get_enhanced_description()
    upsert_desc = """
    - upsert_entity: {"action": "upsert_entity", "params": {"name": "policy_name", "entity_type": "policy", "observations": [{"observation": "content", "observation_type": "type"}], "metadata": {}}}
      Creates new entity or updates existing one with new observations
    """
    return base_desc + upsert_desc
```

### Error Handling

The implementation will include comprehensive error handling:

1. **Parameter Validation**: Check for required fields before API call
2. **API Errors**: Handle 400, 401, 404, 429, 500 responses appropriately
3. **Network Errors**: Implement retry logic with exponential backoff
4. **Response Validation**: Ensure API response contains expected fields

### Testing Strategy

#### Unit Tests

1. **Test Parameter Validation**
   - Missing required parameters
   - Invalid parameter types
   - Empty observations array

2. **Test API Integration**
   - Successful entity creation
   - Successful entity update
   - API error responses
   - Network failures

3. **Test Response Formatting**
   - Complete entity response
   - Partial response handling
   - Error message formatting

#### Integration Tests

1. **End-to-End Upsert Flow**
   - Create new entity with observations
   - Update existing entity with new observations
   - Verify entity state after upsert

2. **Crew Integration Test**
   - Run Memory Maker Crew with Vervelyn policy
   - Verify all expected entities are created
   - Check observation content and metadata

### Performance Considerations

1. **Request Batching**: The upsert endpoint accepts multiple observations in a single request
2. **Response Caching**: Consider caching entity lookups for read operations
3. **Connection Pooling**: Reuse HTTP connections for multiple requests
4. **Timeout Configuration**: Set appropriate timeouts for large observation sets

## Migration Strategy

Since this is adding new functionality without changing existing behavior:

1. **Phase 1**: Implement and test `upsert_entity` action
2. **Phase 2**: Deploy updated tool to development environment
3. **Phase 3**: Run Memory Maker Crew tests with new functionality
4. **Phase 4**: Deploy to production after validation

No data migration is required as this only adds new functionality.

## Security Considerations

1. **Authentication**: Continue using existing JWT token authentication
2. **Authorization**: Respect actor context for all upsert operations
3. **Input Sanitization**: Validate and sanitize all user inputs
4. **Audit Logging**: Log all upsert operations for compliance

## Monitoring and Observability

1. **Metrics**:
   - Upsert operation count
   - Success/failure rates
   - Response times
   - Entity creation vs update ratio

2. **Logging**:
   - Operation start/end with entity details
   - Error conditions with context
   - Performance warnings for slow operations

3. **Alerts**:
   - High failure rate for upsert operations
   - Unusual spike in entity creation
   - Memory service availability issues