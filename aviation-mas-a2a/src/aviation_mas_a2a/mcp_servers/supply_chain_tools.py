"""
Supply Chain Tools for Aviation System using FastMCP
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from loguru import logger

from ..shared.config import config


class SupplyChainTools:
    """Supply chain management tools for aviation system"""
    
    def __init__(self):
        self.mcp = FastMCP("Aviation Supply Chain Server")
        self.inventory_db: Dict[str, Dict[str, Any]] = {}
        self.vendors_db: Dict[str, Dict[str, Any]] = {}
        self.orders_db: Dict[str, Dict[str, Any]] = {}
        
        # Register MCP tools
        self._register_tools()
        logger.info("Supply Chain Tools initialized")
    
    def _register_tools(self):
        """Register all supply chain tools with FastMCP"""
        
        @self.mcp.tool()
        async def create_inventory_item(
            item_name: str,
            part_number: str,
            category: str,
            quantity: int,
            unit_price: float,
            supplier: Optional[str] = None,
            critical_level: int = 10
        ) -> Dict[str, Any]:
            """Create a new inventory item for aviation parts/supplies"""
            try:
                item_id = f"INV_{str(uuid.uuid4())[:8]}"
                
                item = {
                    "item_id": item_id,
                    "item_name": item_name,
                    "part_number": part_number,
                    "category": category,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "supplier": supplier,
                    "critical_level": critical_level,
                    "status": "active",
                    "last_updated": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat()
                }
                
                self.inventory_db[item_id] = item
                logger.info(f"Created inventory item: {item_id}")
                
                return {
                    "status": "success",
                    "message": f"Inventory item '{item_name}' created successfully",
                    "item_id": item_id,
                    "details": item
                }
                
            except Exception as e:
                logger.error(f"Error creating inventory item: {e}")
                return {"status": "error", "message": f"Failed to create inventory item: {str(e)}"}
        
        @self.mcp.tool()
        async def check_inventory(
            search_term: Optional[str] = None,
            category: Optional[str] = None,
            low_stock_only: bool = False
        ) -> Dict[str, Any]:
            """Check inventory levels for aviation parts and supplies"""
            try:
                items = list(self.inventory_db.values())
                
                # Filter by search term
                if search_term:
                    items = [
                        item for item in items
                        if search_term.lower() in item["item_name"].lower() or
                           search_term.lower() in item["part_number"].lower()
                    ]
                
                # Filter by category
                if category:
                    items = [
                        item for item in items
                        if item["category"].lower() == category.lower()
                    ]
                
                # Filter by low stock
                if low_stock_only:
                    items = [
                        item for item in items
                        if item["quantity"] <= item["critical_level"]
                    ]
                
                return {
                    "status": "success",
                    "items_found": len(items),
                    "items": items,
                    "search_criteria": {
                        "search_term": search_term,
                        "category": category,
                        "low_stock_only": low_stock_only
                    }
                }
                
            except Exception as e:
                logger.error(f"Error checking inventory: {e}")
                return {"status": "error", "message": f"Failed to check inventory: {str(e)}"}
        
        @self.mcp.tool()
        async def update_inventory_quantity(
            item_id: str,
            quantity_change: int,
            operation: str = "add",
            notes: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update inventory quantity (add/subtract/set)"""
            try:
                if item_id not in self.inventory_db:
                    return {"status": "error", "message": "Inventory item not found"}
                
                item = self.inventory_db[item_id]
                old_quantity = item["quantity"]
                
                if operation == "add":
                    item["quantity"] += quantity_change
                elif operation == "subtract":
                    item["quantity"] = max(0, item["quantity"] - quantity_change)
                elif operation == "set":
                    item["quantity"] = max(0, quantity_change)
                else:
                    return {"status": "error", "message": "Invalid operation. Use 'add', 'subtract', or 'set'"}
                
                item["last_updated"] = datetime.now().isoformat()
                if notes:
                    item["last_update_notes"] = notes
                
                logger.info(f"Updated inventory {item_id}: {old_quantity} -> {item['quantity']}")
                
                return {
                    "status": "success",
                    "message": f"Inventory updated for {item['item_name']}",
                    "old_quantity": old_quantity,
                    "new_quantity": item["quantity"],
                    "item": item
                }
                
            except Exception as e:
                logger.error(f"Error updating inventory: {e}")
                return {"status": "error", "message": f"Failed to update inventory: {str(e)}"}
        
        @self.mcp.tool()
        async def create_purchase_order(
            vendor_id: str,
            items: List[Dict[str, Any]],
            priority: str = "normal",
            notes: Optional[str] = None
        ) -> Dict[str, Any]:
            """Create a purchase order for aviation parts/supplies"""
            try:
                order_id = f"PO_{str(uuid.uuid4())[:8]}"
                
                total_amount = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in items)
                
                order = {
                    "order_id": order_id,
                    "vendor_id": vendor_id,
                    "items": items,
                    "total_amount": total_amount,
                    "priority": priority,
                    "status": "pending",
                    "notes": notes,
                    "created_at": datetime.now().isoformat(),
                    "expected_delivery": (datetime.now() + timedelta(days=7)).isoformat()
                }
                
                self.orders_db[order_id] = order
                logger.info(f"Created purchase order: {order_id}")
                
                return {
                    "status": "success",
                    "message": f"Purchase order {order_id} created successfully",
                    "order_id": order_id,
                    "details": order
                }
                
            except Exception as e:
                logger.error(f"Error creating purchase order: {e}")
                return {"status": "error", "message": f"Failed to create purchase order: {str(e)}"}
        
        @self.mcp.tool()
        async def get_low_stock_alerts() -> Dict[str, Any]:
            """Get alerts for items with low stock levels"""
            try:
                low_stock_items = [
                    item for item in self.inventory_db.values()
                    if item["quantity"] <= item["critical_level"]
                ]
                
                critical_items = [
                    item for item in low_stock_items
                    if item["quantity"] == 0
                ]
                
                return {
                    "status": "success",
                    "total_low_stock": len(low_stock_items),
                    "critical_items": len(critical_items),
                    "low_stock_items": low_stock_items,
                    "generated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error getting low stock alerts: {e}")
                return {"status": "error", "message": f"Failed to get low stock alerts: {str(e)}"}
    
    def get_tools(self) -> List[Any]:
        """Get all registered supply chain tools"""
        return list(self.mcp.get_tools().values())
    
    async def start_server(self, port: int = None):
        """Start the Supply Chain MCP server"""
        server_port = port or config.mcp_base_port + 3
        logger.info(f"Starting Supply Chain MCP server on port {server_port}")
        await self.mcp.run(host=config.mcp_host, port=server_port)