from logging import Logger, getLogger

logger: Logger = getLogger(__name__)
import json
import re
from bigdata_research_tools.llm.base import (
    REASONING_MODELS,
    LLMConfig,
    LLMEngine,
    AsyncLLMEngine,
)
from bigdata_research_tools.llm.utils import (run_concurrent_prompts, run_parallel_prompts)
from bigdata_research_tools.prompts.lexicon import build_lexicon_prompt

class LexiconGenerator:
    
    def __init__(self, main_theme:str, llm_model_config: str | LLMConfig | dict, mode="keywords", seeds: list|None = [123, 123456, 123456789]):
        """
        Args:
            llm_config (LLMConfig): LLM configuration object (model, api_key, etc)
            seeds (list[int], optional): List of seeds for LLM sampling. Defaults to [123, 123456, 123456789, 456789, 789].
            mode (str): 'keywords' or 'sentences'.
        """
        self.main_theme = main_theme
        self.mode = mode
        self.validate_mode()

        self.seeds = seeds if seeds is not None else [123, 123456, 123456789]
        if isinstance(llm_model_config, dict):
            self.llm_model_config = LLMConfig(**llm_model_config)
        elif isinstance(llm_model_config, str):
            self.llm_model_config = self.get_default_lexicon_config(llm_model_config)
        else:
            self.llm_model_config = llm_model_config

    def validate_mode(self):
        """Validate the mode."""
        if self.mode not in ['keywords', 'sentences']:
            raise ValueError("Mode must be either 'keywords' or 'sentences'.")

    def get_default_lexicon_config(self, model) -> LLMConfig:
        """Get default LLM model configuration for lexicon generation."""
        if any(rm in model for rm in REASONING_MODELS):
            return LLMConfig(
                model=model,
                reasoning_effort="high",
                seed=42,
                response_format={"type": "json_object"},
            )
        else:
            return LLMConfig(
                model=model,
                temperature=0,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                seed=42,
                response_format={"type": "json_object"},
            )
        
    def generate_lexicon(
        self,
        timeout: int | None = 55,
        max_workers: int = 100,
    ) -> list[str]:
        """
        Generate lexicon using LLM prompts.

        Args:
            timeout: Timeout for each LLM request.
            max_workers: Maximum number of concurrent workers.

        Returns:
            List of generated lexicon items.
        """
        system_prompt = build_lexicon_prompt(self.main_theme, mode=self.mode)
        responses = self._run_lexicon_prompts(
            system_prompt,
            timeout=timeout,
            max_workers=max_workers,
        )

        unique_items = self.flatten_responses(responses)

        return unique_items
        
    def _run_lexicon_prompts(
        self,
        system_prompt: str,
        timeout: int | None,
        max_workers: int = 100,
    ) -> list[str]:
        """
        Get the labels from the prompts.

        Args:
            prompts: List of prompts to process
            system_prompt: System prompt for the LLM
            timeout: Timeout for each LLM request for concurrent calls
            max_workers: Maximum number of concurrent workers
            processing_callbacks: Callback function for handling responses
        Returns:
            Dict of parsed responses from the LLM
        """
        llm_kwargs = self.llm_model_config.get_llm_kwargs(
            remove_max_tokens=True, remove_timeout=True
        )

        provider, _ = self.llm_model_config.model.split("::")

        if  (provider == 'bedrock') or (len(self.seeds) == 1):     
            llm = LLMEngine(
                model=self.llm_model_config.model,
                **self.llm_model_config.connection_config,
            )
            
            return run_parallel_prompts(
                llm_engine=llm,
                prompts = [self.main_theme]*len(self.seeds),
                system_prompt=system_prompt,
                processing_callbacks=[self.parse_lexicon_response],
                max_workers=max_workers,
                **llm_kwargs,
            )
        elif (provider != 'bedrock') and (len(self.seeds) > 1):
            llm = AsyncLLMEngine(
                model=self.llm_model_config.model,
                **self.llm_model_config.connection_config,
            )

            return run_concurrent_prompts(
                llm_engine=llm,
                prompts = [self.main_theme]*len(self.seeds),
                system_prompt=system_prompt,
                timeout=timeout,
                processing_callbacks=[self.parse_lexicon_response],
                max_workers=max_workers,
                **llm_kwargs,
            )
        
    def parse_lexicon_response(self, response: str) -> list[str]:
        """
        Parse the response from the LLM model used for lexicon generation.

        Args:
            response: Response string from the LLM.
        Returns:
            List of lexicon items.
        """
        try:
            response = re.sub(r'```', '', response)
            response = re.sub(r'json', '', response)
            parsed = json.loads(response)[self.mode]
            return [item.strip() for item in parsed if item.strip()]
        except json.JSONDecodeError:
            logger.error(f"Error deserializing response: {response}")
            return []

    def flatten_responses(self, responses: list[list[str]]) -> list[str]:
        """
        Flatten the responses from the LLM into a unique list of items.

        Args:
            responses: List of lists of lexicon items from the LLM.
        Returns:
            List of unique lexicon items, preserving order.
        """
        seen = set()
        unique_items = []
        for response_list in responses:
            for item in response_list:
                if item not in seen:
                    seen.add(item)
                    unique_items.append(item)
        return unique_items



        
