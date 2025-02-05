from enum import Enum, auto

class ResourceCategory(Enum):
    """Categories of resources."""
    BASIC = auto()
    FOOD = auto()
    CRAFTING = auto()
    TOOLS = auto()
    ADVANCED = auto()
    SPECIAL = auto()

class ResourceType(Enum):
    """Types of resources available in the game."""
    # Basic resources
    WOOD = auto()
    STONE = auto()
    METAL = auto()
    HERBS = auto()
    WATER = auto()
    
    # Food resources
    FOOD = auto()
    MEAT = auto()
    FISH = auto()
    CROPS = auto()
    SEEDS = auto()
    
    # Crafting materials
    LEATHER = auto()
    CLOTH = auto()
    PAPER = auto()
    INK = auto()
    GEMS = auto()
    GLASS = auto()
    
    # Tools and equipment
    TOOLS = auto()
    WEAPONS = auto()
    ARMOR = auto()
    FURNITURE = auto()
    CONTAINERS = auto()
    
    # Advanced materials
    REFINED_METAL = auto()
    REFINED_WOOD = auto()
    REFINED_STONE = auto()
    REFINED_GEMS = auto()
    REFINED_GLASS = auto()
    
    # Special resources
    ARTIFACTS = auto()
    BOOKS = auto()
    SCROLLS = auto()
    POTIONS = auto()
    DECORATIONS = auto()
    
    # Tools
    AXE = auto()
    PICKAXE = auto()
    SHOVEL = auto()
    HAMMER = auto()
    SAW = auto()
    MALLET = auto()
    SMITHING_HAMMER = auto() 