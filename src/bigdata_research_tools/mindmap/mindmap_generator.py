import ast
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import Logger, getLogger
from typing import Optional

from bigdata_client.daterange import AbsoluteDateRange, RollingDateRange
from bigdata_client.models.advanced_search_query import QueryComponent
from bigdata_client.models.search import DocumentType, SortBy
from bigdata_client.query import (
    Any as BigdataAny,
)
from bigdata_client.query import Entity, Keyword, Similarity
from tqdm import tqdm

from bigdata_research_tools.client import bigdata_connection
from bigdata_research_tools.llm import LLMEngine
from bigdata_research_tools.llm.base import LLMConfig
from bigdata_research_tools.mindmap.mindmap import MindMap, get_default_tree_config
from bigdata_research_tools.mindmap.mindmap_utils import (
    format_mindmap_to_dataframe,
    load_results_from_file,
    prompts_dict,
    save_results_to_file,
)
from bigdata_research_tools.search.search import run_search

logger: Logger = getLogger(__name__)

bigdata_tool_description = [
    {
        "type": "function",
        "function": {
            "name": "bigdata_search",
            "description": "Run a semantic similarity search on news content using Bigdata API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The list of strings containing various detailed sentences to search in News documents.",
                    },
                    "entities_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The list of entities (People, Places or Organizations) to focus the search on. They will be added as search context with an OR logic.",
                    },
                    "keywords_list": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The list of keywords (one or two words defining topics or concepts) to focus the search on. They will be added as search context with an OR logic.",
                    },
                },
                "required": ["search_list", "entities_list", "keywords_list"],
            },
        },
    }
]


class MindMapGenerator:
    """
    Core orchestrator for generating, refining, and dynamically evolving mind maps using LLMs and Bigdata search.

    Features:
    - One-shot mind map generation (optionally grounded in search results)
    - Refined mind map generation (LLM proposes searches to enhance an initial mind map)
    - Dynamic mind map evolution over time intervals (each step refines previous map with new search context)
    """

    def __init__(
        self,
        llm_model_config_base: LLMConfig | dict | str = "openai::gpt-4o-mini",
        llm_model_config_reasoning: Optional[LLMConfig | dict | str] = None,
    ):
        """
        Args:
            llm_client: Handles LLM chat and tool-calling.
        """
        self.bigdata_connection = bigdata_connection()

        llm_model_config_reasoning = (
            llm_model_config_reasoning
            if llm_model_config_reasoning
            else llm_model_config_base
        )

        if isinstance(llm_model_config_base, dict):
            self.llm_model_config_base = LLMConfig(**llm_model_config_base)
        elif isinstance(llm_model_config_base, str):
            self.llm_model_config_base = get_default_tree_config(llm_model_config_base)
        else:
            self.llm_model_config_base = llm_model_config_base

        if isinstance(llm_model_config_reasoning, dict):
            self.llm_model_config_reasoning = LLMConfig(**llm_model_config_reasoning)
        elif isinstance(llm_model_config_reasoning, str):
            self.llm_model_config_reasoning = get_default_tree_config(
                llm_model_config_reasoning
            )
        else:
            self.llm_model_config_reasoning = llm_model_config_reasoning

        self.llm_base = LLMEngine(
            model=self.llm_model_config_base.model,
            **self.llm_model_config_base.connection_config,
        )

        self.llm_reasoning = LLMEngine(
            model=self.llm_model_config_reasoning.model,
            **self.llm_model_config_reasoning.connection_config,
        )

    def _parse_llm_to_themetree(self, mindmap_text: str) -> MindMap:
        """
        Parse LLM output (expected to be a valid JSON object) into a MindMap.
        Strictly enforce JSON/dict structure, required fields, and allowed keys. If parsing or validation fails, raises an error with details.
        """

        text = mindmap_text.strip()
        # Remove code block markers and language tags (minimal cleaning)
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```$", "", text)
        # Remove accidental language tags at the start (e.g., "json\n{")
        text = re.sub(r"^[a-zA-Z]+\s*\n*{", "{", text)
        # Remove any prefix before the first { or [
        text = re.sub(r"^[^({\[]*({|\[)", r"\1", text, flags=re.DOTALL)
        # Try JSON, then ast.literal_eval
        try:
            tree_dict = json.loads(text)
        except Exception:
            try:
                tree_dict = ast.literal_eval(text)
            except Exception as e:
                raise ValueError(
                    f"Failed to parse LLM output as JSON or Python dict.\nRaw output:\n{mindmap_text}\nCLEANED OUTPUT:\n{text}\nError: {e}"
                )

        # --- Strict validation of required fields and allowed keys ---
        allowed_keys = {"label", "node", "summary", "children"}

        def validate_node(node, path="root"):
            if not isinstance(node, dict):
                raise ValueError(f"Node at {path} is not a dict: {node}")
            # Check for illegal keys
            illegal_keys = set(node.keys()) - allowed_keys
            if illegal_keys:
                raise ValueError(
                    f"Illegal key(s) {illegal_keys} at {path}. Node: {node}"
                )
            # Check for required fields
            for key in allowed_keys:
                if key not in node or node[key] is None:
                    raise ValueError(
                        f"Missing or null required field '{key}' at {path}. Node: {node}"
                    )
            if not isinstance(node["children"], list):
                raise ValueError(
                    f"'children' field at {path} is not a list. Node: {node}"
                )
            for idx, child in enumerate(node["children"]):
                validate_node(child, path=f"{path} -> children[{idx}]")

        # Lowercase keys for robustness
        def dict_keys_to_lowercase(d):
            if isinstance(d, dict):
                return {k.lower(): dict_keys_to_lowercase(v) for k, v in d.items()}
            elif isinstance(d, list):
                return [dict_keys_to_lowercase(i) for i in d]
            else:
                return d

        tree_dict = dict_keys_to_lowercase(tree_dict)
        try:
            validate_node(tree_dict)
        except Exception as e:
            raise ValueError(
                f"Mind map structure validation failed: {e}\nParsed dict:\n{json.dumps(tree_dict, indent=2)}"
            )
        try:
            theme_tree = MindMap.from_dict(tree_dict)
        except Exception as e:
            raise ValueError(
                f"Failed to build ThemeTree from dict: {e}\nParsed dict:\n{json.dumps(tree_dict, indent=2)}"
            )
        return theme_tree

    def _themetree_to_dataframe(self, theme_tree: MindMap):
        """
        Convert a ThemeTree object to a pandas DataFrame.
        """
        try:
            df = theme_tree.to_dataframe()
        except Exception as e:
            raise ValueError(
                f"Failed to convert ThemeTree to DataFrame: {e}\nThemeTree:\n{theme_tree}"
            )
        return df

    def compose_base_message(
        self, main_theme: str, focus: str, map_type: str, instructions: Optional[str]
    ) -> list:
        # Explicit, step-by-step prompt (robust, as in working repo, minus Keywords)
        if instructions is None:
            instructions = prompts_dict[map_type]["default_instructions"].format(
                main_theme=main_theme, analyst_focus=focus
            )

        enforce_structure = prompts_dict[map_type]["enforce_structure_string"]
        messages = [
            {
                "role": "system",
                "content": f"{instructions} {focus}\n{enforce_structure}",
            },
            {
                "role": "user",
                "content": prompts_dict[map_type]["user_prompt_message"].format(
                    main_theme=main_theme
                ),
            },
        ]

        return messages

    def compose_tool_call_message(
        self,
        main_theme: str,
        focus: str,
        map_type: str,
        instructions: Optional[str],
        date_range: Optional[tuple[str, str]],
        initial_mindmap: Optional[str],
    ) -> list:
        enforce_structure = prompts_dict[map_type]["enforce_structure_string"]

        if instructions is None:
            instructions = prompts_dict[map_type]["default_instructions"].format(
                main_theme=main_theme, analyst_focus=focus
            )

        tool_prompt = f"{instructions} {focus} You can use news search to find relevant information about the topic. \nUse the Bigdata API to search for news articles related to the topic and use them to inform your response."

        if initial_mindmap:
            tool_prompt += f"\nStarting from the following mind map:\n{initial_mindmap}"
        if date_range is not None:
            tool_prompt += f"\nYour search will be conducted over the range: {date_range[0]} - {date_range[1]}"

        tool_prompt += f"\nReturn a list of searches you would like to perform to enhance it.\n{enforce_structure}"

        messages = [
            {"role": "system", "content": tool_prompt},
            {
                "role": "user",
                "content": prompts_dict[map_type]["user_prompt_message"].format(
                    main_theme=main_theme
                ),
            },
        ]

        return messages

    def send_tool_call(
        self, messages: list, llm_client: LLMEngine, llm_kwargs: dict
    ) -> tuple:
        llm_kwargs.update(
            {
                "tool_choice": {
                    "type": "function",
                    "function": {"name": "bigdata_search"},
                }
            }
        )

        response_dict = llm_client.get_tools_response(
            messages, tools=bigdata_tool_description, **llm_kwargs
        )

        try:
            if response_dict["tool_calls"] is not None:
                tool_call_id = response_dict["id"][0]
                arguments = response_dict["arguments"][0]
                search_list = arguments.get("search_list", [])  # ty: ignore[possibly-missing-attribute]
                entities_list = arguments.get("entities_list", [])  # ty: ignore[possibly-missing-attribute]
                keywords_list = arguments.get("keywords_list", [])  # ty: ignore[possibly-missing-attribute]
                return (
                    tool_call_id,
                    response_dict["tool_calls"],
                    search_list,
                    entities_list,
                    keywords_list,
                )
            else:
                print("No tool call found in the response.")

                return None, None, response_dict["text"], None, None
        except Exception as e:
            raise RuntimeError(f"Failed to parse OpenAI tool call response: {e}")

    def compose_final_message(
        self,
        main_theme: str,
        focus: str,
        map_type: str,
        instructions: Optional[str],
        date_range: Optional[tuple[str, str]],
        tool_calls,
        tool_call_id,
        context,
    ) -> list:
        enforce_structure = prompts_dict[map_type]["enforce_structure_string"]

        if instructions is None:
            instructions = prompts_dict[map_type]["default_instructions"].format(
                main_theme=main_theme, analyst_focus=focus
            )

        final_prompt = f"{instructions} {focus}. \nIMPORTANT: Only create additional branches if the tool call results contain explicit information suggesting that new branches would be relevant.\n{enforce_structure}"

        if date_range is not None:
            final_prompt += f"\nYour search will be conducted over the range: {date_range[0]} - {date_range[1]}"

        final_message = [
            {
                "role": "system",
                "content": final_prompt,
            },
            {
                "role": "user",
                "content": prompts_dict[map_type]["user_prompt_message"].format(
                    main_theme=main_theme
                ),
            },
            {"role": "assistant", "content": None, "tool_calls": tool_calls},
            {"role": "tool", "tool_call_id": tool_call_id, "content": context},
        ]

        return final_message

    def compose_refinement_message(
        self,
        main_theme: str,
        focus: str,
        map_type: str,
        instructions: Optional[str],
        date_range: Optional[tuple[str, str]],
        initial_mindmap: str,
        context: str,
        tool_calls,
        tool_call_id: str | None,
    ) -> list:
        enforce_structure = prompts_dict[map_type]["enforce_structure_string"]

        if instructions is None:
            instructions = prompts_dict[map_type]["default_instructions"].format(
                main_theme=main_theme, analyst_focus=focus
            )

        refine_prompt = f"{instructions} {prompts_dict[map_type]['qualifier']}: {main_theme} {focus}.\nBased on these instructions, enhance the given mindmap with the information below. Only return the mindmap without extra text.\nIMPORTANT: Only create additional branches if the tool call results contain explicit information suggesting that new branches would be relevant.\n{enforce_structure}."

        if date_range is not None:
            refine_prompt += f"\nYour search will be conducted over the range: {date_range[0]} - {date_range[1]}"

        refinement_messages = [
            {"role": "system", "content": refine_prompt},
            {"role": "user", "content": initial_mindmap},
            {"role": "assistant", "content": None, "tool_calls": tool_calls},
            {"role": "tool", "tool_call_id": tool_call_id, "content": context},
        ]

        return refinement_messages

    def generate_one_shot(
        self,
        main_theme: str,
        focus: str,
        allow_grounding: bool = False,
        instructions: Optional[str] = None,
        date_range: Optional[tuple[str, str]] = None,
        map_type: str = "risk",
    ) -> tuple[MindMap, dict]:
        """
        Generate a mind map in one LLM call, optionally allowing the LLM to request grounding.
        If allow_grounding is True, use the specified grounding_method ("tool_call" or "chat").
        Optionally log intermediate steps to disk.
        """

        messages = self.compose_base_message(
            main_theme=main_theme,
            focus=focus,
            map_type=map_type,
            instructions=instructions,
        )

        llm_kwargs = self.llm_model_config_base.get_llm_kwargs(
            remove_max_tokens=True, remove_timeout=True
        )
        if allow_grounding:
            messages = self.compose_tool_call_message(
                main_theme=main_theme,
                focus=focus,
                map_type=map_type,
                instructions=instructions,
                date_range=date_range,
                initial_mindmap=None,
            )
            tool_call_id, tool_calls, search_list, entities_list, keywords_list = (
                self.send_tool_call(messages, self.llm_base, llm_kwargs)
            )

            if search_list and isinstance(search_list, list):
                context = self._run_and_collate_search(
                    search_list, entities_list, keywords_list, date_range=date_range
                )

                final_messages = self.compose_final_message(
                    main_theme=main_theme,
                    focus=focus,
                    map_type=map_type,
                    instructions=instructions,
                    date_range=date_range,
                    tool_calls=tool_calls,
                    tool_call_id=tool_call_id,
                    context=context,
                )

                mindmap_text = self.llm_base.get_response(final_messages)

                theme_tree = self._parse_llm_to_themetree(mindmap_text)
                df = self._themetree_to_dataframe(theme_tree)
                return theme_tree, {
                    "mindmap_text": mindmap_text,
                    "mindmap_df": df,
                    "mindmap_json": theme_tree.to_json(),  ##where does this come from?
                    "grounded": True,
                    "search_queries": search_list,
                    "search_context": context,
                }
            else:
                # decide if this fallback should be simplified
                mindmap_text = search_list if isinstance(search_list, str) else ""
                theme_tree = self._parse_llm_to_themetree(
                    mindmap_text
                )  ## check if correct
                df = format_mindmap_to_dataframe(mindmap_text)
                return MindMap("", 0), {
                    "mindmap_text": mindmap_text,
                    "mindmap_df": df,
                    "mindmap_json": theme_tree.to_json(),
                    "grounded": False,
                }
        # Default: just generate mind map
        mindmap_text = self.llm_base.get_response(messages)

        theme_tree = self._parse_llm_to_themetree(mindmap_text)
        df = self._themetree_to_dataframe(theme_tree)
        return theme_tree, {
            "mindmap_text": mindmap_text,
            "mindmap_tree": theme_tree,
            "mindmap_json": theme_tree.to_json(),
            "mindmap_df": df,
            "grounded": False,
        }

    def generate_refined(
        self,
        main_theme: str,
        focus: str,
        initial_mindmap: str,
        output_dir: str = "./refined_mindmaps",
        filename: str = "refined_mindmap.json",
        map_type: str = "risk",
        instructions: Optional[str] = None,
        search_scope: Optional[DocumentType] = None,
        sortby: Optional[SortBy] = None,
        date_range: Optional[tuple[str, str]] = None,
        chunk_limit: int = 20,
        **llm_kwargs,
    ) -> tuple[MindMap | None, dict]:
        """
        Refine an initial mind map: LLM proposes searches, search is run, LLM refines mind map with search results.
        Optionally log intermediate steps to disk.
        """

        messages = self.compose_tool_call_message(
            main_theme=main_theme,
            focus=focus,
            map_type=map_type,
            instructions=instructions,
            date_range=date_range,
            initial_mindmap=initial_mindmap,
        )
        llm_kwargs = self.llm_model_config_reasoning.get_llm_kwargs(
            remove_max_tokens=True, remove_timeout=True
        )

        tool_call_id, tool_calls, search_list, entities_list, keywords_list = (
            self.send_tool_call(messages, self.llm_reasoning, llm_kwargs=llm_kwargs)
        )

        if search_list and isinstance(search_list, list):
            context = self._run_and_collate_search(
                search_list,
                entities_list,
                keywords_list,
                search_scope,
                sortby,
                date_range,
                chunk_limit,
            )

            refinement_messages = self.compose_refinement_message(
                main_theme=main_theme,
                focus=focus,
                map_type=map_type,
                instructions=instructions,
                date_range=date_range,
                initial_mindmap=initial_mindmap,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id,
                context=context,
            )
            mindmap_text = self.llm_reasoning.get_response(refinement_messages)

            theme_tree = self._parse_llm_to_themetree(mindmap_text)
            df = self._themetree_to_dataframe(theme_tree)
            result_dict = {
                "mindmap_text": mindmap_text,
                "mindmap_df": df,
                "mindmap_json": theme_tree.to_json(),
                "search_queries": search_list,
                "search_context": context,
            }
            save_results_to_file(result_dict, output_dir, filename)
            return theme_tree, result_dict
        else:
            mindmap_text = search_list if isinstance(search_list, str) else ""
            df = format_mindmap_to_dataframe(mindmap_text)
            result_dict = {
                "mindmap_text": mindmap_text,
                "mindmap_df": df,
                "mindmap_json": "",
                "search_queries": [],
                "search_context": "",
            }
            save_results_to_file(result_dict, output_dir, filename)
            return None, result_dict

    def generate_or_load_refined(
        self,
        main_theme: str,
        focus: str,
        map_type: str,
        initial_mindmap: str,
        instructions: Optional[str],
        search_scope: Optional[DocumentType] = None,
        sortby: Optional[SortBy] = None,
        date_range: Optional[tuple[str, str]] = None,
        chunk_limit: int = 20,
        output_dir: str = "./bootstrapped_mindmaps",
        filename: str = "refined_mindmap",
        i: int = 0,
    ) -> dict:
        if f"{filename}_{i}.json" in os.listdir(output_dir):
            result = load_results_from_file(output_dir, f"{filename}_{i}.json")
            print(f"Loaded existing result for {filename}_{i}.json")
        else:
            try:
                _, result = self.generate_refined(
                    instructions=instructions,
                    focus=focus,
                    main_theme=main_theme,
                    map_type=map_type,
                    initial_mindmap=initial_mindmap,
                    date_range=date_range,
                    search_scope=search_scope,
                    sortby=sortby,
                    chunk_limit=chunk_limit,
                    output_dir=output_dir,
                    filename=f"{filename}_{i}.json",
                )
                # save_results_to_file(result, output_dir, )
            except Exception:
                _, result = self.generate_refined(
                    instructions=instructions,
                    focus=focus,
                    main_theme=main_theme,
                    map_type=map_type,
                    initial_mindmap=initial_mindmap,
                    date_range=date_range,
                    output_dir=output_dir,
                    filename=f"{filename}_{i}.json",
                )

        return result

    def bootstrap_refined(
        self,
        main_theme: str,
        focus: str,
        map_type: str,
        initial_mindmap: str,
        instructions: Optional[str],
        search_scope: Optional[DocumentType] = None,
        sortby: Optional[SortBy] = None,
        date_range: Optional[tuple[str, str]] = None,
        chunk_limit: int = 20,
        output_dir: str = "./bootstrapped_mindmaps",
        filename: str = "refined_mindmap",
        n_elements: int = 50,
        max_workers: int = 10,
    ) -> list[dict]:
        """
        Generate multiple refined mindmaps in parallel using ThreadPoolExecutor.

        Generates n_elements mindmaps by calling generate_or_load_refined for each index.
        Uses a thread pool to parallelize the generation process for better efficiency.
        Each mindmap is saved with an index suffix to the output_dir.

        Returns a list of all generated mindmap results.
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        refined_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a mapping of futures to their corresponding indices
            future_to_index = {}

            # Submit all tasks and track which future corresponds to which index
            for i in range(n_elements):
                future = executor.submit(
                    self.generate_or_load_refined,
                    instructions=instructions,
                    focus=focus,
                    main_theme=main_theme,
                    map_type=map_type,
                    initial_mindmap=initial_mindmap,
                    search_scope=search_scope,
                    sortby=sortby,
                    date_range=date_range,
                    chunk_limit=chunk_limit,
                    output_dir=output_dir,
                    filename=filename,
                    i=i,
                )
                future_to_index[future] = i

            # Process futures as they complete
            for future in tqdm(
                as_completed(future_to_index),
                total=n_elements,
                desc="Bootstrapping Refined Mindmaps...",
            ):
                i = future_to_index[future]
                try:
                    # Store the result in the list
                    refined_results.append(future.result())
                except Exception as e:
                    print(f"Error in generating mindmap {i}: {e}")

        return refined_results

    def generate_dynamic(
        self,
        main_theme: str,
        focus: str,
        month_intervals: list[tuple[str, str]],
        month_names: list[str],
        instructions: Optional[str],
        search_scope: Optional[DocumentType] = None,
        sortby: Optional[SortBy] = None,
        chunk_limit: int = 20,
        map_type: str = "risk",
        output_dir: str = "./dynamic_mindmaps",
        **llm_kwargs,
    ) -> tuple[dict[str, MindMap], dict]:
        """
        Dynamic/iterative mind map generation over time intervals.
        Returns a list of dicts, one per interval.
        Each step: generate/refine mind map for the given interval, grounded in search results for that period.
        """
        results = {}
        mind_map_objs = {}
        # Step 1: Generate initial mind map for t0
        one_shot_map, one_shot_dict = self.generate_one_shot(
            main_theme=main_theme,
            focus=focus,
            allow_grounding=False,
            instructions=instructions,
            map_type=map_type,
            **llm_kwargs,
        )
        prev_mindmap = one_shot_dict["mindmap_json"]
        mind_map_objs["base_mindmap"] = one_shot_map
        results["base_mindmap"] = one_shot_dict
        # Step 2: For each subsequent interval, refine using previous mind map and new search, including starting month
        for i, (date_range, month_name) in enumerate(
            zip(month_intervals, month_names), start=0
        ):
            refined_map, refined = self.generate_refined(
                main_theme=main_theme,
                focus=focus,
                initial_mindmap=prev_mindmap,
                map_type=map_type,
                output_dir=output_dir,
                filename=f"{month_name}.json",
                instructions=instructions,
                search_scope=search_scope,
                sortby=sortby,
                date_range=date_range,
                chunk_limit=chunk_limit,
                **llm_kwargs,
            )

            results[month_name] = refined
            mind_map_objs[month_name] = refined_map
            prev_mindmap = refined["mindmap_json"]
        return mind_map_objs, results

    def _run_and_collate_search(
        self,
        search_list: list[str],
        entities_list: Optional[list[str]],
        keywords_list: Optional[list[str]],
        search_scope: Optional[DocumentType] = None,
        sortby: Optional[SortBy] = None,
        date_range: Optional[tuple[str, str]] = None,
        chunk_limit: int = 20,
    ) -> str:
        """
        Run Bigdata search for each query and collate results for LLM context.
        Uses sensible defaults for scope, sortby, and date_range.
        If date_range is a list of one tuple (e.g. [('2025-01-01', '2025-01-31')]), unpacks it.
        If date_range is a tuple/list of two strings, converts to AbsoluteDateRange.
        """

        # Set defaults if not provided
        scope = search_scope if search_scope is not None else DocumentType.NEWS
        sortby = sortby if sortby is not None else SortBy.RELEVANCE

        if date_range is None:
            date_range_filter = RollingDateRange.LAST_THIRTY_DAYS
        else:
            date_range_filter = AbsoluteDateRange(
                start=date_range[0], end=date_range[1]
            )

        if entities_list:
            print(f"Entities List: {entities_list}")
            entity_objs = []
            for entity_name in entities_list:
                try:
                    suggestions = self.bigdata_connection.knowledge_graph.autosuggest(
                        entity_name, limit=1
                    )
                    if suggestions:  # Check if list is not empty
                        entity = suggestions[0]
                        entity_objs.append(entity)
                    else:
                        print(f"Warning: No autosuggest results for '{entity_name}'")
                except Exception as e:
                    print(f"Warning: Autosuggest failed for '{entity_name}': {e}")
                    continue

            confirmed_entities = [
                entity.id
                for entity, orig_str in zip(entity_objs, entities_list)
                if entity.name.lower() in orig_str.lower()
                or orig_str.lower() in entity.name.lower()
            ]
            if confirmed_entities:
                entities = BigdataAny([Entity(entity) for entity in confirmed_entities])
            else:
                entities = None
            print(
                f"Searching with entities: {[entity.name for entity, orig_str in zip(entity_objs, entities_list) if entity.name in orig_str or orig_str in entity.name]}"
            )
        else:
            entities = None
        if keywords_list:
            print(f"Searching with keywords: {keywords_list}")
            keywords = BigdataAny([Keyword(kw) for kw in keywords_list])
        else:
            keywords = None

        print(f"Searching with sentences: {search_list}")

        queries: list[QueryComponent] = [
            Similarity(sentence) for sentence in search_list
        ]
        if entities:
            queries = [query & entities for query in queries]
        if keywords:
            queries = [query & keywords for query in queries]

        all_results = run_search(
            queries=queries,
            date_ranges=date_range_filter,
            sortby=sortby,
            scope=scope,
            limit=chunk_limit,
            only_results=False,
            rerank_threshold=None,
        )

        return self.collate_results(all_results)

    def collate_results(self, results: dict) -> str:
        """
        Collate a list of (query, result) tuples into a single string for LLM context.

        Args:
            results (list): List of (query, result) tuples.

        Returns:
            str: Collated string for LLM context.
        """
        doctexts = []
        for (text_query, date_range), result in results.items():
            dictitem = text_query.to_dict()
            if dictitem["type"] == "similarity":
                sentence = dictitem["value"]
            else:
                sentence = ""
            docstr = f"###Query: {sentence}\n ### Results:\n"
            for doc in result:
                headline = getattr(doc, "headline", "No headline")
                docstr += f"## {headline}\n\n##"
                docstr += f"Date: {doc.timestamp.strftime('%Y-%m-%d')}\n\n"
                if hasattr(doc, "chunks"):
                    for chunk in doc.chunks:
                        docstr += f"{chunk.text}\n"
            doctexts.append(docstr)
        return "\n".join(doctexts)
