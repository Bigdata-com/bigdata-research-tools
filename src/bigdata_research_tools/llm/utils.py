import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Callable, Coroutine

try:
    from openai import BadRequestError  # ty: ignore[unresolved-import]
except ImportError:
    # Fallback, this wont work for actual OpenAI calls but avoids import errors
    class hasJsonBody:
        def json(self) -> dict:
            return {}

    class BadRequestError(Exception):
        response: hasJsonBody


from tqdm import tqdm

from bigdata_research_tools.llm.base import AsyncLLMEngine

logger: Logger = getLogger(__name__)


def initialize_llm_error_log():
    # Ensure output directory exists
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    log_file = output_dir / "llm_error_logs.txt"
    return log_file


def _log_llm_error_to_file(
    lock: threading.Lock,
    log_file: Path,
    timestamp: str,
    chat_history: list,
    error: Exception,
    prompt_idx: int | None = None,
):
    """
    Thread-safe logging of LLM errors to file.

    Args:
        timestamp (str): ISO format timestamp of the error
        chat_history (list): The chat history that caused the error
        error (Exception): The exception that occurred
        prompt_idx (int): Optional index of the prompt for tracking
    """
    log_entry = {
        "timestamp": timestamp,
        "prompt_index": prompt_idx,
        "chat_history": chat_history,
        "error_type": type(error).__name__,
        "error_details": getattr(error, "body", None)
        if hasattr(error, "body")
        else None,
    }

    # Thread-safe file writing
    with lock:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(log_entry, indent=2, default=str) + "\n" + "=" * 80 + "\n"
            )


# https://platform.openai.com/docs/guides/batch
def run_concurrent_prompts(
    llm_engine: AsyncLLMEngine,
    prompts: list[str],
    system_prompt: str,
    timeout: int | None,
    max_workers: int = 30,
    processing_callbacks: list[Callable[[str], str]] | None = None,
    **kwargs,
) -> list[str]:
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

    async def _run_async():
        # Create semaphore INSIDE the event loop
        semaphore = asyncio.Semaphore(max_workers)
        logger.info(f"Running {len(prompts)} prompts concurrently")
        tasks = [
            _fetch_with_semaphore(
                idx,
                llm_engine,
                semaphore,
                system_prompt,
                prompt,
                timeout,
                processing_callbacks=processing_callbacks,
                **kwargs,
            )
            for idx, prompt in enumerate(prompts)
        ]
        return await _run_with_progress_bar(tasks)

    return asyncio.run(_run_async())


async def _fetch_with_semaphore(
    idx: int,
    llm_engine: AsyncLLMEngine,
    semaphore: asyncio.Semaphore,
    system_prompt: str,
    prompt: str,
    timeout: int | None,
    processing_callbacks: list[Callable[[str], str]] | None = None,
    **kwargs,
) -> tuple[int, str]:
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
        processing_callbacks (list[Callable[[str], str]] | None): Optional callback function to be called with the index and response for each prompt.
        kwargs (dict): Additional arguments to pass to the `get_response` method of the LLMEngine.

    Returns:
        Tuple[int, str]: The index of the prompt and the response from the LLM model.
    """
    log_file = initialize_llm_error_log()
    _error_lock = threading.Lock()
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
                    if processing_callbacks is not None:
                        for func in processing_callbacks:
                            response = func(response)
                return idx, response
            except Exception as e:
                if isinstance(e, asyncio.TimeoutError) and attempt == 0:
                    logger.warning(
                        f"Timeout occurred for prompt during LLM call, current timeout configured {timeout} seconds. If this keeps happening (> 1% of your requests), consider increasing the timeout. Retrying..."
                    )
                elif isinstance(e, ValueError):
                    logger.warning(
                        "Error occurred for response validation during LLM call. Retrying..."
                    )
                elif isinstance(e, BadRequestError):
                    # Check for ResponsibleAIPolicyViolation error on Azure OpenAI
                    if (
                        e.response.json().get("innererror", {}).get("code")
                        == "ResponsibleAIPolicyViolation"
                    ):
                        logger.error(
                            "LLM returned a ResponsibleAIPolicyViolation Error. Ignoring this response..."
                        )
                        # Log the error to file
                        timestamp = datetime.now().isoformat()
                        _log_llm_error_to_file(
                            _error_lock, log_file, timestamp, chat_history, e, idx
                        )
                        return idx, ""  # Return empty response for policy violations
                last_exception = e
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                retry_delay = min(retry_delay * 2, 60)
        logger.error(
            f"Failed to get response for prompt: {prompt} Error: {last_exception}"
        )
        return idx, ""


async def _run_with_progress_bar(
    tasks: list[Coroutine[Any, Any, tuple[int, str]]],
) -> list[str]:
    """Run asyncio tasks with a tqdm progress bar."""
    # Pre-allocate a list for results to preserve order
    results = [""] * len(tasks)
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
    prompts: list[str],
    system_prompt: str,
    max_workers: int = 30,
    processing_callbacks: list[Callable[[str], str]] | None = None,
    **kwargs,
) -> list[str]:
    """
    Run the LLM on the received prompts concurrently using threads.

    Args:
        llm_engine: The LLM engine with a synchronous get_response method.
        prompts (list[str]): List of prompts to run concurrently.
        system_prompt (str): The system prompt.
        max_workers (int): The maximum number of threads.
        processing_callbacks (list[Callable[[str], str]] | None): Optional callback function to be called with the index and response for each prompt.
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
