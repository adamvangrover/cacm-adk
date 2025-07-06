# Agent-to-Agent Communication Patterns

Effective communication between agents is crucial for building complex, multi-agent systems. This document outlines the primary patterns for agent-to-agent (A2A) communication currently employed or envisioned in this project.

## 1. Orchestrator-Mediated Communication

*   **Description:** The Orchestrator acts as a central hub or registry for agents. Agents can request instances of other agents from the Orchestrator and then invoke their methods directly.
*   **Mechanism:**
    1.  Agent A needs to interact with Agent B.
    2.  Agent A requests an instance of Agent B from the Orchestrator (e.g., `orchestrator.get_or_create_agent_instance("AgentB_ID", AgentBClass, agent_b_config)`).
    3.  The Orchestrator returns a reference/instance of Agent B.
    4.  Agent A can now call public methods on the Agent B instance (e.g., `await agent_b_instance.perform_task(data)`).
*   **Pros:**
    *   Centralized agent management and discovery.
    *   Orchestrator can manage agent lifecycles, configuration, and potentially load balancing or scaling (in more advanced scenarios).
    *   Decouples agents to some extent, as they don't need to know the exact instantiation details of others.
*   **Cons:**
    *   The Orchestrator can become a bottleneck if not designed carefully.
    *   Introduces a dependency on the Orchestrator for all such interactions.
    *   Primarily supports synchronous request/response patterns unless method calls are designed to be asynchronous and non-blocking.
*   **When to Use:**
    *   When an agent needs to directly invoke a specific capability of another known agent.
    *   When agent lifecycle and instance management are important.

## 2. Shared Context / Data Store

*   **Description:** Agents communicate indirectly by reading from and writing to a shared context object or an external data store (e.g., a shared dictionary, a database, a knowledge graph, or a message bus acting as a blackboard).
*   **Mechanism:**
    1.  Agent A performs a task and writes its output or status to a predefined location in the `SharedContext` (e.g., `shared_context.update_data("task_A_output", result)`).
    2.  Agent B, which depends on the output of Agent A, monitors the `SharedContext` or is triggered when specific data becomes available.
    3.  Agent B reads the data from the `SharedContext` (e.g., `data = shared_context.get_data("task_A_output")`) and proceeds with its task.
*   **Pros:**
    *   Highly decoupled communication; agents don't need direct references to each other.
    *   Excellent for asynchronous workflows and event-driven architectures.
    *   Can support complex data sharing and state management.
*   **Cons:**
    *   Requires careful design of the shared data structures and access protocols.
    *   Potential for race conditions or data inconsistencies if not managed properly (e.g., using locks or transactional updates for critical data).
    *   Discoverability of data and "contracts" for shared data can be challenging to manage.
*   **When to Use:**
    *   For asynchronous task handoffs.
    *   When multiple agents need to access or contribute to a shared piece of information or state.
    *   In event-driven systems where agents react to changes in data.

## 3. Direct Method Calls (Within a Composite Agent or Tightly Coupled System)

*   **Description:** This pattern applies when multiple "agents" or components are part of a larger, composite agent or are so tightly coupled that direct object references are managed internally. This is less "A2A" in a distributed sense and more about internal component interaction.
*   **Mechanism:**
    1.  A primary agent or controller instantiates and holds references to sub-agents or helper components.
    2.  The primary agent directly calls methods on these components.
*   **Pros:**
    *   Simple and efficient for tightly integrated components.
    *   Low overhead.
*   **Cons:**
    *   High coupling. Changes in one component can directly impact others.
    *   Not suitable for distributed or independently deployable agents.
*   **When to Use:**
    *   For internal logic decomposition within a single, complex agent.
    *   When components are inherently part of the same lifecycle and trust boundary.

## 4. Message Queues / Event Bus (Special case of Shared Data Store for Events)

*   **Description:** Agents publish messages (events or commands) to a message queue or event bus, and other interested agents subscribe to these messages.
*   **Mechanism:**
    1.  Agent A produces an event (e.g., "DataProcessedEvent") and publishes it to a specific topic or queue on a message bus (e.g., RabbitMQ, Kafka, Redis Streams).
    2.  Agent B (and any other interested agents) subscribes to that topic/queue.
    3.  The message bus delivers the event to Agent B, which then processes it.
*   **Pros:**
    *   Excellent for asynchronous, event-driven architectures.
    *   Strong decoupling: producers and consumers don't need to know about each other.
    *   Supports broadcasting events to multiple consumers.
    *   Can provide resilience (message persistence) and load balancing.
*   **Cons:**
    *   Introduces an external dependency on the message bus infrastructure.
    *   Requires defining message formats/schemas.
    *   Debugging can be more complex as control flow is not direct.
*   **When to Use:**
    *   For broadcasting events or notifications.
    *   When tasks can be processed asynchronously and independently.
    *   To integrate disparate parts of the system or connect to external systems.

## Choosing the Right Pattern

The choice of communication pattern depends on:

*   **Coupling:** How tightly should agents be coupled?
*   **Synchronicity:** Does the interaction need to be synchronous (caller waits for response) or asynchronous (caller continues, response handled later)?
*   **Complexity of Interaction:** Is it a simple request/response, or a more complex data exchange or workflow?
*   **Scalability and Reliability Needs:** Are there requirements for message persistence, retries, or distributing load?
*   **System Architecture:** What is the overall architecture (e.g., monolithic, microservices, event-driven)?

It's common for a system to use a combination of these patterns for different types of interactions. The `docs/developer_guide/README.md` should be updated to include a link to this file.
```
