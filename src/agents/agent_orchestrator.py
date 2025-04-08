from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self, agents: Dict[str, Any]):
        """
        Initialize the agent orchestrator with a dictionary of agents
        
        Args:
            agents: Dictionary of agent instances with keys like 'safety', 'emotion', 'chat', etc.
        """
        self.agents = agents
        self.conversation_history = []
        self.emotion_history = []
        self.safety_history = []
        
        logger.info("AgentOrchestrator initialized with %d agents", len(agents))

    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user message through all agents and return a coordinated response
        
        Args:
            message: The user's message
            context: Optional context information
            
        Returns:
            Dictionary containing the coordinated response
        """
        try:
            # Step 1: Analyze emotions
            emotion_data = await self.agents["emotion"].analyze_emotion(message)
            self.emotion_history.append(emotion_data)
            
            # Step 2: Assess safety
            safety_data = await self.agents["safety"].check_message(message)
            self.safety_history.append(safety_data)
            
            # Step 3: Generate response
            response = await self.agents["chat"].generate_response(
                message=message,
                context={
                    "emotion": emotion_data,
                    "safety": safety_data
                }
            )
            
            # Step 4: Log interaction
            self._log_interaction(message, emotion_data, safety_data, response)
            
            # Step 5: Prepare result
            result = {
                'response': response.get('response', ''),
                'emotion_analysis': emotion_data,
                'safety_assessment': safety_data,
                'timestamp': datetime.now().isoformat(),
                'requires_escalation': safety_data.get('emergency_protocol', False)
            }
            
            # Store in history
            self.conversation_history.append({
                'user_message': message,
                'system_response': result,
                'timestamp': datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                'response': "I apologize, but I'm having trouble processing your message. Please try again.",
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _log_interaction(self, 
                        message: str, 
                        emotion_data: Dict[str, Any], 
                        safety_data: Dict[str, Any], 
                        response: Dict[str, Any]) -> None:
        """Log the interaction details for monitoring and improvement"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': message,
            'emotion_data': emotion_data,
            'safety_data': safety_data,
            'system_response': response
        }
        
        # Log critical safety concerns
        if safety_data.get('emergency_protocol', False):
            logger.warning(f"Emergency protocol activated: {safety_data.get('concerns', [])}")
            
        # Log low confidence analyses
        if emotion_data.get('confidence', 1.0) < 0.5 or safety_data.get('confidence', 1.0) < 0.5:
            logger.warning("Low confidence in analysis", extra=log_entry)
            
        logger.info("Interaction processed successfully", extra=log_entry)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.conversation_history

    def get_emotional_trends(self) -> Dict[str, Any]:
        """Analyze emotional trends from history"""
        if not self.emotion_history:
            return {}
            
        emotions = [h.get('primary_emotion', 'unknown') for h in self.emotion_history]
        intensities = [h.get('intensity', 5) for h in self.emotion_history]
        
        return {
            'primary_emotions': emotions,
            'intensity_trend': intensities,
            'average_intensity': sum(intensities) / len(intensities) if intensities else 0,
            'most_common_emotion': max(set(emotions), key=emotions.count) if emotions else 'unknown'
        }

    def get_safety_summary(self) -> Dict[str, Any]:
        """Get summary of safety assessments"""
        if not self.safety_history:
            return {}
            
        risk_levels = [h.get('risk_level', 'UNKNOWN') for h in self.safety_history]
        protocols = [h.get('emergency_protocol', False) for h in self.safety_history]
        
        return {
            'risk_level_history': risk_levels,
            'emergency_protocols_activated': sum(1 for p in protocols if p),
            'current_risk_level': risk_levels[-1] if risk_levels else 'UNKNOWN'
        } 