from openai import OpenAI
from typing import Optional
from app.core.config import settings

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: str = "vivid"
    ) -> str:
        """Genera immagine con DALL-E 3"""
        
        # Enhance prompt for better results
        enhanced_prompt = f"""Professional social media visual: {prompt}
Style: Modern, clean, professional, suitable for business social media.
No text overlays, no watermarks."""
        
        response = self.client.images.generate(
            model="dall-e-3",
            prompt=enhanced_prompt,
            size=size,
            quality="standard",
            style=style,
            n=1
        )
        
        return response.data[0].url
    
    async def generate_image_variation(
        self,
        image_url: str,
        prompt: str
    ) -> str:
        """Genera variazione di un'immagine esistente"""
        # DALL-E 3 doesn't support variations directly
        # Use the prompt to generate a new similar image
        return await self.generate_image(prompt)
