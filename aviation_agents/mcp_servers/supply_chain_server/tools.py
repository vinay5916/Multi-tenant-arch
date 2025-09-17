# mcp_servers/supply_chain_server/tools.py - Simplified tools without adk dependencies
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import asyncio

# Mock inventory data
INVENTORY_ITEMS = {
    "ENG_PART_001": {"name": "Turbine Blade Set", "category": "Engine", "current_stock": 15, "min_stock": 5},
    "LAND_GEAR_01": {"name": "Landing Gear Assembly", "category": "Landing System", "current_stock": 3, "min_stock": 2},
    "AVIONICS_A1": {"name": "Navigation Computer", "category": "Avionics", "current_stock": 8, "min_stock": 3},
    "HYDRAULIC_P1": {"name": "Hydraulic Pump", "category": "Hydraulics", "current_stock": 12, "min_stock": 4},
    "BRAKE_DISC_1": {"name": "Carbon Brake Disc", "category": "Braking System", "current_stock": 20, "min_stock": 8}
}

SUPPLIERS = {
    "SUP_001": {"name": "AeroTech Industries", "status": "active", "rating": "A", "location": "Seattle, WA"},
    "SUP_002": {"name": "Aviation Parts Direct", "status": "active", "rating": "B+", "location": "Miami, FL"},
    "SUP_003": {"name": "Global Aviation Supply", "status": "pending", "rating": "A-", "location": "Dallas, TX"}
}

# Mock databases
inventory_db: Dict[str, Dict[str, Any]] = INVENTORY_ITEMS.copy()
orders_db: Dict[str, Dict[str, Any]] = {}
supplier_db: Dict[str, Dict[str, Any]] = SUPPLIERS.copy()

async def track_inventory(inventory_data: Dict[str, Any]) -> Dict[str, Any]:
    """Track inventory levels"""
    try:
        part_number = inventory_data.get("part_number", "ENG_PART_001")
        location = inventory_data.get("location", "Main Warehouse")
        check_type = inventory_data.get("check_type", "current_stock")
        
        if part_number in inventory_db:
            item = inventory_db[part_number]
            
            result = {
                "part_number": part_number,
                "part_name": item["name"],
                "category": item["category"],
                "current_stock": item["current_stock"],
                "minimum_stock": item["min_stock"],
                "location": location,
                "stock_status": "normal" if item["current_stock"] > item["min_stock"] else "low",
                "reorder_needed": item["current_stock"] <= item["min_stock"]
            }
        else:
            result = {
                "part_number": part_number,
                "status": "not_found",
                "message": f"Part {part_number} not found in inventory"
            }
        
        return {
            "status": "success",
            "message": f"Inventory tracked for part {part_number}",
            "details": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to track inventory: {str(e)}"
        }

async def order_parts(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Order parts from suppliers"""
    try:
        order_id = f"ORDER_{str(uuid.uuid4())[:8]}"
        part_number = order_data.get("part_number", "ENG_PART_001")
        quantity = order_data.get("quantity", 1)
        supplier_id = order_data.get("supplier_id", "SUP_001")
        
        order = {
            "order_id": order_id,
            "part_number": part_number,
            "part_name": inventory_db.get(part_number, {}).get("name", "Unknown Part"),
            "quantity": quantity,
            "supplier_id": supplier_id,
            "supplier_name": supplier_db.get(supplier_id, {}).get("name", "Unknown Supplier"),
            "priority": order_data.get("priority", "normal"),
            "delivery_date": order_data.get("delivery_date", (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")),
            "cost_center": order_data.get("cost_center", "Maintenance"),
            "estimated_cost": quantity * 1500,  # Mock cost calculation
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        orders_db[order_id] = order
        
        return {
            "status": "success",
            "message": f"Order placed successfully",
            "order_id": order_id,
            "details": order
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to place order: {str(e)}"
        }

async def check_supplier_status(supplier_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check supplier status and information"""
    try:
        supplier_id = supplier_data.get("supplier_id", "SUP_001")
        check_type = supplier_data.get("check_type", "basic_info")
        
        if supplier_id in supplier_db:
            supplier = supplier_db[supplier_id]
            
            result = {
                "supplier_id": supplier_id,
                "supplier_name": supplier["name"],
                "status": supplier["status"],
                "rating": supplier["rating"],
                "location": supplier["location"],
                "active_orders": len([o for o in orders_db.values() if o.get("supplier_id") == supplier_id]),
                "last_delivery": "2024-01-15",  # Mock data
                "on_time_performance": "92%"  # Mock data
            }
        else:
            result = {
                "supplier_id": supplier_id,
                "status": "not_found",
                "message": f"Supplier {supplier_id} not found"
            }
        
        return {
            "status": "success",
            "message": f"Supplier status checked for {supplier_id}",
            "details": result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check supplier status: {str(e)}"
        }

async def generate_inventory_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate inventory and supply chain reports"""
    try:
        report_type = report_data.get("report_type", "low_stock_alert")
        report_id = f"RPT_{str(uuid.uuid4())[:8]}"
        
        if report_type == "low_stock_alert":
            low_stock_items = [
                {
                    "part_number": part_id,
                    "name": item["name"],
                    "current_stock": item["current_stock"],
                    "minimum_stock": item["min_stock"],
                    "shortage": item["min_stock"] - item["current_stock"]
                }
                for part_id, item in inventory_db.items()
                if item["current_stock"] <= item["min_stock"]
            ]
            
            report_content = {
                "total_parts": len(inventory_db),
                "low_stock_items": low_stock_items,
                "low_stock_count": len(low_stock_items),
                "total_orders": len(orders_db),
                "pending_orders": len([o for o in orders_db.values() if o.get("status") == "pending"])
            }
        else:
            report_content = {
                "message": f"Report type '{report_type}' generated",
                "data": {
                    "inventory_items": len(inventory_db),
                    "suppliers": len(supplier_db),
                    "orders": len(orders_db)
                }
            }
        
        return {
            "status": "success",
            "message": f"Supply chain report generated successfully",
            "report_id": report_id,
            "report_type": report_type,
            "content": report_content,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate report: {str(e)}"
        }