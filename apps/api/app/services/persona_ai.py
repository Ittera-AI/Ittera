import json
from typing import List, Any
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from app.config import settings
from app.models.persona import PersonaDocument, PersonaProfile, PersonaInsight
from app.schemas.persona import AIPersonaExtraction

class PersonaAIService:
    @staticmethod
    async def extract_persona(db: Session, persona_profile: PersonaProfile, documents: List[PersonaDocument]) -> AIPersonaExtraction:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured.")
        
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        system_prompt = """
        You are an expert content strategist and AI persona builder.
        Your goal is to analyze provided documents (like public X profiles, websites) and extract a structured content persona.
        Be specific and practical. Do not invent facts.
        If data is missing, note it in missing_information.
        Distinguish between confirmed facts and inferred insights.
        Build the persona for content strategy, not for invasive profiling.
        Avoid sensitive attribute inference such as religion, caste, health, sexuality, political affiliation, or ethnicity unless explicitly provided.
        """
        
        user_content = f"Target Audience (provided by user): {persona_profile.target_audience or 'Not provided'}\n"
        user_content += f"Niche/Industry (provided by user): {persona_profile.niche or 'Not provided'}\n"
        user_content += f"Goals (provided by user): {', '.join(persona_profile.goals) if persona_profile.goals else 'Not provided'}\n\n"
        
        user_content += "Here are the scraped source documents:\n"
        for doc in documents:
            user_content += f"--- Source URL: {doc.url} ---\n"
            user_content += f"Title: {doc.title}\n"
            user_content += f"Description: {doc.description}\n"
            user_content += f"Content: {doc.clean_text[:5000]}\n"  # Limit each doc to prevent token overflow
            user_content += "---\n\n"
            
        try:
            response = await client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format=AIPersonaExtraction
            )
            
            result = response.choices[0].message.parsed
            if not result:
                raise ValueError("Failed to parse AI output into structured format.")
            return result
            
        except Exception as e:
            raise ValueError(f"AI Persona extraction failed: {str(e)}")
