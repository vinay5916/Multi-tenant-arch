# Aviation MAS-A2A System

A comprehensive Multi-Agent System (MAS-A2A) for aviation operations using Google ADK, FastMCP, and LiteLLM.

## Features

- **Multi-Agent Architecture**: Specialized agents for HR, meetings, and supply chain operations
- **Google ADK Integration**: Native ADK agent structure for robust agent management
- **FastMCP Tools**: High-performance MCP tool servers for specialized operations
- **LiteLLM Support**: Unified interface for multiple LLM providers
- **Aviation Focus**: Purpose-built for aviation industry operations

## Architecture

### Agents
- **Base Agent**: Core agent using Google ADK + LiteLLM
- **HR Agent**: Crew management, training, certifications
- **Meeting Agent**: Scheduling and coordination
- **Supply Chain Agent**: Inventory and procurement management

### MCP Servers
- **HR Tools**: Crew management, training schedules, certifications
- **Meeting Tools**: Calendar management, room booking, notifications
- **Supply Chain Tools**: Inventory tracking, purchase orders, vendor management

## Quick Start

### Prerequisites
- Python 3.12+
- uv package manager

### Installation

1. Clone the repository:
```bash
git clone &lt;repository-url&gt;
cd aviation-mas-a2a
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the System

1. Start the main application:
```bash
uv run python main.py
```

2. The system will start:
   - FastAPI server on http://localhost:8000
   - MCP servers on ports 8001-8003
   - Agent manager with all specialized agents

## API Endpoints

### Core Endpoints
- `GET /` - System information
- `GET /health` - Health check
- `GET /agents` - List all agents
- `POST /message` - Send message to agent
- `POST /broadcast` - Broadcast to all agents

### Agent Operations
- `GET /agents/{agent_type}/status` - Get agent status
- `POST /conversation` - Start multi-agent conversation

### MCP Tools
- `GET /mcp/tools` - List available MCP tools

## Configuration

Key configuration options in `src/aviation_mas_a2a/shared/config.py`:

```python
server_host = "0.0.0.0"
server_port = 8000
mcp_base_port = 8001
debug = True
```

## Development

### Project Structure
```
aviation-mas-a2a/
├── src/aviation_mas_a2a/
│   ├── agents/           # ADK agents
│   ├── mcp_servers/      # FastMCP tool servers
│   ├── shared/           # Shared configuration and utilities
│   └── app.py           # FastAPI application
├── main.py              # Application entry point
└── pyproject.toml       # Project configuration
```

### Adding New Agents

1. Create agent class in `src/aviation_mas_a2a/agents/`
2. Inherit from `BaseAgent`
3. Register in `AgentManager`

### Adding New MCP Tools

1. Create tool server in `src/aviation_mas_a2a/mcp_servers/`
2. Use FastMCP decorators
3. Register tools with the agent system

## Technologies

- **Google ADK**: Agent Development Kit
- **FastMCP**: Model Context Protocol implementation
- **LiteLLM**: LLM provider abstraction
- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **Loguru**: Logging
- **uv**: Package management

## License

[Add your license information here]

## Contributing

[Add contributing guidelines here]
