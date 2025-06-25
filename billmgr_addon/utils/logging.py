# -*- coding: utf-8 -*-

import logging


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Настроить логгер для BILLmanager плагина
    
    Args:
        name: Имя логгера
        level: Уровень логирования
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 