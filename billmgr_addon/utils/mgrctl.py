# -*- coding: utf-8 -*-

import subprocess
from typing import List, Union, Optional

from ..utils.logging import setup_logger

logger = setup_logger(__name__)


def mgrctl_exec(cmd: Optional[Union[List[str], str]] = None, capture_output: bool = False, panel: str = "billmgr") -> Union[bytes, None]:
    """
    Выполнить команду через mgrctl
    
    Args:
        cmd: Команда для выполнения (список или строка)
        capture_output: Захватывать ли вывод команды
        panel: Имя панели (по умолчанию billmgr)
    
    Returns:
        bytes если capture_output=True, иначе None
    
    Examples:
        >>> mgrctl_exec(["service.open", "elid=123", "sok=ok"])
        >>> result = mgrctl_exec(["pricelist", "out=xml"], capture_output=True)
    """
    if cmd is None:
        cmd = []
    
    if isinstance(cmd, str):
        cmd = [cmd]
    
    if not isinstance(cmd, list):
        raise ValueError("Команда должна быть списком строк или строкой")

    mgr_call = ["/usr/local/mgr5/sbin/mgrctl", "-m", panel] + cmd
    logger.info(f"mgrctl call: {mgr_call}")
    
    try:
        if capture_output:
            return subprocess.check_output(mgr_call)
        else:
            subprocess.call(mgr_call)
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"mgrctl command failed: {e}")
        raise 