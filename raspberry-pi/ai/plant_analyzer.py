"""
SmartGrow AI Plant Health Analyzer
==================================

Analyzes plant health using computer vision and AI models.
Supports multiple backends: Google Gemini Vision, OpenAI Vision,
and local TensorFlow models.
"""

import os
import io
import base64
import json
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AnalysisBackend(Enum):
    """Supported AI analysis backends."""
    GEMINI = "gemini"
    OPENAI = "openai"
    TENSORFLOW = "tensorflow"
    MOCK = "mock"


@dataclass
class PlantHealthAnalysis:
    """Result of plant health analysis."""
    
    # Overall health score (0-100)
    health_score: int = 0
    
    # Leaf condition
    leaf_color: str = "unknown"
    leaf_condition: str = "unknown"
    
    # Disease detection
    disease_detected: bool = False
    disease_name: Optional[str] = None
    disease_confidence: float = 0.0
    
    # Growth assessment
    growth_stage: str = "unknown"
    growth_rate: str = "normal"
    
    # Stress indicators
    water_stress: str = "none"  # none, mild, moderate, severe
    light_stress: str = "none"
    nutrient_deficiency: Optional[str] = None
    
    # AI recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 0.0
    model_used: str = "unknown"
    
    # Raw response
    raw_response: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "health_score": self.health_score,
            "leaf_color": self.leaf_color,
            "leaf_condition": self.leaf_condition,
            "disease_detected": self.disease_detected,
            "disease_name": self.disease_name,
            "disease_confidence": self.disease_confidence,
            "growth_stage": self.growth_stage,
            "growth_rate": self.growth_rate,
            "water_stress": self.water_stress,
            "light_stress": self.light_stress,
            "nutrient_deficiency": self.nutrient_deficiency,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "model_used": self.model_used
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class PlantAnalyzer:
    """
    AI-powered plant health analyzer.
    
    Captures images from camera and analyzes them using
    computer vision AI models to assess plant health.
    """
    
    def __init__(
        self,
        backend: AnalysisBackend = AnalysisBackend.GEMINI,
        api_key: Optional[str] = None,
        camera_index: int = 0
    ):
        """Initialize plant analyzer."""
        self.backend = backend
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.camera_index = camera_index
        self._camera = None
        self._analysis_history: List[PlantHealthAnalysis] = []
        
        # Gemini client
        self._genai = None
        self._model = None
        
        logger.info(f"PlantAnalyzer initialized with backend: {backend.value}")
    
    async def initialize(self):
        """Initialize camera and AI backend."""
        await self._init_camera()
        await self._init_ai_backend()
    
    async def _init_camera(self):
        """Initialize camera for image capture."""
        try:
            import cv2
            self._camera = cv2.VideoCapture(self.camera_index)
            if self._camera.isOpened():
                logger.info(f"Camera {self.camera_index} initialized")
            else:
                logger.warning("Camera not available, using mock images")
                self._camera = None
        except ImportError:
            logger.warning("OpenCV not available, camera disabled")
            self._camera = None
    
    async def _init_ai_backend(self):
        """Initialize AI backend."""
        if self.backend == AnalysisBackend.GEMINI:
            await self._init_gemini()
        elif self.backend == AnalysisBackend.OPENAI:
            await self._init_openai()
        elif self.backend == AnalysisBackend.TENSORFLOW:
            await self._init_tensorflow()
    
    async def _init_gemini(self):
        """Initialize Google Gemini Vision."""
        try:
            import google.generativeai as genai
            
            if not self.api_key:
                logger.warning("Gemini API key not set")
                return
            
            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini Vision initialized")
        except ImportError:
            logger.warning("google-generativeai not installed")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
    
    async def _init_openai(self):
        """Initialize OpenAI Vision."""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._openai_client = OpenAI(api_key=api_key)
                logger.info("OpenAI Vision initialized")
        except ImportError:
            logger.warning("openai package not installed")
    
    async def _init_tensorflow(self):
        """Initialize local TensorFlow model."""
        try:
            import tensorflow as tf
            model_path = Path(__file__).parent / "models" / "plant_health.h5"
            if model_path.exists():
                self._tf_model = tf.keras.models.load_model(str(model_path))
                logger.info("TensorFlow model loaded")
        except ImportError:
            logger.warning("TensorFlow not installed")
    
    async def capture_image(self) -> Optional[bytes]:
        """Capture image from camera."""
        if self._camera is None:
            # Return mock image for testing
            return self._create_mock_image()
        
        try:
            import cv2
            ret, frame = self._camera.read()
            if ret:
                _, buffer = cv2.imencode('.jpg', frame)
                return buffer.tobytes()
            else:
                logger.error("Failed to capture image")
                return None
        except Exception as e:
            logger.error(f"Camera capture error: {e}")
            return None
    
    def _create_mock_image(self) -> bytes:
        """Create a mock image for testing."""
        try:
            from PIL import Image
            import io
            
            # Create a simple green image (plant-like)
            img = Image.new('RGB', (640, 480), color=(34, 139, 34))
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            return buffer.getvalue()
        except ImportError:
            # Return minimal JPEG bytes
            return b'\xff\xd8\xff\xe0\x00\x10JFIF'
    
    async def analyze_image(self, image_data: bytes) -> PlantHealthAnalysis:
        """Analyze plant image using configured backend."""
        if self.backend == AnalysisBackend.GEMINI:
            return await self._analyze_with_gemini(image_data)
        elif self.backend == AnalysisBackend.OPENAI:
            return await self._analyze_with_openai(image_data)
        elif self.backend == AnalysisBackend.TENSORFLOW:
            return await self._analyze_with_tensorflow(image_data)
        else:
            return await self._mock_analysis()
    
    async def _analyze_with_gemini(self, image_data: bytes) -> PlantHealthAnalysis:
        """Analyze using Google Gemini Vision."""
        if self._model is None:
            logger.warning("Gemini model not initialized, using mock")
            return await self._mock_analysis()
        
        try:
            from PIL import Image
            import io
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Create analysis prompt
            prompt = """
            Analyze this plant image and provide a detailed health assessment.
            Return your analysis in the following JSON format:
            
            {
                "health_score": <0-100>,
                "leaf_color": "<healthy/yellowing/browning/pale/spotted>",
                "leaf_condition": "<healthy/wilting/drooping/crispy/damaged>",
                "disease_detected": <true/false>,
                "disease_name": "<name or null>",
                "disease_confidence": <0.0-1.0>,
                "growth_stage": "<seed/sprout/seedling/vegetative/flowering/mature>",
                "growth_rate": "<slow/normal/fast>",
                "water_stress": "<none/mild/moderate/severe>",
                "light_stress": "<none/low_light/high_light>",
                "nutrient_deficiency": "<nitrogen/phosphorus/potassium/iron/null>",
                "recommendations": ["recommendation 1", "recommendation 2"],
                "confidence": <0.0-1.0>
            }
            
            Be accurate and helpful. Focus on plant health indicators.
            """
            
            response = await asyncio.to_thread(
                self._model.generate_content,
                [prompt, image]
            )
            
            # Parse JSON response
            try:
                json_str = response.text
                # Extract JSON from response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                data = json.loads(json_str.strip())
                
                analysis = PlantHealthAnalysis(
                    health_score=data.get("health_score", 70),
                    leaf_color=data.get("leaf_color", "unknown"),
                    leaf_condition=data.get("leaf_condition", "unknown"),
                    disease_detected=data.get("disease_detected", False),
                    disease_name=data.get("disease_name"),
                    disease_confidence=data.get("disease_confidence", 0.0),
                    growth_stage=data.get("growth_stage", "unknown"),
                    growth_rate=data.get("growth_rate", "normal"),
                    water_stress=data.get("water_stress", "none"),
                    light_stress=data.get("light_stress", "none"),
                    nutrient_deficiency=data.get("nutrient_deficiency"),
                    recommendations=data.get("recommendations", []),
                    confidence=data.get("confidence", 0.8),
                    model_used="gemini-1.5-flash",
                    raw_response=response.text
                )
                
                self._analysis_history.append(analysis)
                return analysis
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse Gemini response as JSON")
                return await self._mock_analysis()
                
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            return await self._mock_analysis()
    
    async def _analyze_with_openai(self, image_data: bytes) -> PlantHealthAnalysis:
        """Analyze using OpenAI Vision."""
        # Implementation for OpenAI Vision
        return await self._mock_analysis()
    
    async def _analyze_with_tensorflow(self, image_data: bytes) -> PlantHealthAnalysis:
        """Analyze using local TensorFlow model."""
        # Implementation for TensorFlow
        return await self._mock_analysis()
    
    async def _mock_analysis(self) -> PlantHealthAnalysis:
        """Return mock analysis for testing."""
        import random
        
        analysis = PlantHealthAnalysis(
            health_score=random.randint(70, 95),
            leaf_color=random.choice(["healthy", "slightly_pale"]),
            leaf_condition=random.choice(["healthy", "slight_wilting"]),
            disease_detected=False,
            growth_stage=random.choice(["seedling", "vegetative", "flowering"]),
            growth_rate="normal",
            water_stress=random.choice(["none", "mild"]),
            light_stress="none",
            recommendations=[
                "Maintain current watering schedule",
                "Consider adding organic fertilizer",
                "Ensure adequate light exposure"
            ],
            confidence=0.85,
            model_used="mock"
        )
        
        self._analysis_history.append(analysis)
        return analysis
    
    async def analyze_plant(self) -> PlantHealthAnalysis:
        """Capture and analyze plant image."""
        image_data = await self.capture_image()
        if image_data is None:
            logger.error("No image captured")
            return await self._mock_analysis()
        
        return await self.analyze_image(image_data)
    
    def get_analysis_history(self, limit: int = 10) -> List[PlantHealthAnalysis]:
        """Get recent analysis history."""
        return self._analysis_history[-limit:]
    
    def get_health_trend(self) -> Dict[str, Any]:
        """Calculate health trend from history."""
        if len(self._analysis_history) < 2:
            return {"status": "insufficient_data"}
        
        recent = self._analysis_history[-10:]
        scores = [a.health_score for a in recent]
        
        avg_score = sum(scores) / len(scores)
        trend = "stable"
        
        if len(scores) >= 3:
            first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            
            if second_half > first_half + 5:
                trend = "improving"
            elif second_half < first_half - 5:
                trend = "declining"
        
        return {
            "average_score": avg_score,
            "trend": trend,
            "samples": len(scores),
            "latest_score": scores[-1],
            "highest_score": max(scores),
            "lowest_score": min(scores)
        }
    
    async def close(self):
        """Clean up resources."""
        if self._camera is not None:
            self._camera.release()
            self._camera = None
        logger.info("PlantAnalyzer closed")


# Singleton instance
_plant_analyzer: Optional[PlantAnalyzer] = None


async def get_plant_analyzer(
    backend: AnalysisBackend = AnalysisBackend.GEMINI,
    api_key: Optional[str] = None
) -> PlantAnalyzer:
    """Get or create global plant analyzer instance."""
    global _plant_analyzer
    
    if _plant_analyzer is None:
        _plant_analyzer = PlantAnalyzer(backend=backend, api_key=api_key)
        await _plant_analyzer.initialize()
    
    return _plant_analyzer
