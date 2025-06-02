# Configuration Notes for CACM ADK System

## Alpha Vantage API Integration

The `DataRetrievalAgent` can optionally fetch live company overview and market data from Alpha Vantage. To enable this functionality:

1.  **Obtain an API Key**: Get a free API key from [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key).
2.  **Set Environment Variable**: For the most secure and standard approach, set the API key as an environment variable named `ALPHA_VANTAGE_API_KEY`.
    ```bash
    export ALPHA_VANTAGE_API_KEY="YOUR_ACTUAL_API_KEY"
    ```
    (For Windows, use `set ALPHA_VANTAGE_API_KEY="YOUR_ACTUAL_API_KEY"` in Command Prompt or add it to System Environment Variables).
3.  **Alternative (Agent Config - Less Secure for Keys)**: The API key can also be passed via the `agent_config` dictionary when `DataRetrievalAgent` is initialized by the Orchestrator, or as `api_key` in `current_step_inputs` during a `run` call if the `api_source` is set to "AlphaVantage". However, using environment variables is recommended for sensitive keys.

If the API key is not configured or an API call fails, the `DataRetrievalAgent` will fall back to its mock data providers.
