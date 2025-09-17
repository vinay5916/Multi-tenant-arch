# mcp_servers/supply_chain_server/tools.py
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid

# adk tools
from adktools import adk_tool

# Local imports
from .models import (
    AviationPart, StockMovement, PurchaseOrder,
    CreatePurchaseOrderInput, UpdateStockInput, SearchPartsInput,
    PartNotFoundError, InsufficientStockError, SupplierNotFoundError, InvalidMovementTypeError,
    PartCategory, PartStatus, OrderStatus, UrgencyLevel
)

# Aviation suppliers
SUPPLIERS = {
    "boeing": {"name": "Boeing Supply", "contact": "boeing@supplier.com", "rating": "A"},
    "airbus": {"name": "Airbus Parts", "contact": "parts@airbus.com", "rating": "A"},
    "ge_aviation": {"name": "GE Aviation", "contact": "orders@ge.com", "rating": "A"},
    "pratt_whitney": {"name": "Pratt & Whitney", "contact": "supply@pw.com", "rating": "A"},
    "honeywell": {"name": "Honeywell Aerospace", "contact": "aerospace@honeywell.com", "rating": "B"},
    "collins": {"name": "Collins Aerospace", "contact": "parts@collins.com", "rating": "B"},
    "safran": {"name": "Safran Group", "contact": "orders@safran.com", "rating": "A"},
    "local_supplier": {"name": "Local Aviation Supply", "contact": "info@localaviation.com", "rating": "C"}
}

# Mock database
parts_inventory: Dict[str, AviationPart] = {}
stock_movements: List[StockMovement] = []
purchase_orders: Dict[str, PurchaseOrder] = {}

# Initialize with sample aviation parts
def initialize_sample_parts():
    """Initialize with realistic aviation parts"""
    sample_parts = [
        AviationPart(
            part_number="ENG-737-001",
            description="Engine Oil Filter - Boeing 737",
            category=PartCategory.ENGINE_COMPONENT,
            manufacturer="Boeing",
            unit_price=1250.00,
            current_stock=15,
            min_stock_level=5,
            max_stock_level=50,
            location="Warehouse-A-Section-1",
            serial_tracked=True,
            weight_kg=2.5,
            certification_required=True,
            supplier_id="boeing"
        ),
        AviationPart(
            part_number="AVIONICS-A320-GPS",
            description="GPS Navigation Unit - Airbus A320",
            category=PartCategory.AVIONICS,
            manufacturer="Honeywell",
            unit_price=45000.00,
            current_stock=3,
            min_stock_level=2,
            max_stock_level=8,
            location="Warehouse-B-High-Value",
            serial_tracked=True,
            weight_kg=15.0,
            certification_required=True,
            supplier_id="honeywell"
        ),
        AviationPart(
            part_number="HYDRAULIC-FLUID-5606",
            description="Hydraulic Fluid MIL-PRF-5606",
            category=PartCategory.CONSUMABLES,
            manufacturer="Generic",
            unit_price=85.00,
            current_stock=200,
            min_stock_level=50,
            max_stock_level=500,
            location="Warehouse-C-Fluids",
            shelf_life_days=1095,  # 3 years
            weight_kg=1.0,
            certification_required=True,
            supplier_id="local_supplier"
        ),
        AviationPart(
            part_number="LG-TIRE-737-MAIN",
            description="Main Landing Gear Tire - Boeing 737",
            category=PartCategory.LANDING_GEAR,
            manufacturer="Michelin",
            unit_price=3200.00,
            current_stock=8,
            min_stock_level=4,
            max_stock_level=20,
            location="Warehouse-D-Tires",
            weight_kg=68.0,
            certification_required=True,
            supplier_id="boeing"
        ),
        AviationPart(
            part_number="SAFETY-VEST-CREW",
            description="Crew Safety Vest - High Visibility",
            category=PartCategory.CONSUMABLES,
            manufacturer="Safety First",
            unit_price=45.00,
            current_stock=25,
            min_stock_level=10,
            max_stock_level=100,
            location="Warehouse-E-Safety",
            weight_kg=0.5,
            certification_required=False,
            supplier_id="local_supplier"
        )
    ]
    
    for part in sample_parts:
        parts_inventory[part.part_number] = part

# Initialize sample data
initialize_sample_parts()

def get_part_status(part: AviationPart) -> PartStatus:
    """Determine part status based on current stock levels"""
    if part.current_stock <= 0:
        return PartStatus.OUT_OF_STOCK
    elif part.current_stock <= part.min_stock_level:
        return PartStatus.LOW_STOCK
    else:
        return PartStatus.IN_STOCK

@adk_tool(
    name="search_parts",
    description="Search for aviation parts in inventory. Essential for finding parts for maintenance and operations."
)
def search_parts(
    part_number: Optional[str] = None,
    category: Optional[str] = None,
    manufacturer: Optional[str] = None,
    status: Optional[str] = None,
    min_stock_qty: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Search for parts based on various criteria
    
    Args:
        part_number: Partial part number to search
        category: Part category (engine_component, avionics, etc.)
        manufacturer: Manufacturer name
        status: Stock status (in_stock, low_stock, out_of_stock)
        min_stock_qty: Minimum stock quantity threshold
        
    Returns:
        List[Dict]: List of parts matching the search criteria
    """
    try:
        results = []
        
        for part in parts_inventory.values():
            # Apply filters
            if part_number and part_number.upper() not in part.part_number.upper():
                continue
            if category and part.category != category:
                continue
            if manufacturer and manufacturer.lower() not in part.manufacturer.lower():
                continue
            if min_stock_qty and part.current_stock < min_stock_qty:
                continue
                
            current_status = get_part_status(part)
            if status and current_status != status:
                continue
            
            # Add to results
            results.append({
                "part_number": part.part_number,
                "description": part.description,
                "category": part.category,
                "manufacturer": part.manufacturer,
                "current_stock": part.current_stock,
                "min_stock_level": part.min_stock_level,
                "status": current_status,
                "unit_price": part.unit_price,
                "location": part.location,
                "serial_tracked": part.serial_tracked,
                "certification_required": part.certification_required,
                "supplier": SUPPLIERS.get(part.supplier_id, {}).get("name", "Unknown")
            })
        
        # Sort by part number
        results.sort(key=lambda x: x["part_number"])
        return results
        
    except Exception as e:
        raise RuntimeError(f"Error searching parts: {str(e)}")

@adk_tool(
    name="check_low_stock_parts",
    description="Check for parts that are at or below minimum stock levels. Critical for maintaining operations."
)
def check_low_stock_parts() -> List[Dict[str, Any]]:
    """Check for parts with low stock levels
    
    Returns:
        List[Dict]: List of parts at or below minimum stock levels
    """
    try:
        low_stock_parts = []
        
        for part in parts_inventory.values():
            if part.current_stock <= part.min_stock_level:
                days_since_last_order = 0
                if part.last_ordered_date:
                    days_since_last_order = (date.today() - part.last_ordered_date).days
                
                low_stock_parts.append({
                    "part_number": part.part_number,
                    "description": part.description,
                    "category": part.category,
                    "current_stock": part.current_stock,
                    "min_stock_level": part.min_stock_level,
                    "shortage": part.min_stock_level - part.current_stock,
                    "suggested_order_qty": part.max_stock_level - part.current_stock,
                    "unit_price": part.unit_price,
                    "total_cost": (part.max_stock_level - part.current_stock) * part.unit_price,
                    "supplier": SUPPLIERS.get(part.supplier_id, {}).get("name", "Unknown"),
                    "days_since_last_order": days_since_last_order,
                    "location": part.location
                })
        
        # Sort by shortage severity (highest shortage first)
        low_stock_parts.sort(key=lambda x: x["shortage"], reverse=True)
        return low_stock_parts
        
    except Exception as e:
        raise RuntimeError(f"Error checking low stock parts: {str(e)}")

@adk_tool(
    name="update_stock",
    description="Update stock levels for a part. Used for receiving parts, issuing parts for maintenance, etc."
)
def update_stock(
    part_number: str,
    movement_type: str,
    quantity: int,
    reference_doc: Optional[str] = None,
    performed_by: str = "system"
) -> Dict[str, Any] | PartNotFoundError | InvalidMovementTypeError | InsufficientStockError:
    """Update stock levels for a part
    
    Args:
        part_number: Part number to update
        movement_type: Type of movement (IN, OUT, TRANSFER, ADJUSTMENT)
        quantity: Quantity to move (positive for IN, negative for OUT)
        reference_doc: Reference document (PO number, work order, etc.)
        performed_by: Employee ID performing the update
        
    Returns:
        Dict: Updated stock information
        PartNotFoundError: If part doesn't exist
        InvalidMovementTypeError: If movement type is invalid
        InsufficientStockError: If trying to remove more stock than available
    """
    try:
        # Validate part exists
        if part_number not in parts_inventory:
            return PartNotFoundError(
                part_number=part_number,
                message=f"Part '{part_number}' not found in inventory"
            )
        
        # Validate movement type
        valid_types = ["IN", "OUT", "TRANSFER", "ADJUSTMENT"]
        if movement_type not in valid_types:
            return InvalidMovementTypeError(
                movement_type=movement_type,
                valid_types=valid_types,
                message=f"Invalid movement type '{movement_type}'. Must be one of: {', '.join(valid_types)}"
            )
        
        part = parts_inventory[part_number]
        old_stock = part.current_stock
        
        # Calculate new stock level
        if movement_type in ["OUT"]:
            if part.current_stock < abs(quantity):
                return InsufficientStockError(
                    part_number=part_number,
                    requested_quantity=abs(quantity),
                    available_quantity=part.current_stock,
                    message=f"Insufficient stock. Requested: {abs(quantity)}, Available: {part.current_stock}"
                )
            new_stock = part.current_stock - abs(quantity)
        else:  # IN, TRANSFER, ADJUSTMENT
            new_stock = part.current_stock + quantity
        
        # Update stock
        part.current_stock = max(0, new_stock)  # Ensure non-negative
        
        # Create stock movement record
        movement_id = f"MOV{uuid.uuid4().hex[:8].upper()}"
        movement = StockMovement(
            movement_id=movement_id,
            part_number=part_number,
            movement_type=movement_type,
            quantity=quantity,
            reference_doc=reference_doc,
            timestamp=datetime.now(),
            performed_by=performed_by
        )
        stock_movements.append(movement)
        
        # Determine new status
        new_status = get_part_status(part)
        
        return {
            "part_number": part_number,
            "description": part.description,
            "movement_id": movement_id,
            "movement_type": movement_type,
            "quantity_moved": quantity,
            "old_stock": old_stock,
            "new_stock": part.current_stock,
            "new_status": new_status,
            "reference_doc": reference_doc,
            "timestamp": movement.timestamp.isoformat(),
            "performed_by": performed_by
        }
        
    except Exception as e:
        raise RuntimeError(f"Error updating stock: {str(e)}")

@adk_tool(
    name="create_purchase_order",
    description="Create a purchase order for parts. Essential for restocking inventory and AOG situations."
)
def create_purchase_order(
    supplier_id: str,
    requested_by: str,
    urgency_level: str,
    items: List[Dict[str, Any]],
    expected_delivery: Optional[str] = None
) -> PurchaseOrder | SupplierNotFoundError | PartNotFoundError:
    """Create a purchase order
    
    Args:
        supplier_id: Supplier ID
        requested_by: Employee ID requesting the order
        urgency_level: Urgency level (low, medium, high, critical)
        items: List of items with part_number and quantity
        expected_delivery: Expected delivery date in YYYY-MM-DD format
        
    Returns:
        PurchaseOrder: The created purchase order
        SupplierNotFoundError: If supplier doesn't exist
        PartNotFoundError: If any part doesn't exist
    """
    try:
        # Validate supplier
        if supplier_id not in SUPPLIERS:
            return SupplierNotFoundError(
                supplier_id=supplier_id,
                available_suppliers=list(SUPPLIERS.keys()),
                message=f"Supplier '{supplier_id}' not found"
            )
        
        # Validate all parts exist and calculate total
        validated_items = []
        total_amount = 0.0
        
        for item in items:
            part_number = item.get("part_number")
            quantity = item.get("quantity", 1)
            
            if part_number not in parts_inventory:
                return PartNotFoundError(
                    part_number=part_number,
                    message=f"Part '{part_number}' not found in inventory"
                )
            
            part = parts_inventory[part_number]
            line_total = part.unit_price * quantity
            total_amount += line_total
            
            validated_items.append({
                "part_number": part_number,
                "description": part.description,
                "quantity": quantity,
                "unit_price": part.unit_price,
                "line_total": line_total
            })
        
        # Parse expected delivery date
        expected_delivery_date = None
        if expected_delivery:
            expected_delivery_date = datetime.strptime(expected_delivery, "%Y-%m-%d").date()
        
        # Create PO
        po_number = f"PO{uuid.uuid4().hex[:8].upper()}"
        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            order_date=date.today(),
            requested_by=requested_by,
            urgency_level=UrgencyLevel(urgency_level),
            status=OrderStatus.PENDING,
            total_amount=total_amount,
            expected_delivery=expected_delivery_date,
            items=validated_items
        )
        
        # Store PO
        purchase_orders[po_number] = po
        
        # Update last ordered date for parts
        for item in validated_items:
            part = parts_inventory[item["part_number"]]
            part.last_ordered_date = date.today()
        
        return po
        
    except ValueError as e:
        raise RuntimeError(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating purchase order: {str(e)}")

@adk_tool(
    name="get_part_details",
    description="Get detailed information about a specific part including stock history."
)
def get_part_details(part_number: str) -> Dict[str, Any] | PartNotFoundError:
    """Get detailed part information
    
    Args:
        part_number: Part number to look up
        
    Returns:
        Dict: Detailed part information
        PartNotFoundError: If part doesn't exist
    """
    try:
        if part_number not in parts_inventory:
            return PartNotFoundError(
                part_number=part_number,
                message=f"Part '{part_number}' not found in inventory"
            )
        
        part = parts_inventory[part_number]
        
        # Get recent stock movements
        recent_movements = [
            {
                "movement_id": mov.movement_id,
                "movement_type": mov.movement_type,
                "quantity": mov.quantity,
                "reference_doc": mov.reference_doc,
                "timestamp": mov.timestamp.isoformat(),
                "performed_by": mov.performed_by
            }
            for mov in stock_movements 
            if mov.part_number == part_number
        ][-10:]  # Last 10 movements
        
        # Get pending orders
        pending_orders = []
        for po in purchase_orders.values():
            if po.status in [OrderStatus.PENDING, OrderStatus.APPROVED, OrderStatus.ORDERED]:
                for item in po.items:
                    if item["part_number"] == part_number:
                        pending_orders.append({
                            "po_number": po.po_number,
                            "quantity": item["quantity"],
                            "expected_delivery": po.expected_delivery.isoformat() if po.expected_delivery else None,
                            "status": po.status,
                            "urgency": po.urgency_level
                        })
        
        return {
            "part_details": {
                "part_number": part.part_number,
                "description": part.description,
                "category": part.category,
                "manufacturer": part.manufacturer,
                "unit_price": part.unit_price,
                "current_stock": part.current_stock,
                "min_stock_level": part.min_stock_level,
                "max_stock_level": part.max_stock_level,
                "location": part.location,
                "serial_tracked": part.serial_tracked,
                "shelf_life_days": part.shelf_life_days,
                "weight_kg": part.weight_kg,
                "certification_required": part.certification_required,
                "supplier": SUPPLIERS.get(part.supplier_id, {}).get("name", "Unknown"),
                "status": get_part_status(part)
            },
            "stock_analysis": {
                "days_of_supply": max(0, part.current_stock // max(1, len([m for m in stock_movements if m.part_number == part_number and m.movement_type == "OUT"]) // 30)),
                "reorder_point_reached": part.current_stock <= part.min_stock_level,
                "suggested_order_quantity": max(0, part.max_stock_level - part.current_stock) if part.current_stock <= part.min_stock_level else 0
            },
            "recent_movements": recent_movements,
            "pending_orders": pending_orders
        }
        
    except Exception as e:
        raise RuntimeError(f"Error getting part details: {str(e)}")

@adk_tool(
    name="get_supplier_performance",
    description="Get performance metrics for suppliers including delivery times and order fulfillment."
)
def get_supplier_performance() -> Dict[str, Any]:
    """Get supplier performance analytics
    
    Returns:
        Dict: Supplier performance metrics
    """
    try:
        supplier_metrics = {}
        
        for supplier_id, supplier_info in SUPPLIERS.items():
            # Get orders for this supplier
            supplier_orders = [po for po in purchase_orders.values() if po.supplier_id == supplier_id]
            
            total_orders = len(supplier_orders)
            completed_orders = len([po for po in supplier_orders if po.status == OrderStatus.RECEIVED])
            pending_orders = len([po for po in supplier_orders if po.status in [OrderStatus.PENDING, OrderStatus.APPROVED, OrderStatus.ORDERED]])
            total_value = sum([po.total_amount for po in supplier_orders])
            
            # Calculate average delivery time for completed orders
            avg_delivery_days = 0
            if completed_orders > 0:
                delivery_times = []
                for po in supplier_orders:
                    if po.status == OrderStatus.RECEIVED and po.expected_delivery:
                        # Mock calculation - in real system would use actual delivery date
                        delivery_times.append(7)  # Assume 7 days average
                avg_delivery_days = sum(delivery_times) / len(delivery_times) if delivery_times else 0
            
            supplier_metrics[supplier_id] = {
                "name": supplier_info["name"],
                "rating": supplier_info["rating"],
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "pending_orders": pending_orders,
                "total_order_value": total_value,
                "completion_rate": (completed_orders / total_orders * 100) if total_orders > 0 else 0,
                "avg_delivery_days": avg_delivery_days,
                "contact": supplier_info["contact"]
            }
        
        return {
            "supplier_performance": supplier_metrics,
            "summary": {
                "total_suppliers": len(SUPPLIERS),
                "active_suppliers": len([s for s, m in supplier_metrics.items() if m["total_orders"] > 0]),
                "total_orders": sum([m["total_orders"] for m in supplier_metrics.values()]),
                "total_value": sum([m["total_order_value"] for m in supplier_metrics.values()])
            }
        }
        
    except Exception as e:
        raise RuntimeError(f"Error getting supplier performance: {str(e)}")

@adk_tool(
    name="forecast_demand",
    description="Forecast part demand based on historical usage patterns. Helps with inventory planning."
)
def forecast_demand(days_ahead: int = 90) -> List[Dict[str, Any]]:
    """Forecast part demand based on historical usage
    
    Args:
        days_ahead: Number of days to forecast
        
    Returns:
        List[Dict]: Demand forecast for each part
    """
    try:
        forecasts = []
        
        for part in parts_inventory.values():
            # Get historical usage (OUT movements)
            usage_movements = [
                mov for mov in stock_movements 
                if mov.part_number == part.part_number and mov.movement_type == "OUT"
            ]
            
            # Calculate average usage per day
            if usage_movements:
                total_usage = sum([abs(mov.quantity) for mov in usage_movements])
                days_of_data = max(1, len(set([mov.timestamp.date() for mov in usage_movements])))
                avg_daily_usage = total_usage / days_of_data
            else:
                avg_daily_usage = 0
            
            # Simple forecast: average usage * days ahead
            forecasted_demand = avg_daily_usage * days_ahead
            
            # Calculate when stock will run out
            days_until_stockout = 0
            if avg_daily_usage > 0:
                days_until_stockout = part.current_stock / avg_daily_usage
            else:
                days_until_stockout = float('inf')
            
            # Determine action needed
            action_needed = "none"
            if days_until_stockout < 30:
                action_needed = "urgent_reorder"
            elif days_until_stockout < 60:
                action_needed = "reorder_soon"
            elif part.current_stock <= part.min_stock_level:
                action_needed = "reorder_now"
            
            forecasts.append({
                "part_number": part.part_number,
                "description": part.description,
                "current_stock": part.current_stock,
                "avg_daily_usage": round(avg_daily_usage, 2),
                "forecasted_demand": round(forecasted_demand, 2),
                "days_until_stockout": round(days_until_stockout, 1) if days_until_stockout != float('inf') else "never",
                "action_needed": action_needed,
                "suggested_order_qty": max(0, part.max_stock_level - part.current_stock) if action_needed != "none" else 0,
                "category": part.category,
                "unit_price": part.unit_price
            })
        
        # Sort by urgency (days until stockout)
        forecasts.sort(key=lambda x: x["days_until_stockout"] if isinstance(x["days_until_stockout"], (int, float)) else float('inf'))
        
        return forecasts
        
    except Exception as e:
        raise RuntimeError(f"Error forecasting demand: {str(e)}")