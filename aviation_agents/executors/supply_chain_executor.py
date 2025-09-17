# executors/supply_chain_executor.py
import asyncio
import logging
from typing import Any, Dict, AsyncIterable, List
import json

from .base_executor import BaseAgentExecutor, RequestContext, TaskUpdater, TaskState, Artifact
from mcp_servers.supply_chain_server.tools import (
    track_inventory,
    order_parts,
    check_supplier_status,
    generate_inventory_report
)

logger = logging.getLogger(__name__)


class SupplyChainAgentExecutor(BaseAgentExecutor):
    """Supply Chain Agent executor following mas-a2a pattern with tool integration"""
    
    def __init__(self):
        system_prompt = """You are an expert Aviation Supply Chain Management assistant specializing in inventory, procurement, and supplier management for aviation organizations.

Your expertise includes:
- Aircraft parts and components inventory
- Supplier relationship management
- Procurement and ordering processes
- Aviation-specific compliance (FAA/EASA parts)
- Maintenance planning and parts availability

Key responsibilities:
1. INVENTORY MANAGEMENT:
   - Track parts inventory levels
   - Monitor critical component stock
   - Manage reorder points and safety stock
   - Handle part serialization and traceability

2. PROCUREMENT:
   - Process purchase orders
   - Manage supplier relationships
   - Ensure regulatory compliance
   - Track delivery schedules

Available tools:
- track_inventory: Monitor inventory levels
- order_parts: Process part orders
- check_supplier_status: Verify supplier information
- generate_inventory_report: Generate inventory reports

Always use the appropriate tools to perform supply chain tasks. Provide clear, detailed responses for procurement and inventory management."""

        super().__init__(
            agent_name="Aviation Supply Chain Agent",
            agent_type="supply_chain_specialist", 
            system_prompt=system_prompt
        )
    
    async def execute_task(self, context: RequestContext, task_updater: TaskUpdater) -> AsyncIterable[Any]:
        """Execute supply chain-specific tasks"""
        try:
            # Update status
            task_updater.update_status(TaskState.WORKING, "Analyzing supply chain request", 25.0)
            
            # Get LLM response to understand the request
            llm_response = await self._call_llm(context.user_message)
            
            # Check if we need to use tools
            tool_results = await self._process_supply_chain_tools(context.user_message, context)
            
            # Update progress
            task_updater.update_status(TaskState.WORKING, "Processing supply chain data", 75.0)
            
            # Combine LLM response with tool results
            final_response = await self._combine_responses(llm_response, tool_results, context.user_message)
            
            # Add final artifact
            task_updater.add_artifact(
                content=final_response,
                artifact_type="supply_chain_response",
                metadata={
                    "agent_type": "supply_chain",
                    "tools_used": len(tool_results) > 0,
                    "tenant_id": context.tenant_id
                }
            )
            
            # Complete task
            task_updater.complete()
            
            yield task_updater.artifacts[-1]
            
        except Exception as e:
            logger.error(f"Supply Chain Agent execution failed: {str(e)}")
            task_updater.fail(f"Supply chain task failed: {str(e)}")
            raise
    
    async def _process_supply_chain_tools(self, user_message: str, context: RequestContext) -> List[Dict[str, Any]]:
        """Process supply chain-related tool calls based on user message"""
        tool_results = []
        message_lower = user_message.lower()
        
        try:
            # Detect tool usage needs based on keywords
            if any(keyword in message_lower for keyword in ["inventory", "stock", "check parts", "track"]):
                result = await track_inventory({
                    "part_number": "ENG_PART_001",
                    "location": "Main Warehouse",
                    "check_type": "current_stock"
                })
                tool_results.append({"tool": "track_inventory", "result": result})
            
            if any(keyword in message_lower for keyword in ["order", "purchase", "buy parts", "procurement"]):
                result = await order_parts({
                    "part_number": "ENG_PART_001",
                    "quantity": 5,
                    "supplier_id": "SUP_001",
                    "priority": "normal",
                    "delivery_date": "2024-02-15",
                    "cost_center": "Maintenance"
                })
                tool_results.append({"tool": "order_parts", "result": result})
            
            if any(keyword in message_lower for keyword in ["supplier", "vendor", "check supplier"]):
                result = await check_supplier_status({
                    "supplier_id": "SUP_001",
                    "check_type": "full_status"
                })
                tool_results.append({"tool": "check_supplier_status", "result": result})
            
            if any(keyword in message_lower for keyword in ["report", "inventory report", "summary"]):
                result = await generate_inventory_report({
                    "report_type": "low_stock_alert",
                    "date_range": "2024-01-01_2024-01-31",
                    "location_filter": "all"
                })
                tool_results.append({"tool": "generate_inventory_report", "result": result})
                
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            tool_results.append({"tool": "error", "result": f"Tool execution failed: {str(e)}"})
        
        return tool_results
    
    async def _combine_responses(self, llm_response: str, tool_results: List[Dict[str, Any]], user_message: str) -> str:
        """Combine LLM response with tool results"""
        if not tool_results:
            return llm_response
        
        # Create a comprehensive response
        combined_response = f"{llm_response}\n\n"
        
        if tool_results:
            combined_response += "## Supply Chain System Actions Performed:\n\n"
            for tool_result in tool_results:
                tool_name = tool_result.get("tool", "unknown")
                result = tool_result.get("result", {})
                
                if tool_name != "error":
                    combined_response += f"✅ **{tool_name.replace('_', ' ').title()}:**\n"
                    if isinstance(result, dict):
                        for key, value in result.items():
                            combined_response += f"   - {key.replace('_', ' ').title()}: {value}\n"
                    else:
                        combined_response += f"   - Result: {result}\n"
                    combined_response += "\n"
                else:
                    combined_response += f"❌ **Error:** {result}\n\n"
        
        return combined_response