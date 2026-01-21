import os
import json
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """
    A class to manage system prompts stored in external files.
    This allows for easy editing of prompts without changing code.
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        """
        Initialize the PromptManager with a directory containing prompt files.
        
        Args:
            prompts_dir: Directory where prompt files are stored (default: "prompts")
        """
        self.prompts_dir = Path(prompts_dir)
        self._prompts_cache: Dict[str, str] = {}
        
        # Create the prompts directory if it doesn't exist
        self.prompts_dir.mkdir(exist_ok=True)
        
        # Load all prompts on initialization
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt files from the prompts directory."""
        for prompt_file in self.prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self._prompts_cache[prompt_name] = f.read()
                logger.info(f"Loaded prompt: {prompt_name}")
            except Exception as e:
                logger.error(f"Failed to load prompt from {prompt_file}: {e}")
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Get a prompt by name.
        
        Args:
            prompt_name: Name of the prompt (without extension)
            
        Returns:
            The prompt text if found, None otherwise
        """
        return self._prompts_cache.get(prompt_name)
    
    def update_prompt(self, prompt_name: str, new_content: str) -> bool:
        """
        Update a prompt file with new content.
        
        Args:
            prompt_name: Name of the prompt (without extension)
            new_content: New content for the prompt
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prompt_file = self.prompts_dir / f"{prompt_name}.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Update the cache
            self._prompts_cache[prompt_name] = new_content
            logger.info(f"Updated prompt: {prompt_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update prompt {prompt_name}: {e}")
            return False
    
    def list_prompts(self) -> list:
        """
        List all available prompts.
        
        Returns:
            List of prompt names
        """
        return list(self._prompts_cache.keys())
    
    def create_prompt(self, prompt_name: str, content: str) -> bool:
        """
        Create a new prompt file.
        
        Args:
            prompt_name: Name of the prompt (without extension)
            content: Content for the new prompt
            
        Returns:
            True if successful, False otherwise
        """
        if prompt_name in self._prompts_cache:
            logger.warning(f"Prompt {prompt_name} already exists")
            return False
        
        return self.update_prompt(prompt_name, content)
    
    def delete_prompt(self, prompt_name: str) -> bool:
        """
        Delete a prompt file.
        
        Args:
            prompt_name: Name of the prompt (without extension)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prompt_file = self.prompts_dir / f"{prompt_name}.txt"
            if prompt_file.exists():
                prompt_file.unlink()
                
                # Remove from cache
                if prompt_name in self._prompts_cache:
                    del self._prompts_cache[prompt_name]
                
                logger.info(f"Deleted prompt: {prompt_name}")
                return True
            else:
                logger.warning(f"Prompt {prompt_name} does not exist")
                return False
        except Exception as e:
            logger.error(f"Failed to delete prompt {prompt_name}: {e}")
            return False