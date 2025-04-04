"""
Module that includes all functions to create or extract
information related to the sub-theme tree structure.

Copyright (C) 2024, RavenPack | Bigdata.com. All rights reserved.
Author: Jelena Starovic (jstarovic@ravenpack.com)
"""

import ast
from dataclasses import dataclass
from string import Template
from typing import Any, Dict, List

import graphviz

from bigdata_research_tools.llm import LLMEngine
from bigdata_research_tools.prompts.themes import (
    SourceType,
    theme_generation_default_prompts,
)

themes_default_llm_model_config: Dict[str, Any] = {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "kwargs": {
        "temperature": 0.01,  # Deterministic as possible
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "seed": 42,
        "response_format": {"type": "json_object"},
    },
}


@dataclass
class ThemeTree:
    """
    A hierarchical tree structure rooted in a main theme, branching into distinct sub-themes
    that guide the analyst's research process.

    Each node in the tree provides a unique identifier, a descriptive label, and a summary
    explaining its relevance.

    Args:
        label (str): The name of the theme or sub-theme.
        node (int): A unique identifier for the node.
        summary (str): A brief explanation of the node’s relevance. For the root node
            (main theme), this describes the overall theme; for sub-nodes, it explains their
            connection to the parent theme.
        children (Optional[List[ThemeTree]]): A list of child nodes representing sub-themes.
    """

    label: str
    node: int
    summary: str
    children: List["ThemeTree"] = None

    def __post_init__(self):
        self.children = self.children or []

    def __str__(self) -> str:
        return self.as_string()

    def as_string(self, prefix: str = "") -> str:
        """
        Convert the tree into a string.

        Args:
            prefix (str): prefix to add to each branch.

        Returns:
            str: The tree as a string
        """
        s = prefix + self.label + "\n"

        if not self.children:
            return s

        for i, child in enumerate(self.children):
            is_last = i == (len(self.children) - 1)
            if is_last:
                branch = "└── "
                child_prefix = prefix + "    "
            else:
                branch = "├── "
                child_prefix = prefix + "│   "

            s += prefix + branch
            s += child.as_string(prefix=child_prefix)
        return s

    @staticmethod
    def from_dict(tree_dict: dict) -> "ThemeTree":
        """
        Create a ThemeTree object from a dictionary.

        Args:
            tree_dict (dict): A dictionary representing the `ThemeTree` structure with the following keys:

                - `label` (str): The name of the theme or sub-theme.
                - `node` (int): A unique identifier for the node.
                - `summary` (str): A brief explanation of the node’s relevance.
                - `children` (list, optional): A list of dictionaries representing sub-themes,
                  each following the same structure.

        Returns:
            ThemeTree: The `ThemeTree` object generated from the dictionary.
        """
        theme_tree = ThemeTree(**tree_dict)
        theme_tree.children = [
            ThemeTree.from_dict(child) for child in tree_dict.get("children", [])
        ]
        return theme_tree

    def get_summaries(self) -> List[str]:
        """
        Extract the node summaries from a ThemeTree.

        Returns:
            list[str]: List of all 'summary' values in the tree, including its children.
        """
        summaries = [self.summary]
        for child in self.children:
            summaries.extend(child.get_summaries())
        return summaries

    def get_terminal_summaries(self) -> List[str]:
        """
        Extract summaries from terminal nodes of the tree. 

        Returns:
            The summaries of terminal nodes
        """
        def extract_(node):
            if node.children:
                for child in node.children:
                    extract_(child)
            else:
                summaries.append(node.summary)

        summaries = []
        extract_(self)
        return summaries

    def get_terminal_label_summaries(self) -> Dict[str, str]:
        """
        Extract the summaries from terminal nodes of the tree.

        Returns:
            dict[str, str]: Dictionary with the labels of the ThemeTree as keys and
            their associated summaries as values, only using terminal nodes.
        """
        label_summary = {}
        if not self.children:
            label_summary[self.label] = self.summary
        for child in self.children:
            label_summary.update(child.get_terminal_label_summaries())
        return label_summary

    @staticmethod
    def stringify_label_summaries(label_summaries: Dict[str, str]) -> List[str]:
        """
        Convert the label summaries of a ThemeTree into a list of strings.

        Args:
            label_summaries (dict[str, str]): A dictionary of label summaries of ThemeTree.
                Expected format: {label: summary}.
        Returns:
            List[str]: A list of strings, each one containing a label and its summary.
        """
        return [f"{label}: {summary}" for label, summary in label_summaries.items()]

    def get_terminal_labels(self) -> List[str]:
        """
        Extract the terminal labels from the tree.

        Returns:
        :return: The terminal node labels
        """
        summaries = self.get_terminal_label_summaries()
        summaries = ThemeTree.stringify_label_summaries(summaries)


        return [res.split(":")[0] for res in summaries]

    def print(self, prefix: str = "") -> None:
        """
        Print the tree.

        Args:
            prefix (str): prefix to add to each branch, if any.

        Returns:
            None.
        """
        print(self.as_string(prefix=prefix))

    def visualize(self) -> None:
        """
        Creates a vertical mind map from the given tree structure.
        Uses labels for middle nodes and summaries for leaf/terminal nodes.

        Returns:
            A Graphviz Digraph object for rendering the mindmap.
        """
        mindmap = graphviz.Digraph()

        # Set direction to left-right
        mindmap.attr(
            rankdir='LR', 
            ordering='in',
            splines='curved',
        ) 

        def add_nodes(node):
            # Determine if the node is a terminal (leaf) node
            is_terminal = not node.children
            
            # For terminal nodes, use summary if available, otherwise use label
            # For middle nodes, use the label
            node_text = node.summary if is_terminal and hasattr(node, 'summary') else node.label
            
            # Add a node to the mind map with a box shape
            mindmap.node(
                str(node), 
                node_text, 
                shape="box", 
                style="filled", 
                # Make terminal nodes lighter than middle nodes
                fillcolor='lightgrey' if not is_terminal else '#e0e0e0', 
                margin="0.2,0", 
                align="left", 
                fontsize="12", 
                fontname="Arial",
            )
            
            # If the node has children, recursively add them
            if node.children:
                for child in node.children:
                    # Add an edge from the parent to each child
                    mindmap.edge(
                        str(node), 
                        str(child),
                    )
                    # Recursively add child nodes
                    add_nodes(child)

        # Start with the root node
        add_nodes(self)

        # Return the Graphviz dot object for rendering
        return mindmap

def generate_theme_tree(
    main_theme: str,
    dataset: SourceType,
    focus: str = "",
    llm_model_config: Dict[str, Any] = None,
) -> ThemeTree:
    """
    Generate a `ThemeTree` class from a main theme and a dataset.

    Args:
        main_theme (str): The primary theme to analyze.
        dataset (SourceType): The dataset type to filter by.
        focus (str, optional): Specific aspect(s) to guide sub-theme generation.
        llm_model_config (dict): Configuration for the large language model used to generate themes.
            Expected keys:
            - `provider` (str): The model provider (e.g., `'openai'`).
            - `model` (str): The model name (e.g., `'gpt-4o-mini'`).
            - `kwargs` (dict): Additional parameters for model execution, such as:
            - `temperature` (float)
            - `top_p` (float)
            - `frequency_penalty` (float)
            - `presence_penalty` (float)
            - `seed` (int)
            - etc.

    Returns:
        ThemeTree: The generated theme tree.
    """
    ll_model_config = llm_model_config or themes_default_llm_model_config
    model_str = f"{ll_model_config['provider']}::{ll_model_config['model']}"
    llm = LLMEngine(model=model_str)

    system_prompt_template = theme_generation_default_prompts[dataset]
    system_prompt = Template(system_prompt_template).safe_substitute(
        main_theme=main_theme, focus=focus
    )

    chat_history = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": main_theme},
    ]
    if dataset == SourceType.CORPORATE_DOCS and focus:
        chat_history.append({"role": "user", "content": focus})

    tree_str = llm.get_response(chat_history, **ll_model_config["kwargs"])

    # tree_str = re.sub('```', '', tree_str)
    # tree_str = re.sub('json', '', tree_str)

    # Convert string into dictionary
    tree_dict = ast.literal_eval(tree_str)
    return ThemeTree.from_dict(tree_dict)
