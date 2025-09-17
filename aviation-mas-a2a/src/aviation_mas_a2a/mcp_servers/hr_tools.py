"""
HR Tools for Aviation System using FastMCP
"""
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from loguru import logger

from ..shared.config import config


class HRTools:
    """HR operations tools for aviation system"""
    
    def __init__(self):
        self.mcp = FastMCP("Aviation HR Server")
        self.employees_db: Dict[str, Dict[str, Any]] = {}
        self.trainings_db: Dict[str, List[Dict[str, Any]]] = {}
        self.certifications_db: Dict[str, List[Dict[str, Any]]] = {}
        
        # Register MCP tools
        self._register_tools()
        logger.info("HR Tools initialized")
    
    def _register_tools(self):
        """Register all HR tools with FastMCP"""
        
        @self.mcp.tool()
        async def create_employee_record(
            name: str,
            position: str,
            department: str,
            hire_date: Optional[str] = None,
            certifications: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """Create a new employee record for aviation personnel"""
            try:
                employee_id = f"EMP_{str(uuid.uuid4())[:8]}"
                
                employee = {
                    "employee_id": employee_id,
                    "name": name,
                    "position": position,
                    "department": department,
                    "hire_date": hire_date or datetime.now().strftime("%Y-%m-%d"),
                    "certifications": certifications or [],
                    "status": "active",
                    "created_at": datetime.now().isoformat()
                }
                
                self.employees_db[employee_id] = employee
                logger.info(f"Created employee record: {employee_id}")
                
                return {
                    "status": "success",
                    "message": f"Employee {name} created successfully",
                    "employee_id": employee_id,
                    "details": employee
                }
                
            except Exception as e:
                logger.error(f"Error creating employee: {e}")
                return {"status": "error", "message": f"Failed to create employee: {str(e)}"}
        
        @self.mcp.tool()
        async def schedule_training(
            employee_id: str,
            training_type: str,
            scheduled_date: str,
            duration_hours: int = 8,
            instructor: Optional[str] = None
        ) -> Dict[str, Any]:
            """Schedule training for aviation personnel"""
            try:
                if employee_id not in self.employees_db:
                    return {"status": "error", "message": "Employee not found"}
                
                training_id = f"TRN_{str(uuid.uuid4())[:8]}"
                training = {
                    "training_id": training_id,
                    "employee_id": employee_id,
                    "training_type": training_type,
                    "scheduled_date": scheduled_date,
                    "duration_hours": duration_hours,
                    "instructor": instructor,
                    "status": "scheduled",
                    "created_at": datetime.now().isoformat()
                }
                
                if employee_id not in self.trainings_db:
                    self.trainings_db[employee_id] = []
                self.trainings_db[employee_id].append(training)
                
                logger.info(f"Scheduled training: {training_id}")
                return {
                    "status": "success",
                    "message": f"Training {training_type} scheduled successfully",
                    "training_id": training_id,
                    "details": training
                }
                
            except Exception as e:
                logger.error(f"Error scheduling training: {e}")
                return {"status": "error", "message": f"Failed to schedule training: {str(e)}"}
        
        @self.mcp.tool()
        async def get_employee_info(employee_id: str) -> Dict[str, Any]:
            """Get detailed information about an aviation employee"""
            try:
                if employee_id not in self.employees_db:
                    return {"status": "error", "message": "Employee not found"}
                
                employee = self.employees_db[employee_id]
                trainings = self.trainings_db.get(employee_id, [])
                certifications = self.certifications_db.get(employee_id, [])
                
                return {
                    "status": "success",
                    "employee": employee,
                    "trainings": trainings,
                    "certifications": certifications
                }
                
            except Exception as e:
                logger.error(f"Error getting employee info: {e}")
                return {"status": "error", "message": f"Failed to get employee info: {str(e)}"}
        
        @self.mcp.tool()
        async def list_employees_by_department(department: str) -> Dict[str, Any]:
            """List all employees in a specific aviation department"""
            try:
                employees = [
                    emp for emp in self.employees_db.values()
                    if emp["department"].lower() == department.lower()
                ]
                
                return {
                    "status": "success",
                    "department": department,
                    "employee_count": len(employees),
                    "employees": employees
                }
                
            except Exception as e:
                logger.error(f"Error listing employees: {e}")
                return {"status": "error", "message": f"Failed to list employees: {str(e)}"}
    
    def get_tools(self) -> List[Any]:
        """Get all registered HR tools"""
        return list(self.mcp.get_tools().values())
    
    async def start_server(self, port: int = None):
        """Start the HR MCP server"""
        server_port = port or config.mcp_base_port + 1
        logger.info(f"Starting HR MCP server on port {server_port}")
        await self.mcp.run(host=config.mcp_host, port=server_port)