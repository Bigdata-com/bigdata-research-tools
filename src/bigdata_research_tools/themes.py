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
    label: str
    node: int
    summary: str
    children: List["ThemeTree"] = None

    def __post_init__(self):
        self.children = self.children or []

    @staticmethod
    def from_dict(tree_dict: dict) -> "ThemeTree":
        theme_tree = ThemeTree(**tree_dict)
        theme_tree.children = [
            ThemeTree.from_dict(child) for child in tree_dict.get("children", [])
        ]
        return theme_tree

    def get_summaries(self) -> List[str]:
        """
        Extract the node summaries from a ThemeTree.

        :return: List of all 'summary' values in the tree, including its children.
        """
        summaries = [self.summary]
        for child in self.children:
            summaries.extend(child.get_summaries())
        return summaries

    def get_label_summaries(self) -> Dict[str, str]:
        """
        Extract the label summaries from the tree.

        :return: Dictionary with all the labels of the Tree as keys and their
            associated summaries as values.
        """
        label_summary = {self.label: self.summary}
        for child in self.children:
            label_summary.update(child.get_label_summaries())
        return label_summary

    def get_terminal_label_summaries(self) -> Dict[str, str]:
        """
        Extract the summaries from terminal nodes of the tree.

        :return: Dictionary with the labels of the Tree as keys and their
            associated summaries as values, but only for terminal nodes.
        """
        label_summary = {}
        if not self.children:
            label_summary[self.label] = self.summary
        for child in self.children:
            label_summary.update(child.get_terminal_label_summaries())
        return label_summary


def generate_theme_tree(
    main_theme: str,
    dataset: SourceType,
    focus: str = "",
    llm_model_config: Dict[str, Any] = None,
) -> ThemeTree:
    """
    Generate themes based on the main theme.

    :param main_theme: The main theme to analyze.
    :param dataset: The type of dataset to filter by.
    :param focus: The focus(es), if any.
    :param llm_model_config: The large language model configuration to
        generate the themes.
        Expected keys:
            - provider: The provider of the model, e.g. 'openai'.
            - model: The model name, e.g. 'gpt-4o-mini'.
            - kwargs: Extra arguments to execute the model, e.g.:
                - temperature.
                - top_p.
                - frequency_penalty.
                - presence_penalty.
                - seed.
                - etc.
                See `LLMEngine.get_response()` for more details.
    :return: ThemeTree object. Attributes:
        - label: The label of the node.
        - node: The node number.
        - summary: The summary of the node.
        - children: list of other ThemeTree objects.
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
    Convert the label summaries into a list of strings.

    :param label_summaries: A dictionary of label summaries.
    :return: A list of strings.
    """
    return [f"{label}: {summary}" for label, summary in label_summaries.items()]


def extract_node_labels(tree: ThemeTree) -> List[str]:
    """
    Extract the node labels from the tree.

    :param tree: ThemeTree object. Attributes:
        - label: The label of the node.
        - node: The node number.
        - summary: The summary of the node.
        - children: list of other ThemeTree objects.
    :return: The node labels
    """

    sums = tree.get_label_summaries()
    sums = stringify_label_summaries(sums)

    # Remove the top level node
    sums = sums[1:]
    sums = [res.split(":")[0] for res in sums]

    return sums


def extract_terminal_labels(tree: ThemeTree) -> List[str]:
    """
    Extract the terminal labels from the tree.

    :param tree: ThemeTree object. Attributes:
        - label: The label of the node.
        - node: The node number.
        - summary: The summary of the node.
        - children: list of other ThemeTree objects.
    :return: The terminal node labels
    """
    summaries = tree.get_terminal_label_summaries()
    summaries = stringify_label_summaries(summaries)

    # Remove the top level node
    return [res.split(":")[0] for res in summaries]


def print_tree(node: ThemeTree, prefix="") -> None:
    """
    Print the tree.

    :param node: The node to print. It can be the entire tree. Attributes:
        - label: The label of the node.
        - node: The node number.
        - summary: The summary of the node.
        - children: list of other ThemeTree objects.
    :param prefix: Prefix to add to the branches.
    :return: None. Will print the tree.
    """
    print(prefix + node.label)

    if not node.children:
        return

    for i, child in enumerate(node.children):
        is_last = i == (len(node.children) - 1)
        if is_last:
            branch = "└── "
            child_prefix = prefix + "    "
        else:
            branch = "├── "
            child_prefix = prefix + "│   "

        print(prefix + branch, end="")
        print_tree(child, child_prefix)


def visualize_tree(tree: ThemeTree) -> None:
    """
    Visualize the tree.

    :param tree: ThemeTree object. Attributes:
        - label: The label of the node.
        - node: The node number.
        - summary: The summary of the node.
        - children: list of other ThemeTree objects.
    :return: None. Will show the tree visualization as a plotly graph.
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
    extract_labels(tree)

    df = pd.DataFrame({"labels": labels, "parents": parents})
    fig = px.treemap(df, names="labels", parents="parents")
    fig.show()
