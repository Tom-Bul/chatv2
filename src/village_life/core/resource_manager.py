"""
Resource management system implementation.
Handles resource storage, transformation, and tracking.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
import uuid

from .abstractions.base import IResource, IModifier
from .event_system import publish_event, ResourceEvent
from .modifiers import create_modifier
from .resource_types import ResourceType, ResourceCategory

# Set up logging
logging.basicConfig(
    filename='game.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ResourceProperties:
    """Properties defining a resource type."""
    name: str
    category: ResourceCategory
    base_value: float
    decay_rate: float  # Units lost per day
    quality_impact: float  # How much quality affects value (0-1)
    stackable: bool
    max_stack: int
    weight: float  # Weight per unit
    
    def calculate_value(self, quantity: float, quality: float) -> float:
        """Calculate total value of resources."""
        base = self.base_value * quantity
        quality_bonus = base * (quality - 0.5) * self.quality_impact
        return max(0, base + quality_bonus)

class Resource(IResource):
    """Implementation of a resource stack."""
    def __init__(self, 
                 resource_type: ResourceType,
                 properties: ResourceProperties,
                 quantity: float = 0.0,
                 quality: float = 1.0):
        self._id = str(uuid.uuid4())
        self._type = resource_type
        self._properties = properties
        self._quantity = quantity
        self._quality = quality
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def type(self) -> str:
        return self._type.name
    
    @property
    def quantity(self) -> float:
        return self._quantity
    
    @property
    def quality(self) -> float:
        return self._quality
    
    def apply_modifier(self, modifier: IModifier) -> 'Resource':
        """Apply a modifier to this resource."""
        modified = modifier.modify(self)
        if not isinstance(modified, Resource):
            raise ValueError(f"Modifier returned invalid type: {type(modified)}")
        return modified
    
    def transform(self, modifier: IModifier) -> 'Resource':
        """Transform this resource using a modifier."""
        return self.apply_modifier(modifier)
    
    def combine(self, other: 'Resource') -> 'Resource':
        """Combine this resource with another of the same type."""
        if self._type != other._type:
            raise ValueError(f"Cannot combine different resource types: {self._type} and {other._type}")
        
        total_quantity = self._quantity + other._quantity
        # Calculate weighted average quality
        new_quality = ((self._quality * self._quantity) + 
                      (other._quality * other._quantity)) / total_quantity
        
        publish_event(ResourceEvent(
            resource_id=self.id,
            action="combine",
            old_value=self._quantity,
            new_value=total_quantity,
            quality_change=new_quality - self._quality
        ))
        
        return Resource(
            self._type,
            self._properties,
            total_quantity,
            new_quality
        )
    
    def split(self, quantity: float) -> Tuple['Resource', 'Resource']:
        """Split this resource into two parts."""
        if quantity > self._quantity:
            raise ValueError(f"Cannot split more than available: {quantity} > {self._quantity}")
        
        remaining = Resource(
            self._type,
            self._properties,
            self._quantity - quantity,
            self._quality
        )
        
        split = Resource(
            self._type,
            self._properties,
            quantity,
            self._quality
        )
        
        return split, remaining

class ResourceManager:
    """Manages all resources in the game."""
    def __init__(self):
        self._storage: Dict[ResourceType, Resource] = {}
        self._storage_capacity = 1000.0
        self._properties = self._initialize_properties()
    
    def _initialize_properties(self) -> Dict[ResourceType, ResourceProperties]:
        """Initialize resource properties."""
        return {
            # Basic resources
            ResourceType.WOOD: ResourceProperties(
                name="Wood",
                category=ResourceCategory.BASIC,
                base_value=1.0,
                decay_rate=0.0,
                quality_impact=0.5,
                stackable=True,
                max_stack=100,
                weight=2.0
            ),
            ResourceType.STONE: ResourceProperties(
                name="Stone",
                category=ResourceCategory.BASIC,
                base_value=1.0,
                decay_rate=0.0,
                quality_impact=0.3,
                stackable=True,
                max_stack=100,
                weight=3.0
            ),
            ResourceType.METAL: ResourceProperties(
                name="Metal",
                category=ResourceCategory.BASIC,
                base_value=2.0,
                decay_rate=0.0,
                quality_impact=0.7,
                stackable=True,
                max_stack=50,
                weight=4.0
            ),
            ResourceType.HERBS: ResourceProperties(
                name="Herbs",
                category=ResourceCategory.BASIC,
                base_value=2.0,
                decay_rate=0.1,
                quality_impact=0.8,
                stackable=True,
                max_stack=50,
                weight=0.5
            ),
            ResourceType.WATER: ResourceProperties(
                name="Water",
                category=ResourceCategory.BASIC,
                base_value=0.5,
                decay_rate=0.0,
                quality_impact=0.3,
                stackable=True,
                max_stack=100,
                weight=1.0
            ),
            
            # Food resources
            ResourceType.FOOD: ResourceProperties(
                name="Food",
                category=ResourceCategory.FOOD,
                base_value=2.0,
                decay_rate=0.2,
                quality_impact=0.8,
                stackable=True,
                max_stack=50,
                weight=1.0
            ),
            ResourceType.MEAT: ResourceProperties(
                name="Meat",
                category=ResourceCategory.FOOD,
                base_value=3.0,
                decay_rate=0.3,
                quality_impact=0.9,
                stackable=True,
                max_stack=30,
                weight=1.5
            ),
            ResourceType.FISH: ResourceProperties(
                name="Fish",
                category=ResourceCategory.FOOD,
                base_value=2.5,
                decay_rate=0.25,
                quality_impact=0.8,
                stackable=True,
                max_stack=40,
                weight=1.0
            ),
            ResourceType.CROPS: ResourceProperties(
                name="Crops",
                category=ResourceCategory.FOOD,
                base_value=1.5,
                decay_rate=0.15,
                quality_impact=0.7,
                stackable=True,
                max_stack=50,
                weight=1.0
            ),
            ResourceType.SEEDS: ResourceProperties(
                name="Seeds",
                category=ResourceCategory.FOOD,
                base_value=1.0,
                decay_rate=0.05,
                quality_impact=0.6,
                stackable=True,
                max_stack=100,
                weight=0.1
            ),
            
            # Crafting materials
            ResourceType.LEATHER: ResourceProperties(
                name="Leather",
                category=ResourceCategory.CRAFTING,
                base_value=3.0,
                decay_rate=0.05,
                quality_impact=0.7,
                stackable=True,
                max_stack=40,
                weight=1.0
            ),
            ResourceType.CLOTH: ResourceProperties(
                name="Cloth",
                category=ResourceCategory.CRAFTING,
                base_value=2.5,
                decay_rate=0.05,
                quality_impact=0.6,
                stackable=True,
                max_stack=50,
                weight=0.5
            ),
            ResourceType.PAPER: ResourceProperties(
                name="Paper",
                category=ResourceCategory.CRAFTING,
                base_value=1.5,
                decay_rate=0.1,
                quality_impact=0.4,
                stackable=True,
                max_stack=100,
                weight=0.2
            ),
            ResourceType.INK: ResourceProperties(
                name="Ink",
                category=ResourceCategory.CRAFTING,
                base_value=3.0,
                decay_rate=0.1,
                quality_impact=0.5,
                stackable=True,
                max_stack=20,
                weight=0.2
            ),
            ResourceType.GEMS: ResourceProperties(
                name="Gems",
                category=ResourceCategory.CRAFTING,
                base_value=10.0,
                decay_rate=0.0,
                quality_impact=1.0,
                stackable=True,
                max_stack=10,
                weight=0.1
            ),
            ResourceType.GLASS: ResourceProperties(
                name="Glass",
                category=ResourceCategory.CRAFTING,
                base_value=2.0,
                decay_rate=0.0,
                quality_impact=0.8,
                stackable=True,
                max_stack=30,
                weight=1.0
            ),
            
            # Tools and equipment
            ResourceType.TOOLS: ResourceProperties(
                name="Tools",
                category=ResourceCategory.TOOLS,
                base_value=5.0,
                decay_rate=0.1,
                quality_impact=0.9,
                stackable=True,
                max_stack=10,
                weight=2.0
            ),
            ResourceType.WEAPONS: ResourceProperties(
                name="Weapons",
                category=ResourceCategory.TOOLS,
                base_value=8.0,
                decay_rate=0.05,
                quality_impact=1.0,
                stackable=True,
                max_stack=5,
                weight=3.0
            ),
            ResourceType.ARMOR: ResourceProperties(
                name="Armor",
                category=ResourceCategory.TOOLS,
                base_value=10.0,
                decay_rate=0.05,
                quality_impact=1.0,
                stackable=True,
                max_stack=5,
                weight=5.0
            ),
            ResourceType.FURNITURE: ResourceProperties(
                name="Furniture",
                category=ResourceCategory.TOOLS,
                base_value=6.0,
                decay_rate=0.02,
                quality_impact=0.8,
                stackable=True,
                max_stack=5,
                weight=8.0
            ),
            ResourceType.CONTAINERS: ResourceProperties(
                name="Containers",
                category=ResourceCategory.TOOLS,
                base_value=4.0,
                decay_rate=0.02,
                quality_impact=0.6,
                stackable=True,
                max_stack=10,
                weight=2.0
            ),
            
            # Advanced materials
            ResourceType.REFINED_METAL: ResourceProperties(
                name="Refined Metal",
                category=ResourceCategory.ADVANCED,
                base_value=5.0,
                decay_rate=0.0,
                quality_impact=0.9,
                stackable=True,
                max_stack=20,
                weight=3.0
            ),
            ResourceType.REFINED_WOOD: ResourceProperties(
                name="Refined Wood",
                category=ResourceCategory.ADVANCED,
                base_value=3.0,
                decay_rate=0.0,
                quality_impact=0.8,
                stackable=True,
                max_stack=30,
                weight=1.5
            ),
            ResourceType.REFINED_STONE: ResourceProperties(
                name="Refined Stone",
                category=ResourceCategory.ADVANCED,
                base_value=3.0,
                decay_rate=0.0,
                quality_impact=0.7,
                stackable=True,
                max_stack=30,
                weight=2.5
            ),
            ResourceType.REFINED_GEMS: ResourceProperties(
                name="Refined Gems",
                category=ResourceCategory.ADVANCED,
                base_value=20.0,
                decay_rate=0.0,
                quality_impact=1.0,
                stackable=True,
                max_stack=5,
                weight=0.1
            ),
            ResourceType.REFINED_GLASS: ResourceProperties(
                name="Refined Glass",
                category=ResourceCategory.ADVANCED,
                base_value=5.0,
                decay_rate=0.0,
                quality_impact=0.9,
                stackable=True,
                max_stack=15,
                weight=0.8
            ),
            
            # Special resources
            ResourceType.ARTIFACTS: ResourceProperties(
                name="Artifacts",
                category=ResourceCategory.SPECIAL,
                base_value=50.0,
                decay_rate=0.01,
                quality_impact=1.0,
                stackable=True,
                max_stack=1,
                weight=1.0
            ),
            ResourceType.BOOKS: ResourceProperties(
                name="Books",
                category=ResourceCategory.SPECIAL,
                base_value=15.0,
                decay_rate=0.02,
                quality_impact=0.8,
                stackable=True,
                max_stack=10,
                weight=1.0
            ),
            ResourceType.SCROLLS: ResourceProperties(
                name="Scrolls",
                category=ResourceCategory.SPECIAL,
                base_value=20.0,
                decay_rate=0.05,
                quality_impact=0.9,
                stackable=True,
                max_stack=5,
                weight=0.2
            ),
            ResourceType.POTIONS: ResourceProperties(
                name="Potions",
                category=ResourceCategory.SPECIAL,
                base_value=25.0,
                decay_rate=0.1,
                quality_impact=1.0,
                stackable=True,
                max_stack=5,
                weight=0.5
            ),
            ResourceType.DECORATIONS: ResourceProperties(
                name="Decorations",
                category=ResourceCategory.SPECIAL,
                base_value=10.0,
                decay_rate=0.01,
                quality_impact=0.7,
                stackable=True,
                max_stack=10,
                weight=1.0
            ),
            
            # Tools
            ResourceType.AXE: ResourceProperties(
                name="Axe",
                category=ResourceCategory.TOOLS,
                base_value=8.0,
                decay_rate=0.05,
                quality_impact=1.0,
                stackable=True,
                max_stack=5,
                weight=3.0
            ),
            ResourceType.PICKAXE: ResourceProperties(
                name="Pickaxe",
                category=ResourceCategory.TOOLS,
                base_value=8.0,
                decay_rate=0.05,
                quality_impact=1.0,
                stackable=True,
                max_stack=5,
                weight=3.0
            ),
            ResourceType.SHOVEL: ResourceProperties(
                name="Shovel",
                category=ResourceCategory.TOOLS,
                base_value=6.0,
                decay_rate=0.05,
                quality_impact=0.9,
                stackable=True,
                max_stack=5,
                weight=2.5
            ),
            ResourceType.HAMMER: ResourceProperties(
                name="Hammer",
                category=ResourceCategory.TOOLS,
                base_value=7.0,
                decay_rate=0.05,
                quality_impact=0.9,
                stackable=True,
                max_stack=5,
                weight=2.0
            ),
            ResourceType.SAW: ResourceProperties(
                name="Saw",
                category=ResourceCategory.TOOLS,
                base_value=7.0,
                decay_rate=0.05,
                quality_impact=0.9,
                stackable=True,
                max_stack=5,
                weight=2.0
            ),
            ResourceType.MALLET: ResourceProperties(
                name="Mallet",
                category=ResourceCategory.TOOLS,
                base_value=5.0,
                decay_rate=0.05,
                quality_impact=0.8,
                stackable=True,
                max_stack=5,
                weight=1.5
            ),
            ResourceType.SMITHING_HAMMER: ResourceProperties(
                name="Smithing Hammer",
                category=ResourceCategory.TOOLS,
                base_value=10.0,
                decay_rate=0.05,
                quality_impact=1.0,
                stackable=True,
                max_stack=3,
                weight=3.0
            )
        }
    
    def add_resource(self, resource_type: ResourceType, quantity: float, quality: float = 1.0) -> bool:
        """Add resources to storage."""
        if quantity <= 0:
            return False
        
        properties = self._properties.get(resource_type)
        if not properties:
            return False
        
        new_resource = Resource(resource_type, properties, quantity, quality)
        
        if resource_type in self._storage:
            self._storage[resource_type] = self._storage[resource_type].combine(new_resource)
        else:
            self._storage[resource_type] = new_resource
        
        publish_event(ResourceEvent(
            resource_id=new_resource.id,
            action="add",
            new_value=quantity,
            quality_change=quality
        ))
        
        return True
    
    def remove_resource(self, resource_type: ResourceType, quantity: float) -> Tuple[bool, float, float]:
        """Remove resources from storage."""
        if resource_type not in self._storage:
            return False, 0.0, 0.0
        
        resource = self._storage[resource_type]
        if resource.quantity < quantity:
            return False, 0.0, 0.0
        
        split_resource, remaining = resource.split(quantity)
        self._storage[resource_type] = remaining
        
        if remaining.quantity <= 0:
            del self._storage[resource_type]
        
        publish_event(ResourceEvent(
            resource_id=resource.id,
            action="remove",
            old_value=resource.quantity,
            new_value=remaining.quantity
        ))
        
        return True, split_resource.quantity, split_resource.quality
    
    def get_total_weight(self) -> float:
        """Calculate total weight of all stored resources."""
        return sum(
            resource.quantity * self._properties[resource_type].weight
            for resource_type, resource in self._storage.items()
        )
    
    def get_resource_info(self, resource_type: ResourceType) -> Optional[dict]:
        """Get information about a specific resource type."""
        if resource_type not in self._storage:
            return None
        
        resource = self._storage[resource_type]
        properties = self._properties[resource_type]
        
        return {
            "type": resource_type.name,
            "quantity": resource.quantity,
            "quality": resource.quality,
            "value": properties.calculate_value(resource.quantity, resource.quality),
            "weight": properties.weight * resource.quantity
        }
    
    def get_storage_info(self) -> dict:
        """Get information about all stored resources."""
        return {
            "capacity": self._storage_capacity,
            "total_weight": self.get_total_weight(),
            "resources": [
                self.get_resource_info(resource_type)
                for resource_type in self._storage.keys()
            ]
        }
    
    def update(self, time_passed: timedelta, season_effects: dict) -> None:
        """Update resource states based on time passed."""
        for resource_type, resource in list(self._storage.items()):
            properties = self._properties[resource_type]
            
            # Apply decay
            decay = properties.decay_rate * time_passed.total_seconds() / 86400.0  # per day
            if decay > 0:
                decay_modifier = create_modifier("multiply", strength=1.0 - decay)
                self._storage[resource_type] = resource.transform(decay_modifier)
            
            # Apply season effects
            if resource_type.name in season_effects:
                season_modifier = create_modifier(
                    "multiply",
                    strength=season_effects[resource_type.name]
                )
                self._storage[resource_type] = resource.transform(season_modifier)
            
            # Remove empty stacks
            if resource.quantity <= 0:
                del self._storage[resource_type]
    
    def save_state(self) -> dict:
        """Save the current state."""
        return {
            "storage_capacity": self._storage_capacity,
            "resources": {
                resource_type.name: {
                    "quantity": resource.quantity,
                    "quality": resource.quality
                }
                for resource_type, resource in self._storage.items()
            }
        }
    
    def load_state(self, state: dict) -> None:
        """Load a saved state."""
        self._storage_capacity = state.get("storage_capacity", 1000.0)
        self._storage.clear()
        
        for resource_name, data in state.get("resources", {}).items():
            try:
                resource_type = ResourceType[resource_name]
                properties = self._properties[resource_type]
                self._storage[resource_type] = Resource(
                    resource_type,
                    properties,
                    data.get("quantity", 0.0),
                    data.get("quality", 1.0)
                )
            except (KeyError, ValueError) as e:
                logger.error(f"Error loading resource {resource_name}: {e}") 