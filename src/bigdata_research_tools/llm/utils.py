import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger, getLogger
from typing import List, Tuple

from openai import APITimeoutError, RateLimitError
from tqdm import tqdm

from bigdata_research_tools.llm.base import AsyncLLMEngine, LLMEngine

logger: Logger = getLogger(__name__)


# https://platform.openai.com/docs/guides/batch
def run_concurrent_prompts(
    llm_engine: AsyncLLMEngine,
    prompts: List[str],
    system_prompt: str,
    max_workers: int = 30,
    **kwargs,
) -> List[str]:
    """
    Run the LLM on the received prompts, concurrently.

    Args:
        llm_engine (AsyncLLMEngine): The LLM engine to use.
        prompts (list[str]): List of prompts to run concurrently.
        system_prompt (str): The system prompt.
        max_workers (int): The maximum number of workers to run concurrently.
        kwargs (dict): Additional arguments to pass to the `get_response` method of the LLMEngine.

    Returns:
        list[str]: The list of responses from the LLM model, each in the same order as the prompts.
    """
    semaphore = asyncio.Semaphore(max_workers)
    logger.info(f"Running {len(prompts)} prompts concurrently")
    tasks = [
        _fetch_with_semaphore(
            idx, llm_engine, semaphore, system_prompt, prompt, **kwargs
        )
        for idx, prompt in enumerate(prompts)
    ]
    return asyncio.run(_run_with_progress_bar(tasks))


async def _fetch_with_semaphore(
    idx: int,
    llm_engine: AsyncLLMEngine,
    semaphore: asyncio.Semaphore,
    system_prompt: str,
    prompt: str,
    **kwargs,
) -> Tuple[int, str]:
    """
    Fetch the response from the LLM engine with a semaphore.

    Args:
        idx (int): The index of the prompt, to keep the original order.
        llm_engine (AsyncLLMEngine): The LLM engine to use.
        semaphore (asyncio.Semaphore): The semaphore to use, to limit the
            number of concurrent requests.
        system_prompt (str): The system prompt.
        prompt (str): The prompt to run.
        kwargs (dict): Additional arguments to pass to the `get_response` method of the LLMEngine.

    Returns:
        Tuple[int, str]: The index of the prompt and the response from the LLM model.
    """
    chat_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    async with semaphore:
        retry_delay = 1  # Initial delay in seconds
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = await llm_engine.get_response(chat_history, **kwargs)
                return idx, response
            except (APITimeoutError, RateLimitError):
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                retry_delay = min(retry_delay * 2, 60)
        logger.error(f"Failed to get response for prompt: {prompt}")
        return idx, ""


async def _run_with_progress_bar(tasks) -> List:
    """Run asyncio tasks with a tqdm progress bar."""
    # Pre-allocate a list for results to preserve order
    results = [None] * len(tasks)
    with tqdm(total=len(tasks), desc="Querying an LLM...") as pbar:
        for coro in asyncio.as_completed(tasks):
            idx, result = await coro
            results[idx] = result
            # Update the progress bar
            pbar.update(1)
    return results


# ADS-140
# Added function to run synchronous LLM calls in parallel using threads.
def run_parallel_prompts(
    llm_engine,
    prompts: List[str],
    system_prompt: str,
    max_workers: int = 30,
    **kwargs,
) -> List[str]:
    """
    Run the LLM on the received prompts concurrently using threads.

    Args:
        llm_engine: The LLM engine with a synchronous get_response method.
        prompts (list[str]): List of prompts to run concurrently.
        system_prompt (str): The system prompt.
        max_workers (int): The maximum number of threads.
        kwargs (dict): Additional arguments for get_response.

    Returns:
        list[str]: Responses in the same order as prompts.
    """

    def fetch(idx, prompt):
        chat_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        retry_delay = 1
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = llm_engine.get_response(chat_history, **kwargs)
                return idx, response
            except (APITimeoutError, RateLimitError):
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
        logger.error(f"Failed to get response for prompt: {prompt}")
        return idx, ""

    results = [None] * len(prompts)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch, idx, prompt) for idx, prompt in enumerate(prompts)
        ]
        for future in tqdm(
            as_completed(futures), total=len(prompts), desc="Querying an LLM..."
        ):
            idx, result = future.result()
            results[idx] = result
    return results
