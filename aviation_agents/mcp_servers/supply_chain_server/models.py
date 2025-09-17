# mcp_servers/supply_chain_server/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, date
from enum import Enum

# Import from adktools
from adktools.models import DomainError

class PartCategory(str, Enum):
    ENGINE_COMPONENT = "engine_component"
    AVIONICS = "avionics"
    LANDING_GEAR = "landing_gear"
    HYDRAULICS = "hydraulics"
    ELECTRICAL = "electrical"
    STRUCTURAL = "structural"
    INTERIOR = "interior"
    CONSUMABLES = "consumables"
    TOOLS = "tools"

class PartStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    ON_ORDER = "on_order"
    BACKORDERED = "backordered"
    DISCONTINUED = "discontinued"

class OrderStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ORDERED = "ordered"
    SHIPPED = "shipped"
    RECEIVED = "received"
    CANCELLED = "cancelled"

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # AOG (Aircraft on Ground)

class AviationPart(BaseModel):
    part_number: str
    description: str
    category: PartCategory
    manufacturer: str
    unit_price: float
    current_stock: int
    min_stock_level: int
    max_stock_level: int
    location: str  # warehouse location
    serial_tracked: bool = False
    shelf_life_days: Optional[int] = None
    weight_kg: float
    dimensions: Optional[str] = None
    certification_required: bool = True
    last_ordered_date: Optional[date] = None
    supplier_id: str

class StockMovement(BaseModel):
    movement_id: str
    part_number: str
    movement_type: str  # "IN", "OUT", "TRANSFER", "ADJUSTMENT"
    quantity: int
    reference_doc: Optional[str] = None  # PO number, work order, etc.
    timestamp: datetime
    location_from: Optional[str] = None
    location_to: Optional[str] = None
    performed_by: str

class PurchaseOrder(BaseModel):
    po_number: str
    supplier_id: str
    order_date: date
    requested_by: str
    urgency_level: UrgencyLevel
    status: OrderStatus
    total_amount: float
    expected_delivery: Optional[date] = None
    items: List[Dict[str, Any]] = []  # part_number, quantity, unit_price

# Input Models
class CreatePurchaseOrderInput(BaseModel):
    supplier_id: str = Field(..., description="Supplier ID")
    requested_by: str = Field(..., description="Employee ID requesting the order")
    urgency_level: UrgencyLevel = Field(..., description="Urgency level of the order")
    items: List[Dict[str, Any]] = Field(..., description="List of items with part_number, quantity")
    expected_delivery: Optional[str] = Field(None, description="Expected delivery date in YYYY-MM-DD format")

class UpdateStockInput(BaseModel):
    part_number: str = Field(..., description="Part number to update")
    movement_type: str = Field(..., description="Movement type: IN, OUT, TRANSFER, ADJUSTMENT")
    quantity: int = Field(..., description="Quantity (positive for IN, negative for OUT)")
    reference_doc: Optional[str] = Field(None, description="Reference document (PO, work order, etc.)")
    performed_by: str = Field(..., description="Employee ID performing the update")

class SearchPartsInput(BaseModel):
    part_number: Optional[str] = Field(None, description="Partial part number to search")
    category: Optional[PartCategory] = Field(None, description="Part category")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    status: Optional[PartStatus] = Field(None, description="Stock status")
    min_stock_qty: Optional[int] = Field(None, description="Minimum stock quantity")

# Error Models
class PartNotFoundError(DomainError):
    part_number: str = Field(..., description="The part number that was not found")
    error_type: Literal["part_not_found"] = "part_not_found"

class InsufficientStockError(DomainError):
    part_number: str = Field(..., description="Part number with insufficient stock")
    requested_quantity: int = Field(..., description="Requested quantity")
    available_quantity: int = Field(..., description="Available quantity")
    error_type: Literal["insufficient_stock"] = "insufficient_stock"

class SupplierNotFoundError(DomainError):
    supplier_id: str = Field(..., description="The supplier ID that was not found")
    available_suppliers: List[str] = Field(..., description="List of available supplier IDs")
    error_type: Literal["supplier_not_found"] = "supplier_not_found"

class InvalidMovementTypeError(DomainError):
    movement_type: str = Field(..., description="The invalid movement type")
    valid_types: List[str] = Field(..., description="List of valid movement types")
    error_type: Literal["invalid_movement_type"] = "invalid_movement_type"