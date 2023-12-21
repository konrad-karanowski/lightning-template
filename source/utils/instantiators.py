from typing import List

import hydra
from lightning import Callback
from lightning.pytorch.loggers import Logger
from omegaconf import DictConfig

from utils import pylogger

logger = pylogger.RankedLogger(__name__, rank_zero_only=True)


def instantiate_callbacks(callbacks_config: DictConfig) -> List[Callback]:
    """Instantiates callbacks from config.

    :param callbacks_config: A DictConfig object containing callback configurations.
    :return: A list of instantiated callbacks.
    """
    callbacks: List[Callback] = []

    if not callbacks_config:
        logger.warning("No callback configs found! Skipping..")
        return callbacks

    if not isinstance(callbacks_config, DictConfig):
        raise TypeError("Callbacks config must be a DictConfig!")

    for _, callback in callbacks_config.items():
        if isinstance(callback, DictConfig) and "_target_" in callback:
            logger.info(f"Instantiating callback <{callback._target_}>")
            callbacks.append(hydra.utils.instantiate(callback))

    return callbacks


def instantiate_loggers(logger_config: DictConfig) -> List[Logger]:
    """Instantiates loggers from config.

    :param logger_config: A DictConfig object containing logger configurations.
    :return: A list of instantiated loggers.
    """
    loggers: List[Logger] = []

    if not logger_config:
        logger.warning("No logger configs found! Skipping...")
        return loggers

    if not isinstance(logger_config, DictConfig):
        raise TypeError("Logger config must be a DictConfig!")

    for _, logg in logger_config.items():
        if isinstance(logg, DictConfig) and "_target_" in logg:
            logger.info(f"Instantiating logger <{logg._target_}>")
            loggers.append(hydra.utils.instantiate(logg))

    return loggers
