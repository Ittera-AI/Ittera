import json
import re
from typing import List, Any
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from app.config import settings
from app.models.persona import PersonaDocument, PersonaProfile
from app.schemas.persona import AIPersonaExtraction

class PersonaAIService:
    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if code_block:
            try:
                return json.loads(code_block.group(1).strip())
            except json.JSONDecodeError:
                pass

        obj = re.search(r"\{[\s\S]*\}", text)
        if obj:
            return json.loads(obj.group(0))

        raise ValueError("AI response did not contain valid JSON.")

    @staticmethod
    async def extract_persona(db: Session, persona_profile: PersonaProfile, documents: List[PersonaDocument]) -> AIPersonaExtraction:
        if not settings.AIML_API_KEY:
            raise ValueError("AIML_API_KEY is not configured.")
        
        client_kwargs: dict[str, Any] = {"api_key": settings.AIML_API_KEY}
        if settings.AIML_BASE_URL:
            client_kwargs["base_url"] = settings.AIML_BASE_URL
        client = AsyncOpenAI(**client_kwargs)
        
        system_prompt = """
        You are an expert content strategist and AI persona builder.
        Your goal is to analyze provided documents (like public X profiles, websites) and extract a structured content persona.
        Be specific and practical. Do not invent facts.
        If data is missing, note it in missing_information.
        Distinguish between confirmed facts and inferred insights.
        Build the persona for content strategy, not for invasive profiling.
        Avoid sensitive attribute inference such as religion, caste, health, sexuality, political affiliation, or ethnicity unless explicitly provided.
        Return only valid JSON matching this schema:
        {schema}
        """.format(schema=json.dumps(AIPersonaExtraction.model_json_schema(), indent=2))
        
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
            response = await client.chat.completions.create(
                model=settings.AIML_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                max_tokens=2500,
            )
            
            raw = response.choices[0].message.content or ""
            data = PersonaAIService._extract_json(raw)
            result = AIPersonaExtraction.model_validate(data)
            if not result:
                raise ValueError("Failed to parse AI output into structured format.")
            return result
            
        except Exception as e:
            raise ValueError(f"AI Persona extraction failed: {str(e)}")
