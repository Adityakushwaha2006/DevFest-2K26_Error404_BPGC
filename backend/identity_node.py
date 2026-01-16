"""
Node-Based Identity Resolution System
Core classes for cross-platform identity validation
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class Platform(Enum):
    """Supported platforms for identity nodes"""
    GITHUB = "github"
    TWITTER = "twitter"
    DEVTO = "devto"
    LINKEDIN = "linkedin"
    HASHNODE = "hashnode"


@dataclass
class CrossReference:
    """Represents a link to another platform found in a node"""
    platform: Platform
    identifier: str
    source_field: str  # e.g., "bio", "website", "email"
    confidence: float = 0.0


@dataclass
class ActivityEvent:
    """Single activity event from any platform"""
    platform: Platform
    event_type: str  # "commit", "tweet", "article", "post"
    content: str
    timestamp: datetime
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"


class IdentityNode:
    """
    Represents a single platform identity node.
    Stores data and cross-references to other platforms.
    """
    
    def __init__(self, platform: Platform, identifier: str):
        self.platform = platform
        self.identifier = identifier
        self.data: Dict[str, Any] = {}
        self.cross_references: List[CrossReference] = []
        self.activities: List[ActivityEvent] = []
        self.confidence_score: float = 0.0
        self.last_updated: Optional[datetime] = None
        self.fetch_status: str = "pending"  # "pending", "success", "failed"
        self.error_message: Optional[str] = None
        
    def add_cross_reference(self, platform: Platform, identifier: str, source_field: str):
        """Add a reference to another platform"""
        cross_ref = CrossReference(
            platform=platform,
            identifier=identifier,
            source_field=source_field
        )
        self.cross_references.append(cross_ref)
        
    def add_activity(self, activity: ActivityEvent):
        """Add an activity event to this node"""
        self.activities.append(activity)
        
    def get_name(self) -> Optional[str]:
        """Extract name from data (platform-agnostic)"""
        return self.data.get('name') or self.data.get('full_name')
    
    def get_bio(self) -> Optional[str]:
        """Extract bio/description from data"""
        return (self.data.get('bio') or 
                self.data.get('description') or 
                self.data.get('summary'))
    
    def get_location(self) -> Optional[str]:
        """Extract location from data"""
        return self.data.get('location')
    
    def get_company(self) -> Optional[str]:
        """Extract company/organization from data"""
        return self.data.get('company') or self.data.get('organization')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for JSON serialization"""
        return {
            'platform': self.platform.value,
            'identifier': self.identifier,
            'data': self.data,
            'cross_references': [
                {
                    'platform': ref.platform.value,
                    'identifier': ref.identifier,
                    'source_field': ref.source_field,
                    'confidence': ref.confidence
                }
                for ref in self.cross_references
            ],
            'activities': [
                {
                    'platform': act.platform.value,
                    'event_type': act.event_type,
                    'content': act.content,
                    'timestamp': act.timestamp.isoformat(),
                    'url': act.url,
                    'metadata': act.metadata,
                    'sentiment': act.sentiment
                }
                for act in self.activities
            ],
            'confidence_score': self.confidence_score,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'fetch_status': self.fetch_status
        }


class IdentityGraph:
    """
    Manages multiple IdentityNode instances and validates them against each other.
    """
    
    def __init__(self):
        self.nodes: Dict[str, IdentityNode] = {}  # Key: "platform:identifier"
        self.unified_profile: Optional[Dict[str, Any]] = None
        
    def add_node(self, node: IdentityNode) -> str:
        """Add a node to the graph and return its key"""
        key = f"{node.platform.value}:{node.identifier}"
        self.nodes[key] = node
        return key
    
    def get_node(self, platform: Platform, identifier: str) -> Optional[IdentityNode]:
        """Retrieve a node by platform and identifier"""
        key = f"{platform.value}:{identifier}"
        return self.nodes.get(key)
    
    def calculate_cross_validation_score(self) -> float:
        """
        Calculate overall identity confidence based on cross-references.
        Returns 0.0 to 1.0
        """
        if len(self.nodes) < 2:
            return 0.5  # Single node, moderate confidence
        
        total_score = 0.0
        comparisons = 0
        
        nodes_list = list(self.nodes.values())
        
        # Compare each pair of nodes
        for i, node1 in enumerate(nodes_list):
            for node2 in nodes_list[i+1:]:
                score = self._compare_nodes(node1, node2)
                total_score += score
                comparisons += 1
        
        return total_score / comparisons if comparisons > 0 else 0.0
    
    def _compare_nodes(self, node1: IdentityNode, node2: IdentityNode) -> float:
        """Compare two nodes and return similarity score"""
        score = 0.0
        
        # 1. Name matching (30%)
        if node1.get_name() and node2.get_name():
            if self._fuzzy_match(node1.get_name(), node2.get_name()):
                score += 0.3
        
        # 2. Bidirectional cross-references (40%)
        if self._has_bidirectional_reference(node1, node2):
            score += 0.4
        
        # 3. Location/Company matching (20%)
        if node1.get_location() and node2.get_location():
            if self._fuzzy_match(node1.get_location(), node2.get_location()):
                score += 0.1
        
        if node1.get_company() and node2.get_company():
            if self._fuzzy_match(node1.get_company(), node2.get_company()):
                score += 0.1
        
        # 4. Bio keyword overlap (10%)
        if node1.get_bio() and node2.get_bio():
            if self._keyword_overlap(node1.get_bio(), node2.get_bio()) > 0.5:
                score += 0.1
        
        return score
    
    def _fuzzy_match(self, str1: str, str2: str) -> bool:
        """Simple fuzzy string matching"""
        # Normalize: lowercase, remove special chars
        s1 = ''.join(c.lower() for c in str1 if c.isalnum() or c.isspace())
        s2 = ''.join(c.lower() for c in str2 if c.isalnum() or c.isspace())
        
        # Check if one contains the other or if they're very similar
        return (s1 in s2 or s2 in s1 or s1 == s2)
    
    def _keyword_overlap(self, bio1: str, bio2: str) -> float:
        """Calculate keyword overlap between two bios"""
        words1 = set(bio1.lower().split())
        words2 = set(bio2.lower().split())
        
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        words1 -= stopwords
        words2 -= stopwords
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _has_bidirectional_reference(self, node1: IdentityNode, node2: IdentityNode) -> bool:
        """Check if two nodes reference each other"""
        # Check if node1 references node2's platform with node2's identifier
        node1_refs_node2 = any(
            ref.platform == node2.platform and 
            ref.identifier.lower() == node2.identifier.lower()
            for ref in node1.cross_references
        )
        
        # Check if node2 references node1's platform with node1's identifier
        node2_refs_node1 = any(
            ref.platform == node1.platform and 
            ref.identifier.lower() == node1.identifier.lower()
            for ref in node2.cross_references
        )
        
        return node1_refs_node2 or node2_refs_node1
    
    def synthesize_profile(self) -> Dict[str, Any]:
        """
        Combine all nodes into a unified profile with aggregated activities.
        """
        if not self.nodes:
            return {}
        
        # Calculate overall confidence
        overall_confidence = self.calculate_cross_validation_score()
        
        # Get the most complete node (highest data fields)
        primary_node = max(self.nodes.values(), key=lambda n: len(n.data))
        
        # Aggregate all activities and sort by timestamp
        all_activities = []
        for node in self.nodes.values():
            all_activities.extend(node.activities)
        
        all_activities.sort(key=lambda a: a.timestamp, reverse=True)
        
        # Build unified profile
        unified = {
            'name': primary_node.get_name(),
            'bio': primary_node.get_bio(),
            'location': primary_node.get_location(),
            'company': primary_node.get_company(),
            'overall_confidence': overall_confidence,
            'platforms': {
                node.platform.value: {
                    'identifier': node.identifier,
                    'confidence': node.confidence_score,
                    'data': node.data
                }
                for node in self.nodes.values()
            },
            'aggregated_activity': [
                {
                    'platform': act.platform.value,
                    'event_type': act.event_type,
                    'content': act.content,
                    'timestamp': act.timestamp.isoformat(),
                    'url': act.url,
                    'sentiment': act.sentiment
                }
                for act in all_activities[:50]  # Limit to most recent 50
            ],
            'last_updated': datetime.now().isoformat()
        }
        
        self.unified_profile = unified
        return unified
    
    def to_dict(self) -> Dict[str, Any]:
        """Export entire graph as dictionary"""
        return {
            'nodes': {key: node.to_dict() for key, node in self.nodes.items()},
            'unified_profile': self.unified_profile or self.synthesize_profile()
        }
