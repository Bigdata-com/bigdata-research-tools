from typing import Any, List, Dict, Optional, Tuple
from bigdata_research_tools.llm.base import LLMConfig
from bigdata_research_tools.llm import LLMEngine

from bigdata_research_tools.search.query_builder import build_batched_query
# from bigdata_research_tools.search.query_builder import (
#     EntitiesToSearch,
#     build_batched_query,
#     create_date_ranges,
# )
# cannot use query builder because it is to error-prone to build EntitiesToSearch based on the LLM output
from bigdata_research_tools.search.search import run_search
from bigdata_research_tools.client import bigdata_connection
from bigdata_client.query import (
    Any,
    Keyword,
    Similarity,
)

from bigdata_research_tools.mindmap.mindmap_utils import format_mindmap_to_dataframe, save_results_to_file, load_results_from_file, prompts_dict
import os
import json
import re
import json
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from bigdata_research_tools.mindmap.mindmap import MindMap, get_default_tree_config
from logging import Logger, getLogger
from bigdata_client.models.search import DocumentType, SortBy
from bigdata_client.daterange import RollingDateRange, AbsoluteDateRange
logger: Logger = getLogger(__name__)

bigdata_tool_description = [{
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
                            }
                        },
                        "required": ["search_list", "entities_list", "keywords_list"]
                        }                    
                }
            }]

class MindMapGenerator:
    """
    Core orchestrator for generating, refining, and dynamically evolving mind maps using LLMs and Bigdata search.

    Features:
    - One-shot mind map generation (optionally grounded in search results)
    - Refined mind map generation (LLM proposes searches to enhance an initial mind map)
    - Dynamic mind map evolution over time intervals (each step refines previous map with new search context)
    """

    def __init__(self,
                llm_model_config_base: LLMConfig | dict | str = "openai::gpt-4o-mini",
                llm_model_config_reasoning: Optional[LLMConfig | dict | str] = None,
                ):
        """
        Args:
            llm_client: Handles LLM chat and tool-calling.
        """
        self.bigdata_connection = bigdata_connection()
        
        llm_model_config_reasoning = llm_model_config_reasoning if llm_model_config_reasoning else llm_model_config_base

        if isinstance(llm_model_config_base, dict):
            self.llm_model_config_base = LLMConfig(**llm_model_config_base)
        elif isinstance(llm_model_config_base, str):
            self.llm_model_config_base = get_default_tree_config(llm_model_config_base)

        if isinstance(llm_model_config_reasoning, dict):
            self.llm_model_config_reasoning = LLMConfig(**llm_model_config_reasoning)
        elif isinstance(llm_model_config_reasoning, str):
            self.llm_model_config_reasoning = get_default_tree_config(llm_model_config_reasoning)
        
        print(self.llm_model_config_base)
        self.llm_base = LLMEngine(model=self.llm_model_config_base.model, **self.llm_model_config_base.connection_config)
        print(self.llm_model_config_reasoning)
        self.llm_reasoning = LLMEngine(model=self.llm_model_config_reasoning.model, **self.llm_model_config_reasoning.connection_config)

    def _parse_llm_to_themetree(self, mindmap_text: str) -> MindMap:
        """
        Parse LLM output (expected to be a valid JSON object) into a MindMap.
        Strictly enforce JSON/dict structure, required fields, and allowed keys. If parsing or validation fails, raises an error with details.
        """
        import collections.abc
        text = mindmap_text.strip()
        # Remove code block markers and language tags (minimal cleaning)
        text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
        text = re.sub(r'```$', '', text)
        # Remove accidental language tags at the start (e.g., "json\n{")
        text = re.sub(r'^[a-zA-Z]+\s*\n*{', '{', text)
        # Remove any prefix before the first { or [
        text = re.sub(r'^[^({\[]*({|\[)', r'\1', text, flags=re.DOTALL)
        # Try JSON, then ast.literal_eval
        try:
            tree_dict = json.loads(text)
        except Exception:
            try:
                tree_dict = ast.literal_eval(text)
            except Exception as e:
                raise ValueError(f"Failed to parse LLM output as JSON or Python dict.\nRaw output:\n{mindmap_text}\nCLEANED OUTPUT:\n{text}\nError: {e}")

        # --- Strict validation of required fields and allowed keys ---
        allowed_keys = {"label", "node", "summary", "children"}
        def validate_node(node, path="root"):
            if not isinstance(node, dict):
                raise ValueError(f"Node at {path} is not a dict: {node}")
            # Check for illegal keys
            illegal_keys = set(node.keys()) - allowed_keys
            if illegal_keys:
                raise ValueError(f"Illegal key(s) {illegal_keys} at {path}. Node: {node}")
            # Check for required fields
            for key in allowed_keys:
                if key not in node or node[key] is None:
                    raise ValueError(f"Missing or null required field '{key}' at {path}. Node: {node}")
            if not isinstance(node["children"], list):
                raise ValueError(f"'children' field at {path} is not a list. Node: {node}")
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
            raise ValueError(f"Mind map structure validation failed: {e}\nParsed dict:\n{json.dumps(tree_dict, indent=2)}")
        try:
            theme_tree = MindMap.from_dict(tree_dict)
        except Exception as e:
            raise ValueError(f"Failed to build ThemeTree from dict: {e}\nParsed dict:\n{json.dumps(tree_dict, indent=2)}")
        return theme_tree

    def _themetree_to_dataframe(self, theme_tree: MindMap):
        """
        Convert a ThemeTree object to a pandas DataFrame.
        """
        try:
            df = theme_tree.to_dataframe()
        except Exception as e:
            raise ValueError(f"Failed to convert ThemeTree to DataFrame: {e}\nThemeTree:\n{theme_tree}")
        return df
    
    def compose_base_message(self, main_theme: str, focus: str, map_type: str, instructions: Optional[str]) -> list:
        # Explicit, step-by-step prompt (robust, as in working repo, minus Keywords)
        enforce_structure = prompts_dict[map_type]['enforce_structure_string']
        messages = [
            {"role": "system", "content": f"{instructions} {focus}\n{enforce_structure}"},
            {"role": "user", "content":  prompts_dict[map_type]['user_prompt_message'].format(main_theme=main_theme)}
        ]
        return messages
    
    def compose_tool_call_message(self, main_theme: str, focus: str, map_type: str, instructions: Optional[str], initial_mindmap: Optional[str]) -> list:
        enforce_structure = prompts_dict[map_type]['enforce_structure_string']
        tool_prompt = f"{instructions} {focus} You can use news search to find relevant information about the topic. \nUse the Bigdata API to search for news articles related to the topic and use them to inform your response."
        if initial_mindmap:

            tool_prompt+=f"Starting from the following mind map:\n{initial_mindmap}"
            
        tool_prompt+=f"\nReturn a list of searches you would like to perform to enhance it.\n{enforce_structure}"

        messages = [
            {"role": "system", "content": tool_prompt},
            {"role": "user", "content": prompts_dict[map_type]['user_prompt_message'].format(main_theme=main_theme)}
        ]

        return messages

    def send_tool_call(self, messages: list, llm_client:LLMEngine, llm_kwargs: dict) -> list:

        llm_kwargs.update({"tool_choice": {"type": "function", "function": {"name": "bigdata_search"}}})

        response_dict = llm_client.get_tools_response(
            messages,tools=bigdata_tool_description, **llm_kwargs)

        try:
            if response_dict["tool_calls"] is not None:
                
                tool_call_id = response_dict["id"][0]
                arguments = response_dict["arguments"][0]
                search_list = arguments.get("search_list", [])
                entities_list = arguments.get("entities_list", [])
                keywords_list = arguments.get("keywords_list", [])
                return tool_call_id, response_dict["tool_calls"], search_list, entities_list, keywords_list
            else:
                print("No tool call found in the response.")
                
                return None, None, response_dict["text"], None, None
        except Exception as e:
            raise RuntimeError(f"Failed to parse OpenAI tool call response: {e}")

    def compose_final_message(self, main_theme: str, focus: str, map_type: str, instructions: Optional[str], tool_calls, tool_call_id, context) -> list:
        enforce_structure = prompts_dict[map_type]['enforce_structure_string']

        final_message = [
                        {"role": "system", "content": f"{instructions} {focus}. IMPORTANT: Only create additional branches if the tool call results contain explicit information suggesting that new branches would be relevant. \n{enforce_structure}"},
                        {"role": "user", "content": prompts_dict[map_type]['user_prompt_message'].format(main_theme=main_theme)},
                        {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": tool_calls
                        },
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": context
                        }
                    ]
        
        return final_message
    
    def compose_refinement_message(self, main_theme: str, focus: str, map_type: str, instructions: Optional[str], initial_mindmap: str, context: str, tool_calls, tool_call_id) -> list:

        enforce_structure = prompts_dict[map_type]['enforce_structure_string']

        refine_prompt = (
                    f"{instructions} {prompts_dict[map_type]['qualifier']}: {main_theme} {focus} "
                    "Based on these instructions, enhance the given mindmap with the information below. Only return the mindmap without extra text."
                    "IMPORTANT: Only create additional branches if the tool call results contain explicit information suggesting that new branches would be relevant."
                    f"{enforce_structure}."

                )
        refinement_messages = [
                    {"role": "system", "content": refine_prompt},
                    {"role": "user", "content": initial_mindmap},
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": tool_calls
                    },
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": context
                    }
                ]
        
        return refinement_messages

    def generate_one_shot(
        self,
        focus: str,
        main_theme: str,
        instructions: Optional[str] = None,
        allow_grounding: bool = False,
        grounding_method: str = "tool_call",
        date_range: Optional[Tuple[str, str]] = None,
        map_type: str = "risk",
    ) -> Dict[str, Any]:
        """
        Generate a mind map in one LLM call, optionally allowing the LLM to request grounding.
        If allow_grounding is True, use the specified grounding_method ("tool_call" or "chat").
        Optionally log intermediate steps to disk.
        """
        
        
        messages = self.compose_base_message(main_theme, focus, map_type, instructions)

        llm_kwargs = self.llm_model_config_base.get_llm_kwargs(remove_max_tokens=True, remove_timeout=True)
        if allow_grounding:
            if grounding_method == "tool_call":
                messages.append({"role": "user", "content": "You can use news search to find relevant information about the topic. "
            "Use the Bigdata API to search for news articles related to the topic and use them to inform your response. You will need to specify a list of sentences, a list of entities, and a list of keywords."})
                tool_call_id, tool_calls, search_list, entities_list, keywords_list = self.send_tool_call(messages,self.llm_base, llm_kwargs)
                
                if search_list and isinstance(search_list, list):
                    context = self._run_and_collate_search(search_list, entities_list, keywords_list, date_range=date_range)
                    
                    final_messages = self.compose_final_message(main_theme, focus, map_type, instructions, tool_calls, tool_call_id, context)

                    mindmap_text = self.llm_base.get_response(final_messages)

                    theme_tree = self._parse_llm_to_themetree(mindmap_text)
                    df = self._themetree_to_dataframe(theme_tree)
                    return {
                        "mindmap_text": mindmap_text,
                        "mindmap_df": df,
                        "mindmap_json": theme_tree.to_json(), ##where does this come from?
                        "grounded": True,
                        "search_queries": search_list,
                        "search_context": context
                    }
                else:
                    #decide if this fallback should be simplified
                    mindmap_text = search_list if isinstance(search_list, str) else ""
                    theme_tree = self._parse_llm_to_themetree(mindmap_text) ## check if correct
                    df = format_mindmap_to_dataframe(mindmap_text)
                    return {
                        "mindmap_text": mindmap_text,
                        "mindmap_df": df,
                        "mindmap_json": theme_tree.to_json(),
                        "grounded": False
                    }
            else:
                #decide if this fallback should be simplified
                messages[0]["content"] += (
                    " You may request news search to ground your mind map. "
                    "If you want to search, return a list of queries."
                )
                response = self.llm_base.get_response(messages)

                queries = self._parse_queries(response)

                if queries:
                    context = self._run_and_collate_search(queries, [], [])
                    
                    followup_messages = [
                        {"role": "system", "content": f"{instructions} {focus}"},
                        {"role": "user", "content": prompts_dict[map_type]['user_prompt_message'].format(main_theme=main_theme)},
                        {"role": "assistant", "content": "News search results:\n" + context}
                    ]
                    mindmap_text = self.llm_base.get_response(followup_messages)

                    df = format_mindmap_to_dataframe(mindmap_text)
                    return {
                        "mindmap_text": mindmap_text,
                        "mindmap_df": df,
                        "mindmap_json": theme_tree.to_json(),
                        "grounded": True,
                        "search_queries": queries,
                        "search_context": context
                    }
        # Default: just generate mind map
        mindmap_text = self.llm_base.get_response(messages)
        
        theme_tree = self._parse_llm_to_themetree(mindmap_text)
        df = self._themetree_to_dataframe(theme_tree)
        return {
            "mindmap_text": mindmap_text,
            "mindmap_tree": theme_tree,
            "mindmap_json": theme_tree.to_json(),
            "mindmap_df": df,
            "grounded": False
        }

    def generate_refined(
        self,
        focus: str,
        main_theme: str,
        initial_mindmap: str,
        grounding_method: str = "tool_call",
        output_dir:str = "./refined_mindmaps",
        filename:str = "refined_mindmap.json",
        map_type: str = "risk",
        instructions: Optional[str] = None,
        search_scope: Optional[Any] = None,
        sortby: Optional[Any] = None,
        date_range: Optional[Any] = None,
        chunk_limit: Optional[int] = 20,
        **llm_kwargs
    ) -> Dict[str, Any]:
        """
        Refine an initial mind map: LLM proposes searches, search is run, LLM refines mind map with search results.
        Optionally log intermediate steps to disk.
        """
        messages = self.compose_tool_call_message(main_theme, focus, map_type, instructions, initial_mindmap)
        llm_kwargs = self.llm_model_config_reasoning.get_llm_kwargs(remove_max_tokens=True, remove_timeout=True)
        if grounding_method == "tool_call":
            tool_call_id, tool_calls, search_list, entities_list, keywords_list = self.send_tool_call(
                    messages,self.llm_reasoning, llm_kwargs=llm_kwargs)
            
            if search_list and isinstance(search_list, list):
                context = self._run_and_collate_search(
                    search_list, entities_list, keywords_list, search_scope, sortby, date_range, chunk_limit
                )
                
                refinement_messages = self.compose_refinement_message(main_theme, focus, map_type, instructions, initial_mindmap, context, tool_calls, tool_call_id)
                mindmap_text = self.llm_reasoning.get_response(refinement_messages)

                theme_tree = self._parse_llm_to_themetree(mindmap_text)
                df = self._themetree_to_dataframe(theme_tree)
                result_dict = {
                    "mindmap_text": mindmap_text,
                    "mindmap_df": df,
                    "mindmap_json": theme_tree.to_json(),
                    "search_queries": search_list,
                    "search_context": context
                }
                save_results_to_file(result_dict, output_dir, filename)
                return result_dict
            else:
                mindmap_text = search_list if isinstance(search_list, str) else ""
                df = format_mindmap_to_dataframe(mindmap_text)
                result_dict = {
                    "mindmap_text": mindmap_text,
                    "mindmap_df": df,
                    "mindmap_json": theme_tree.to_json(),
                    "search_queries": [],
                    "search_context": ""
                }
                save_results_to_file(result_dict, output_dir, filename)
                return result_dict
        else:
            queries_json = self.llm_reasoning.get_response(messages)

            search_queries = self._parse_queries(queries_json)
            context = self._run_and_collate_search(
                search_queries, [], [], search_scope, sortby, date_range, chunk_limit
            )

            refinement_messages = self.compose_refinement_message(main_theme, focus, map_type, instructions, initial_mindmap, context, tool_calls, tool_call_id)
            mindmap_text = self.llm_reasoning.get_response(refinement_messages)

            theme_tree = self._parse_llm_to_themetree(mindmap_text)
            df = self._themetree_to_dataframe(theme_tree)
            result_dict = {
                "mindmap_text": mindmap_text,
                "mindmap_df": df,
                "mindmap_json": theme_tree.to_json(),
                "search_queries": search_queries,
                "search_context": context
            }
            save_results_to_file(result_dict, output_dir, filename)
            return result_dict
        
    def generate_or_load_refined(self, instructions: str,
                            focus: str,
                            main_theme: str,
                            map_type: str,
                            initial_mindmap: str,
                            llm_model: str = "o3-mini",
                            reasoning_effort: str = "high",
                            search_scope: Any = None,
                            sortby: Any = None,
                            date_range: Any = None,
                            chunk_limit: int = 20,
                            grounding_method: str = "tool_call",
                            output_dir:str = "./bootstrapped_mindmaps",
                            filename: str = "refined_mindmap",
                            i: int = 0):
        if f"{filename}_{i}.json" in os.listdir(output_dir):
            result = load_results_from_file(output_dir, f"{filename}_{i}.json")
            print(f"Loaded existing result for {filename}_{i}.json")
        else:
            try:
                result = self.generate_refined(
                    instructions=instructions,
                    focus=focus,
                    main_theme=main_theme,
                    map_type=map_type,
                    initial_mindmap=initial_mindmap,
                    reasoning_effort=reasoning_effort,
                    grounding_method=grounding_method,
                    date_range=date_range,
                    output_dir=output_dir,
                    filename = f"{filename}_{i}.json"
                )
                #save_results_to_file(result, output_dir, )
            except Exception as e:
                print(e)
                result = self.generate_refined(
                    instructions=instructions,
                    focus=focus,
                    main_theme=main_theme,
                    map_type=map_type,
                    initial_mindmap=initial_mindmap,
                    reasoning_effort=reasoning_effort,
                    grounding_method=grounding_method,
                    date_range=date_range,
                    output_dir=output_dir,
                    filename = f"{filename}_{i}.json"
                )
                #save_results_to_file(result, output_dir, f"{filename}_{i}.json")
        return result

    def bootstrap_refined(self, instructions: str,
                        focus: str,
                        main_theme: str,
                        map_type: str,
                        initial_mindmap: str,
                        search_scope: Any = None,
                        sortby: Any = None,
                        date_range: Any = None,
                        chunk_limit: int = 20,
                        grounding_method: str = "tool_call",
                        output_dir: str = "./bootstrapped_mindmaps",
                        filename: str = "refined_mindmap",
                        n_elements: int = 50,
                        max_workers: int = 10):
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
                    grounding_method=grounding_method,
                    output_dir=output_dir,
                    filename=filename,
                    i=i
                )
                future_to_index[future] = i

            # Process futures as they complete
            for future in tqdm(
                as_completed(future_to_index), total=n_elements, desc="Bootstrapping Refined Mindmaps..."
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
        instructions: str,
        focus: str,
        main_theme: str,
        month_intervals: List[Tuple[str, str]],
        month_names: List[str],
        search_scope: Any = None,
        sortby: Any = None,
        chunk_limit: int = 20,
        grounding_method: str = "tool_call",
        map_type: str = "risk",
        output_dir: str = "./dynamic_mindmaps",
        **llm_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Dynamic/iterative mind map generation over time intervals.
        Returns a list of dicts, one per interval.
        Each step: generate/refine mind map for the given interval, grounded in search results for that period.
        """
        results = {}
        # Step 1: Generate initial mind map for t0
        one_shot = self.generate_one_shot(
            instructions, focus, main_theme, map_type=map_type, **llm_kwargs
        )
        prev_mindmap = one_shot["mindmap_text"]
        results['base_mindmap'] = one_shot
        # Step 2: For each subsequent interval, refine using previous mind map and new search, including starting month
        for i, (interval, month_name) in enumerate(zip(month_intervals, month_names), start=0):
            date_range = self._make_absolute_date_range(interval)
            refined = self.generate_refined(focus = focus,
                                            main_theme=main_theme,
                                            initial_mindmap=prev_mindmap,
                                            grounding_method=grounding_method,
                                            output_dir=output_dir,
                                            filename=f"{month_name}.json",
                                            map_type=map_type,
                                            instructions=instructions,
                                            search_scope=search_scope,
                                            sortby=sortby,
                                            date_range=date_range,
                                            chunk_limit=chunk_limit,
                                            **llm_kwargs
                                                )

            results[month_name] = refined
            prev_mindmap = refined["mindmap_text"]
        return results

    def _run_and_collate_search(
        self,
        search_list: List[str],
        entities_list: List[str],
        keywords_list: List[str],
        search_scope: Any = None,
        sortby: Any = None,
        date_range: Any = None,
        chunk_limit: int = 20
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

        # --- Robust date_range parsing ---
        # If date_range is a list of one tuple, unpack it
        if isinstance(date_range, list) and len(date_range) == 1 and isinstance(date_range[0], (tuple, list)) and len(date_range[0]) == 2:
            date_range = date_range[0]
        # If date_range is a tuple/list of two strings, convert to AbsoluteDateRange
        if isinstance(date_range, (tuple, list)) and len(date_range) == 2 and all(isinstance(x, str) for x in date_range):
            date_range = AbsoluteDateRange(start=date_range[0], end=date_range[1])
        elif date_range is None:
            date_range = RollingDateRange.LAST_THIRTY_DAYS

        if entities_list:
            print(f"Entities List: {entities_list}")
            entity_objs = []
            for entity_name in entities_list:
                try:
                    entity = self.bigdata_connection.knowledge_graph.autosuggest(entity_name, limit=1)[0]
                    entity_objs.append(entity)
                except Exception as e:
                    print(f"Warning: Autosuggest failed for '{entity_name}': {e}")
                    continue
            print(f"Searching with entities: {[entity.name for entity, orig_str in zip(entity_objs, entities_list) if entity.name in orig_str or orig_str in entity.name]}")
            confirmed_entities = [entity for entity, orig_str in zip(entity_objs, entities_list) if entity.name in orig_str or orig_str in entity.name]
            if confirmed_entities:
                entities = Any(confirmed_entities)
            else:
                entities = None
        else:
            entities = None
        if keywords_list:
            print(f"Searching with keywords: {keywords_list}")
            keywords = Any([Keyword(kw) for kw in keywords_list])
        else:
            keywords = None
        
        queries = [Similarity(sentence) for sentence in search_list]
        if entities:
            queries = [query&entities for query in queries]
        if keywords:
            queries = [query&keywords for query in queries]
        
        all_results = run_search(queries=queries,
                                 date_ranges = date_range,
                                sortby = sortby,
                                scope = scope,
                                limit = chunk_limit,
                                only_results = False,
                                rerank_threshold = None)

        return self.collate_results(all_results)
    
    def collate_results(self, results: List[Tuple[str, Any]]) -> str:
        """
        Collate a list of (query, result) tuples into a single string for LLM context.

        Args:
            results (list): List of (query, result) tuples.

        Returns:
            str: Collated string for LLM context.
        """
        doctexts = []
        for (text_query, date_range), result in results.items():
            for item in text_query.items:
                dictitem = item.to_dict()
                if dictitem['type']=='similarity':
                    sentence = dictitem['value']
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

    @staticmethod
    def _parse_queries(self, queries_json: str) -> List[str]:
        """
        Parse LLM output (JSON or text) into a list of search queries.
        """
        import json
        try:
            queries = json.loads(queries_json)
            if isinstance(queries, list):
                return queries
            elif isinstance(queries, dict) and "search_list" in queries:
                return queries["search_list"]
            elif isinstance(queries, dict) and "queries" in queries:
                return queries["queries"]
        except Exception:
            # Fallback: split by lines
            return [q.strip() for q in queries_json.splitlines() if q.strip()]
        return []

    @staticmethod
    def _make_absolute_date_range(interval: Tuple[str, str]) -> Any:
        """
        Helper to create an AbsoluteDateRange object from a (start, end) tuple.
        """
        return AbsoluteDateRange(start=interval[0], end=interval[1])