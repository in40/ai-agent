"""
LLM-Based Entity Extraction
Uses LM Studio for intelligent entity extraction with custom prompts
"""
import requests
import json
from typing import Dict, List, Any, Optional
import re


class LLMEntityExtractor:
    """
    LLM-based entity extraction using LM Studio
    """
    
    def __init__(self, 
                 base_url: str = None,
                 model: str = None,
                 api_key: Optional[str] = None):
        """
        Initialize LLM entity extractor
        
        Args:
            base_url: LM Studio API base URL (default: from env NLP_LLM_BASE_URL or http://192.168.51.237:1234/v1)
            model: Model name to use (default: from env NLP_LLM_MODEL or Qwen3.5-35B-Thinking)
            api_key: API key (if required)
        """
        import os
        self.base_url = base_url or os.getenv('NLP_LLM_BASE_URL', 'http://192.168.51.237:1234/v1')
        self.model = model or os.getenv('NLP_LLM_MODEL', 'Qwen3.5-35B-Thinking')
        self.api_key = api_key
        self.endpoint = f"{self.base_url}/chat/completions"
        
        # Entity extraction prompt template
        self.extraction_prompt = """You are an expert NLP entity extractor. Your task is to identify and classify named entities in the provided text.

## Entity Types to Extract:
1. **STANDARD**: Technical standards (GOST, ISO, IEC, RFC, NIST, etc.)
   - Examples: "GOST R 34.10-2012", "ISO 27001", "RFC 8446"
   
2. **ORGANIZATION**: Companies, government bodies, agencies, institutions
   - Examples: "FSB Russia", "ISO/IEC", "NIST", "Apple Inc."
   
3. **TECHNOLOGY**: Technical terms, algorithms, protocols, methods
   - Examples: "elliptic curve cryptography", "SHA-256", "AES encryption"
   
4. **LOCATION**: Geographical entities, countries, regions, cities
   - Examples: "Russian Federation", "Moscow", "European Union"
   
5. **CONCEPT**: Domain-specific concepts, abstract ideas
   - Examples: "digital signature", "hash function", "encryption key"
   
6. **PERSON**: People mentioned (full names)
   - Examples: "John Smith", "Jane Doe"
   
7. **DATE**: Dates, times, periods
   - Examples: "2012", "January 2023", "5 years"
   
8. **LAW**: Laws, regulations, policies, directives
   - Examples: "GDPR", "HIPAA", "Federal Law No. 152-FZ"

## Output Format:
Return ONLY valid JSON in this exact format:
{{
  "entities": [
    {{
      "text": "exact text from document",
      "label": "ENTITY_TYPE",
      "start": character_position_start,
      "end": character_position_end,
      "confidence": 0.0-1.0,
      "context": "surrounding context (optional)"
    }}
  ],
  "statistics": {{
    "total_entities": number,
    "by_type": {{
      "STANDARD": count,
      "ORGANIZATION": count,
      ...
    }}
  }}
}}

## Rules:
1. Extract entities EXACTLY as they appear in the text
2. Provide character positions (start and end) for each entity
3. Assign confidence score based on how certain you are (0.0-1.0)
4. If no entities of a type are found, don't include that type in statistics
5. Return ONLY the JSON, no additional text

## Text to Analyze:
{text}
"""
    
    def extract_entities(self, text: str, max_length: int = 4000) -> Dict[str, Any]:
        """
        Extract entities using LLM
        
        Args:
            text: Input text
            max_length: Maximum text length to send (to avoid token limits)
            
        Returns:
            Dictionary with entities and statistics
        """
        # Truncate if necessary
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"
        
        # Prepare prompt
        prompt = self.extraction_prompt.format(text=text)
        
        # Prepare request
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert NLP entity extractor. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent extraction
            "max_tokens": 2000
        }
        
        try:
            # Send request to LM Studio
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON from response
            entities_data = self._parse_json_response(content)
            
            return entities_data
            
        except requests.exceptions.RequestException as e:
            print(f"LLM API request failed: {e}")
            return {"entities": [], "statistics": {"total_entities": 0, "by_type": {}}, "error": str(e)}
        except Exception as e:
            print(f"LLM entity extraction error: {e}")
            return {"entities": [], "statistics": {"total_entities": 0, "by_type": {}}, "error": str(e)}
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response
        
        Args:
            content: Response content (may contain markdown)
            
        Returns:
            Parsed JSON dictionary
        """
        # Remove markdown code blocks if present
        content = re.sub(r'^```json\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
        content = re.sub(r'^```\s*|\s*```$', '', content.strip(), flags=re.MULTILINE)
        
        # Try to find JSON object - look for opening brace
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)
        
        # Clean up common LLM formatting issues
        content = content.replace('\n  "', '\n"')  # Fix indented quotes
        content = content.replace('"\n  "', '",\n"')  # Fix missing commas
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Content preview: {content[:500]}...")
            
            # Try to extract entities array even if JSON is malformed
            entities_match = re.search(r'"entities"\s*:\s*\[([\s\S]*?)\]', content)
            if entities_match:
                print("Found entities array in response")
                return {
                    "entities": [],
                    "statistics": {"total_entities": 0, "by_type": {}},
                    "error": f"Partial parse: {e}",
                    "raw_content": content[:2000]
                }
            
            return {"entities": [], "statistics": {"total_entities": 0, "by_type": {}}, "error": f"JSON parse error: {e}", "raw_content": content[:2000]}
    
    def extract_entities_batch(self, texts: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Extract entities from multiple texts
        
        Args:
            texts: List of texts to analyze
            max_concurrent: Maximum concurrent requests (not implemented yet)
            
        Returns:
            List of extraction results
        """
        results = []
        for i, text in enumerate(texts):
            print(f"Processing text {i+1}/{len(texts)}...")
            result = self.extract_entities(text)
            result["text_index"] = i
            results.append(result)
        return results
    
    def compare_extraction_methods(self, text: str, 
                                   spacy_entities: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Compare LLM extraction with other methods
        
        Args:
            text: Input text
            spacy_entities: Optional spaCy entities for comparison
            
        Returns:
            Comparison results
        """
        llm_result = self.extract_entities(text)
        
        comparison = {
            "llm_entities": len(llm_result.get("entities", [])),
            "spacy_entities": len(spacy_entities) if spacy_entities else 0,
            "llm_types": list(llm_result.get("statistics", {}).get("by_type", {}).keys()),
            "agreement": None
        }
        
        if spacy_entities:
            # Calculate agreement (simple overlap)
            llm_texts = set([e["text"] for e in llm_result.get("entities", [])])
            spacy_texts = set([e["text"] for e in spacy_entities])
            
            if llm_texts and spacy_texts:
                overlap = llm_texts.intersection(spacy_texts)
                comparison["agreement"] = {
                    "overlap_count": len(overlap),
                    "llm_unique": len(llm_texts - spacy_texts),
                    "spacy_unique": len(spacy_texts - llm_texts),
                    "jaccard_similarity": len(overlap) / len(llm_texts.union(spacy_texts))
                }
        
        return comparison


# Singleton instance
_llm_extractor_instance: Optional[LLMEntityExtractor] = None

def get_llm_entity_extractor(
    base_url: str = "http://192.168.51.237:1234/v1",
    model: str = "Qwen3.5-35B-Thinking",  # Updated to Qwen 3.5 35B with 262k context
    api_key: Optional[str] = None
) -> LLMEntityExtractor:
    """Get or create LLM entity extractor instance"""
    global _llm_extractor_instance
    if _llm_extractor_instance is None:
        _llm_extractor_instance = LLMEntityExtractor(base_url, model, api_key)
    return _llm_extractor_instance
