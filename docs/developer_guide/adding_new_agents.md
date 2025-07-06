# Adding New Agents

This guide outlines the process for adding new agents to the system. Agents are fundamental components responsible for specific tasks and capabilities.

## Key Considerations

*   **Purpose and Scope:** Clearly define the agent's responsibility. What specific problem will it solve?
*   **Interaction Patterns:** How will this agent interact with other agents or system components? (e.g., via Orchestrator, direct calls, shared context).
*   **Skills:** What Semantic Kernel skills or native Python functions will this agent utilize?
*   **Configuration:** What configuration parameters will the agent require? How will these be managed?
*   **Data Handling:** How will the agent manage input and output data?
*   **Ontology Alignment:** If the agent interacts with the Knowledge Graph, ensure its operations are aligned with the existing ontology.

## Steps to Add a New Agent

1.  **Define the Agent Class:**
    *   Create a new Python file in the `adk/agents/` directory (e.g., `my_new_agent.py`).
    *   Define the agent class, typically inheriting from a base agent class if one exists (e.g., `BaseAgent`).
    *   Implement the agent's core logic within its methods.

2.  **Register with Orchestrator (if applicable):**
    *   If the agent needs to be managed or discovered by the Orchestrator, ensure it's registered appropriately. This might involve updating Orchestrator configuration or registration mechanisms.

3.  **Implement Necessary Skills:**
    *   If the agent requires new Semantic Kernel skills, follow the guide for [Adding Semantic Kernel Skills](./adding_semantic_kernel_skills.md).

4.  **Add Configuration:**
    *   Define any necessary configuration parameters in the relevant configuration files (e.g., `config/agents.yaml` or similar).

5.  **Write Unit Tests:**
    *   Create unit tests for the new agent in the `tests/agents/` directory (e.g., `test_my_new_agent.py`).
    *   Ensure tests cover the agent's core functionality and interaction patterns.

6.  **Update Documentation:**
    *   Add a section to the main project documentation detailing the new agent's purpose, capabilities, and configuration.
    *   Consider adding an `AGENTS.md` file in the agent's specific directory if it has unique conventions.

## Example (Conceptual)

```python
# adk/agents/example_processing_agent.py
from adk.agents.base_agent import BaseAgent # Assuming a base agent class

class ExampleProcessingAgent(BaseAgent):
    def __init__(self, agent_id, config, orchestrator):
        super().__init__(agent_id, config, orchestrator)
        # Initialize agent-specific attributes

    async def process_data(self, data):
        # Agent's core logic to process data
        self.logger.info(f"Processing data: {data}")
        # ... utilize skills, interact with other agents, etc.
        processed_data = {"status": "processed", "original_data": data}
        return processed_data

    async def another_capability(self, params):
        # Another distinct capability of this agent
        pass
```

## Best Practices

*   **Single Responsibility Principle:** Aim for agents that have a clear and focused purpose.
*   **Modularity:** Design agents to be as modular and reusable as possible.
*   **Testability:** Write agents with testability in mind.
*   **Clear Logging:** Implement comprehensive logging for easier debugging and monitoring.
```
