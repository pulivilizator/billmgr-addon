#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI интерфейс для BILLmanager плагинов

Универсальный CLI обработчик для плагинов.
"""

import os
import sys
from pathlib import Path


def create_cli_app_from_module(module_name):
    """
    Создать CLI приложение из модуля проекта

    Args:
        module_name: Имя модуля проекта (например, 'my_plugin')
    """
    try:
        # Импортируем модуль проекта
        project_module = __import__(module_name)

        # Пробуем найти функцию создания CLI приложения
        if hasattr(project_module, "create_cli_app"):
            return project_module.create_cli_app()
        elif hasattr(project_module, "app"):
            return project_module.app
        else:
            raise ImportError(
                f"Module {module_name} doesn't have 'create_cli_app' function or 'app' object"
            )

    except ImportError:
        # Fallback - создаем простое приложение
        from billmgr_addon import create_cli_app

        return create_cli_app()


def main():
    """Главная функция CLI интерфейса"""
    # Определяем имя проекта из переменной окружения или из директории
    project_name = os.environ.get("PLUGIN_NAME")

    if not project_name:
        # Пробуем определить из текущей директории
        cwd = Path.cwd()
        if (cwd / "setup.py").exists():
            # Читаем setup.py чтобы найти имя пакета
            try:
                import re

                setup_content = (cwd / "setup.py").read_text()
                match = re.search(r"name=['\"]([^'\"]+)['\"]", setup_content)
                if match:
                    project_name = match.group(1).replace("-", "_")
            except:
                pass

        if not project_name:
            project_name = cwd.name.replace("-", "_")

    # Добавляем текущую директорию в Python path
    sys.path.insert(0, str(Path.cwd()))

    try:
        app = create_cli_app_from_module(project_name)

        # Запускаем CLI в контексте приложения (адаптировано из исходного cli.py)
        with app.app_context():
            app.cli.main()

    except Exception as e:
        print(f"CLI Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
