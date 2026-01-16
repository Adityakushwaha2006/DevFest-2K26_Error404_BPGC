"""
Scoring Engine: Momentum, Readiness, and Win Probability
The CORE DIFFERENTIATOR of NEXUS - timing intelligence
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from identity_node import IdentityNode, ActivityEvent
import math


class MomentumScorer:
    """
    Calculates momentum score based on activity patterns.
    High momentum = actively engaged, good time to connect.
    """
    
    def __init__(self, decay_factor: float = 0.8):
        """
        Args:
            decay_factor: How quickly old activity loses weight (0-1)
                         0.8 = activity 1 week ago is worth 80% less
        """
        self.decay_factor = decay_factor
    
    def calculate_momentum(self, activities: List[ActivityEvent]) -> float:
        """
        Calculate momentum score from 0-100.
        
        Algorithm:
        - Recent activity gets higher weight
        - More frequent activity = higher score
        - Exponential time decay
        
        Returns:
            Score 0-100 where:
            - 0-30: Dormant (low activity)
            - 30-60: Moderate  
            - 60-80: Active
            - 80-100: Very active (high momentum)
        """
        if not activities:
            return 0.0
        
        now = datetime.now()
        score = 0.0
        
        for activity in activities:
            # Calculate days since activity
            if activity.timestamp.tzinfo is None:
                activity_time = activity.timestamp
            else:
                activity_time = activity.timestamp.replace(tzinfo=None)
            
            days_ago = (now - activity_time).days
            
            # Time decay: older activities count less
            # Using exponential decay: score *= decay^days
            weight = math.pow(self.decay_factor, days_ago)
            
            # Add weighted score
            score += weight
        
        # Normalize to 0-100 scale
        # Assume 30 activities in last week = score 100
        normalized_score = min(100, (score / 30) * 100)
        
        return round(normalized_score, 2)
    
    def get_activity_burst_periods(
        self,
        activities: List[ActivityEvent],
        window_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Identify periods of high activity (bursts).
        
        Returns:
            List of burst periods with start/end dates and intensity
        """
        if not activities:
            return []
        
        # Group activities by day
        daily_counts = {}
        for activity in activities:
            date = activity.timestamp.date()
            daily_counts[date] = daily_counts.get(date, 0) + 1
        
        # Find burst periods (days with >3 activities)
        bursts = []
        for date, count in daily_counts.items():
            if count >= 3:
                bursts.append({
                    'date': date.isoformat(),
                    'activity_count': count,
                    'intensity': 'high' if count >= 5 else 'moderate'
                })
        
        return sorted(bursts, key=lambda x: x['date'], reverse=True)


class ReadinessScorer:
    """
    Calculates readiness score - likelihood of positive response.
    Combines context, timing, and intent signals.
    """
    
    # Default weights (can be adjusted)
    DEFAULT_WEIGHTS = {
        'context': 0.3,    # Shared interests/context
        'timing': 0.5,     # Current activity level
        'intent': 0.2      # Explicit signals (hiring, looking for, etc.)
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS
    
    def calculate_readiness(
        self,
        context_score: float,
        momentum_score: float,
        intent_score: float
    ) -> float:
        """
        Calculate overall readiness score (0-100).
        
        Args:
            context_score: How well your profiles match (0-100)
            momentum_score: Their current activity level (0-100)
            intent_score: Explicit signals they're open to connect (0-100)
        
        Returns:
            Weighted readiness score 0-100
        """
        # Normalize all scores to 0-1
        context_norm = context_score / 100
        momentum_norm = momentum_score / 100
        intent_norm = intent_score / 100
        
        # Calculate weighted sum
        readiness = (
            self.weights['context'] * context_norm +
            self.weights['timing'] * momentum_norm +
            self.weights['intent'] * intent_norm
        )
        
        # Convert back to 0-100 scale
        return round(readiness * 100, 2)
    
    def detect_intent_signals(self, node: IdentityNode) -> float:
        """
        Detect explicit intent signals in bio/recent activity.
        
        Signals:
        - "hiring", "looking for", "open to"
        - "DM me", "let's connect"
        - "available for", "seeking"
        
        Returns:
            Intent score 0-100
        """
        intent_keywords = [
            'hiring', 'looking for', 'seeking', 'open to',
            'available for', 'dm me', 'connect', 'collaboration',
            'opportunities', 'recruiting', 'join', 'help wanted'
        ]
        
        score = 0.0
        
        # Check bio
        bio = (node.get_bio() or '').lower()
        for keyword in intent_keywords:
            if keyword in bio:
                score += 20  # Each keyword in bio = +20 points
        
        # Check recent activities (last 5)
        recent_activities = node.activities[:5]
        for activity in recent_activities:
            content = activity.content.lower()
            for keyword in intent_keywords:
                if keyword in content:
                    score += 10  # Each keyword in activity = +10 points
        
        return min(100, score)


class WinProbabilityCalculator:
    """
    Predicts probability of successful connection.
    The "Magic Feature" - tells you WHEN to connect.
    """
    
    def __init__(self):
        self.momentum_scorer = MomentumScorer()
        self.readiness_scorer = ReadinessScorer()
    
    def calculate_win_probability(
        self,
        node: IdentityNode,
        context_similarity: float = 0.7
    ) -> Dict[str, Any]:
        """
        Calculate probability of successful connection.
        
        Args:
            node: Target's identity node
            context_similarity: How similar you are (0-1)
        
        Returns:
            Dict with probability, recommendation, and reasoning
        """
        # Calculate component scores
        momentum = self.momentum_scorer.calculate_momentum(node.activities)
        intent = self.readiness_scorer.detect_intent_signals(node)
        context = context_similarity * 100
        
        # Calculate readiness
        readiness = self.readiness_scorer.calculate_readiness(
            context_score=context,
            momentum_score=momentum,
            intent_score=intent
        )
        
        # Determine recommendation
        recommendation = self._get_recommendation(momentum, readiness)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(momentum, intent, context, readiness)
        
        return {
            'probability': readiness,
            'momentum_score': momentum,
            'intent_score': intent,
            'context_score': context,
            'recommendation': recommendation,
            'reasoning': reasoning,
            'component_scores': {
                'context': context,
                'timing': momentum,
                'intent': intent
            }
        }
    
    def _get_recommendation(self, momentum: float, readiness: float) -> str:
        """
        Generate action recommendation based on scores.
        """
        if readiness >= 75 and momentum >= 60:
            return "✅ ACT NOW - High engagement window"
        elif readiness >= 50 and momentum >= 40:
            return "⚡ GOOD TIME - Moderately active"
        elif momentum < 30:
            return f"⏸️ WAIT - Low activity (dormant period)"
        elif intent >= 50:
            return "💡 CONSIDER - They're open but not very active"
        else:
            return "⏳ MONITOR - Wait for higher activity"
    
    def _generate_reasoning(
        self,
        momentum: float,
        intent: float,
        context: float,
        readiness: float
    ) -> str:
        """Generate human-readable explanation."""
        reasons = []
        
        # Momentum reasoning
        if momentum >= 70:
            reasons.append("Currently very active")
        elif momentum >= 40:
            reasons.append("Moderately active")
        else:
            reasons.append("Low recent activity")
        
        # Intent reasoning
        if intent >= 50:
            reasons.append("Shows open signals in profile/activity")
        elif intent > 0:
            reasons.append("Some receptivity signals detected")
        
        # Context reasoning
        if context >= 70:
            reasons.append("Strong profile match")
        elif context >= 50:
            reasons.append("Good profile alignment")
        
        return "; ".join(reasons)
    
    def predict_best_time(
        self,
        node: IdentityNode,
        days_ahead: int = 7
    ) -> Optional[str]:
        """
        Predict the best time in the next N days to connect.
        
        Returns:
            ISO date string or None
        """
        # Get activity burst periods
        bursts = self.momentum_scorer.get_activity_burst_periods(node.activities)
        
        if not bursts:
            return None
        
        # Find most recent burst
        latest_burst = bursts[0]
        burst_date = datetime.fromisoformat(latest_burst['date'])
        
        # If burst was in last 2 days, suggest now
        days_since_burst = (datetime.now() - burst_date).days
        
        if days_since_burst <= 2:
            return "now"
        else:
            # Suggest waiting for next likely burst
            # Assume weekly pattern
            next_burst = datetime.now() + timedelta(days=(7 - days_since_burst))
            return next_burst.date().isoformat()
