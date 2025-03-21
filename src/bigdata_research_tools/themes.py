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

import pandas as pd

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

    def get_label_summaries(self) -> Dict[str, str]:
        """
        Extract the label summaries from the tree.

        Returns:
            dict[str, str]: Dictionary with all the labels of the ThemeTree as keys and their associated summaries as values.
        """
        label_summary = {self.label: self.summary}
        for child in self.children:
            label_summary.update(child.get_label_summaries())
        return label_summary

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
        Visualize the tree. Will use a plotly treemap.

        Returns:
            None. Will show the tree visualization as a plotly graph.
        """
        try:
            import plotly.express as px
        except ImportError:
            raise ImportError(
                "Missing optional dependency for theme visualization, "
                "please install `bigdata_research_tools[plotly]` to enable them."
            )

        def extract_labels(node: ThemeTree, parent_label=""):
            labels.append(node.label)
            parents.append(parent_label)
            for child in node.children:
                extract_labels(child, node.label)

        labels = []
        parents = []
        extract_labels(self)

        df = pd.DataFrame({"labels": labels, "parents": parents})
        fig = px.treemap(df, names="labels", parents="parents")
        fig.show()


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
        llm_model_config (dict): Configuration for the large language model used to
            generate themes.
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


# def convert_to_node_tree(tree: ThemeTree) -> List[ThemeTree]:
#     """
#     Convert the tree into a node tree.
#
#     :param tree: ThemeTree object. Attributes:
#         - label: The label of the node.
#         - node: The node number.
#         - summary: The summary of the node.
#         - children: list of other ThemeTree objects.
#     :return: The node tree
#     """
#
#     def convert_(node):
#         new_node = {
#             "label": node.label,
#             "value": f"node_{node.node}",
#             "summary": node.summary,
#         }
#         new_node.children = [convert_(child) for child in node.children]
#         return new_node
#
#     return [convert_(tree)]


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


# def extract_node_labels(tree: ThemeTree) -> List[str]:
#     """
#     Extract the node labels from the tree.
#
#     :param tree: ThemeTree object. Attributes:
#         - label: The label of the node.
#         - node: The node number.
#         - summary: The summary of the node.
#         - children: list of other ThemeTree objects.
#     :return: The node labels
#     """
#
#     sums = tree.get_label_summaries()
#     sums = stringify_label_summaries(sums)
#
#     # Remove the top level node
#     sums = sums[1:]
#     sums = [res.split(":")[0] for res in sums]
#
#     return sums
#
#
# def extract_terminal_labels(tree: ThemeTree) -> List[str]:
#     """
#     Extract the terminal labels from the tree.
#
#     :param tree: ThemeTree object. Attributes:
#         - label: The label of the node.
#         - node: The node number.
#         - summary: The summary of the node.
#         - children: list of other ThemeTree objects.
#     :return: The terminal node labels
#     """
#     summaries = tree.get_terminal_label_summaries()
#     summaries = stringify_label_summaries(summaries)
#
#     # Remove the top level node
#     return [res.split(":")[0] for res in summaries]
