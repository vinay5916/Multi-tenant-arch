# Aviation Multi-Agent System - MAS-A2A Pattern

A sophisticated multi-tenant architecture for aviation industry operations using the MAS-A2A (Multi-Agent System Agent-to-Agent) pattern with intelligent agent executors.

## 🚀 Features

- **MAS-A2A Pattern**: Agent-to-Agent communication with proper executor architecture
- **Multi-Tenant Architecture**: Support for multiple aviation organizations
- **Specialized Agent Executors**: HR, Meeting Room Management, Supply Chain & Inventory
- **Intelligent Orchestration**: Smart routing and multi-agent coordination
- **FastAPI Backend**: RESTful API with real-time responses
- **Web Interface**: User-friendly chat interface with agent selection
- **Ollama Integration**: Local LLM support with fallback capabilities
- **Tool Integration**: Simplified tools without external dependencies

## 🏗️ Architecture

### Agent Executor Pattern
The system follows the MAS-A2A pattern with the following components:

1. **BaseAgentExecutor**: Abstract base class for all agent executors
2. **Specialized Executors**: Each agent type has its own executor
3. **Task Management**: Status tracking, progress updates, and artifact handling
4. **Orchestrator**: Coordinates multi-agent workflows and response synthesis

### Agent Types
1. **HR Agent Executor**: Employee management, certifications, training compliance
2. **Meeting Agent Executor**: Room booking, scheduling, calendar integration  
3. **Supply Chain Agent Executor**: Inventory management, procurement, supplier relations
4. **Orchestrator Agent Executor**: Smart routing and multi-agent coordination

### Technology Stack
- **FastAPI** for web framework
- **LiteLLM** for model abstraction and Ollama integration
- **Pydantic** for data validation and type safety
- **Uvicorn** for ASGI server
- **Custom Executors** following MAS-A2A pattern

## 📦 Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```
DEFAULT_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

3. Run the setup script:
```bash
./setup.ps1
```

## 🚀 Usage

### Starting the System
```bash
python main.py
```

The system will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Web Interface
The web interface provides:
- Agent selection (Orchestrator, HR, Meeting, Supply Chain)
- Real-time chat with intelligent agents
- Status monitoring and execution time tracking
- Professional aviation-themed UI

### API Endpoints

- `POST /chat` - Main chat interface with agent selection
- `GET /agents` - List available agents and system status
- `GET /agents/{agent_type}/status` - Get specific agent status
- `POST /agents/{agent_type}/chat` - Chat with specific agent directly
- `GET /health` - System health check
- `GET /tenants` - List available tenants

### Example API Usage

```bash
# Chat with orchestrator (smart routing)
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Schedule a flight briefing meeting and check inventory",
       "agent_type": "orchestrator",
       "tenant_id": "aviation_demo"
     }'

# Direct HR agent interaction
curl -X POST "http://localhost:8000/agents/hr/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Create employee record for new pilot",
       "tenant_id": "aviation_demo"
     }'
```

## ⚙️ Configuration

### Tenant Configuration
Edit `config/tenant_config.py` to add new aviation organizations:

```python
TENANT_CONFIGS = {
    "airline_alpha": {
        "name": "Alpha Airlines",
        "departments": ["Flight Operations", "Maintenance", "Ground Services"],
        "agents": ["hr", "meeting", "supply_chain"]
    }
}
```

### Agent Settings
Modify `config/settings.py` for system-wide configuration.

## 🤖 Agent Capabilities

### HR Agent Executor
- ✅ Employee record creation and management
- ✅ Certification tracking (pilot licenses, mechanic certifications)
- ✅ Training schedule coordination  
- ✅ Compliance report generation

### Meeting Agent Executor
- ✅ Conference room booking (Flight Ops Center, Briefing Rooms, etc.)
- ✅ Availability checking and conflict resolution
- ✅ Booking cancellation and management
- ✅ Meeting utilization reporting

### Supply Chain Agent Executor
- ✅ Aircraft parts inventory tracking
- ✅ Parts ordering and procurement
- ✅ Supplier status monitoring
- ✅ Low stock alerts and reporting

### Orchestrator Agent Executor
- ✅ Smart query routing to appropriate agents
- ✅ Multi-agent coordination for complex queries
- ✅ Response synthesis from multiple agents
- ✅ Parallel and sequential agent execution

## 🛠️ Development

### MAS-A2A Executor Pattern
The system implements a clean executor pattern:

```python
# Base executor with task management
class BaseAgentExecutor(ABC):
    async def execute(self, context: RequestContext) -> Dict[str, Any]
    async def execute_task(self, context: RequestContext, task_updater: TaskUpdater) -> AsyncIterable[Any]

# Specialized executor implementation
class HRAgentExecutor(BaseAgentExecutor):
    async def execute_task(self, context, task_updater):
        # HR-specific logic with tool integration
        # Status updates, progress tracking, artifact management
```

### Adding New Agent Executors
1. Create executor class inheriting from `BaseAgentExecutor`
2. Implement `execute_task` method with agent-specific logic
3. Add tool integration if needed
4. Register in main application `AGENT_REGISTRY`

### Tool Integration
Tools are simplified Python functions without external dependencies:

```python
async def create_employee_record(employee_data: Dict[str, Any]) -> Dict[str, Any]:
    # Simple function implementation
    # Returns structured response with status and data
```

## 🧪 Testing

The system provides comprehensive testing capabilities:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test agent status
curl http://localhost:8000/agents

# Test specific agent
curl http://localhost:8000/agents/hr/status
```

## 🚀 Deployment

The system supports multiple deployment options:

- **Local Development**: Direct Python execution
- **Production**: Uvicorn with proper configuration
- **Containerized**: Docker-ready with proper dependencies
- **Cloud**: Compatible with AWS/Azure/GCP

## 📊 System Status

✅ **Completed Features:**
- MAS-A2A executor pattern implementation
- Multi-agent orchestration with smart routing
- All agent executors (HR, Meeting, Supply Chain)
- Web interface with real-time interaction
- API endpoints with proper error handling
- Tool integration without external dependencies
- Task management and status tracking

🎯 **Architecture Benefits:**
- Clean separation of concerns with executors
- Scalable multi-agent coordination
- Robust error handling and fallback
- Professional aviation-focused interface
- Production-ready with proper monitoring

## 🆘 Support

The system is fully operational and ready for aviation industry use cases. For advanced configurations or custom implementations, refer to the executor pattern documentation in the codebase.

---

**Built with the MAS-A2A Pattern** - A robust, scalable, and maintainable multi-agent architecture for enterprise aviation operations.