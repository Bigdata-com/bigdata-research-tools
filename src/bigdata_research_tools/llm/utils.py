import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger, getLogger
from typing import Any, Coroutine

from tqdm import tqdm

from bigdata_research_tools.llm.base import AsyncLLMEngine

logger: Logger = getLogger(__name__)


# https://platform.openai.com/docs/guides/batch
def run_concurrent_prompts(
    llm_engine: AsyncLLMEngine,
    prompts: list[str],
    system_prompt: str,
    timeout: int | None,
    max_workers: int = 30,
    callback: Any = None,
    **kwargs,
) -> dict:
    """
    Run the LLM on the received prompts, concurrently.

    Args:
        llm_engine (AsyncLLMEngine): The LLM engine to use.
        prompts (list[str]): List of prompts to run concurrently.
        system_prompt (str): The system prompt.
        timeout (int | None): Timeout for each LLM request.
        max_workers (int): The maximum number of workers to run concurrently.
        kwargs (dict): Additional arguments to pass to the `get_response` method of the LLMEngine.

    Returns:
        dict: The dictionary of parsed responses from the LLM model, each keyed by the prompt index.
    """
    semaphore = asyncio.Semaphore(max_workers)
    logger.info(f"Running {len(prompts)} prompts concurrently")
    tasks = [
        _fetch_with_semaphore(
            idx, llm_engine, semaphore, system_prompt, prompt, timeout=timeout, callback=callback, **kwargs
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
    timeout: int | None,
    callback: Any = None,
    **kwargs,
) -> tuple[int, dict]:
    """
    Fetch the response from the LLM engine with a semaphore.

    Args:
        idx (int): The index of the prompt, to keep the original order.
        llm_engine (AsyncLLMEngine): The LLM engine to use.
        semaphore (asyncio.Semaphore): The semaphore to use, to limit the
            number of concurrent requests.
        system_prompt (str): The system prompt.
        prompt (str): The prompt to run.
        timeout (int | None): Timeout for the LLM request.
        callback (Any): Optional callback function to be called with the index and response for each prompt.
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
        last_exception = None
        for attempt in range(max_retries):
            try:
                # Sometimes, the LLM (often OpenAI) can take up to ten minutes to respond without throwing an error,
                # retrying after a prudential timeout avoids this situation.
                # A first analysis show that:
                # from 5k requests
                # ~20 took longer than 10 seconds
                # ~10 took longer than 30 seconds
                # ~3 took longer than 60 seconds, with up to 600 seconds
                async with asyncio.timeout(timeout):
                    response = await llm_engine.get_response(chat_history, **kwargs)
                    if callback is not None:
                        for func in callback:
                            response = func(response)
                return idx, response
            except Exception as e:
                if isinstance(e, asyncio.TimeoutError) and attempt == 0:
                    logger.warning(
                        f"Timeout occurred for prompt during LLM call, current timeout configured {timeout} seconds. If this keeps happening (> 1% of your requests), consider increasing the timeout. Retrying..."
                    )
                elif isinstance(e, ValueError):
                    logger.warning(
                        f"Error occurred for response validation during LLM call. Retrying..."
                    )
                last_exception = e
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                retry_delay = min(retry_delay * 2, 60)
        logger.error(
            f"Failed to get response for prompt: {prompt} Error: {last_exception}"
        )
        return idx, {}


async def _run_with_progress_bar(
    tasks: list[Coroutine[Any, Any, tuple[int, dict]]],
) -> dict:
    """Run asyncio tasks with a tqdm progress bar."""
    # Pre-allocate a list for results to preserve order
    results = {} #""] * len(tasks)
    with tqdm(total=len(tasks), desc="Querying an LLM...") as pbar:
        for coro in asyncio.as_completed(tasks):
            idx, result = await coro
            #results[idx] = result
            results.update(result)
            # Update the progress bar
            pbar.update(1)

    return results

# ADS-140
# Added function to run synchronous LLM calls in parallel using threads.
def run_parallel_prompts(
    llm_engine,
    prompts: list[str],
    system_prompt: str,
    max_workers: int = 30,
    callback: Any = None,
    **kwargs,
) -> list[str]:
    """
    Run the LLM on the received prompts concurrently using threads.

    Args:
        llm_engine: The LLM engine with a synchronous get_response method.
        prompts (list[str]): List of prompts to run concurrently.
        system_prompt (str): The system prompt.
        max_workers (int): The maximum number of threads.
        callback (Any): Optional callback function to be called with the index and response for each prompt.
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
        last_exception = None
        for attempt in range(max_retries):
            try:
                response = llm_engine.get_response(chat_history, **kwargs)
                return idx, response
            except Exception as e:
                last_exception = e
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)
        logger.error(
            f"Failed to get response for prompt: {prompt} Error: {last_exception}"
        )
        return idx, ""

    results = [""] * len(prompts)
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
