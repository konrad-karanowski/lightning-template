from pathlib import Path
from typing import Sequence

import rich
import rich.syntax
import rich.tree
from hydra.core.hydra_config import HydraConfig
from lightning_utilities.core.rank_zero import rank_zero_only
from omegaconf import DictConfig, OmegaConf, open_dict
from rich.prompt import Prompt

from utils import pylogger

log = pylogger.RankedLogger(__name__, rank_zero_only=True)


@rank_zero_only
def print_config_tree(
    config: DictConfig,
    print_order: Sequence[str] = (
        "datamodule",
        "model",
        "callbacks",
        "logger",
        "trainer",
        "paths",
        "extras",
    ),
    resolve: bool = False,
    save_to_file: bool = False,
) -> None:
    """Prints the contents of a DictConfig as a tree structure using the Rich library.

    :param config: A DictConfig composed by Hydra.
    :param print_order: Determines in what order config components are printed. Default is ``("datamodule", "model",
    "callbacks", "logger", "trainer", "paths", "extras")``.
    :param resolve: Whether to resolve reference fields of DictConfig. Default is ``False``.
    :param save_to_file: Whether to export config to the hydra output folder. Default is ``False``.
    """
    style = "dim"
    tree = rich.tree.Tree("CONFIG", style=style, guide_style=style)

    queue = []

    # add fields from `print_order` to queue
    for field in print_order:
        queue.append(field) if field in config else log.warning(
            f"Field '{field}' not found in config. Skipping '{field}' config printing..."
        )

    # add all the other fields to queue (not specified in `print_order`)
    for field in config:
        if field not in queue:
            queue.append(field)

    # generate config tree from queue
    for field in queue:
        branch = tree.add(field, style=style, guide_style=style)

        config_group = config[field]
        if isinstance(config_group, DictConfig):
            branch_content = OmegaConf.to_yaml(config_group, resolve=resolve)
        else:
            branch_content = str(config_group)

        branch.add(rich.syntax.Syntax(branch_content, "yaml"))

    # print config tree
    rich.print(tree)

    # save config tree to file
    if save_to_file:
        with open(Path(config.paths.hydra_output_dir, "config_tree.log"), "w") as file:
            rich.print(tree, file=file)


@rank_zero_only
def enforce_tags(config: DictConfig, save_to_file: bool = False) -> None:
    """Prompts user to input tags from command line if no tags are provided in config.

    :param config: A DictConfig composed by Hydra.
    :param save_to_file: Whether to export tags to the hydra output folder. Default is ``False``.
    """
    if not config.get("core").get("tags"):
        if "id" in HydraConfig().cfg.hydra.job:
            raise ValueError("Specify tags before launching a multirun!")

        log.warning("No tags provided in config. Prompting user to input tags...")
        tags = Prompt.ask("Enter a list of comma separated tags", default="dev")
        tags = [t.strip() for t in tags.split(",") if t != ""]

        with open_dict(config):
            config.core.tags = tags

        log.info(f"Tags: {config.tags}")

    if save_to_file:
        with open(Path(config.paths.hydra_output_dir, "tags.log"), "w") as file:
            rich.print(config.core.tags, file=file)
