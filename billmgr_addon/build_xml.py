#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Сборщик XML конфигурации для BILLmanager плагинов

Универсальный сборщик XML файлов с поддержкой импортов.
Адаптирован из cloud-infrastructure-reselling-addon/build_xml.py
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.etree.ElementTree import Element


def get_entry_from_file(entry_path) -> "XmlEntry":
    """Получить XML запись из файла"""
    if not Path(entry_path).is_absolute():
        sys.exit(f"Entry file path {entry_path} must be absolute")

    absolute_path = Path(entry_path).resolve()
    entry_xml_file = None
    try:
        entry_xml_file = open(absolute_path, "r", encoding="utf-8")
    except IOError:
        sys.exit(f"Entry XML file is not found in {absolute_path}")

    entry_root = None
    try:
        entry_root = ET.fromstring(entry_xml_file.read())
    except ET.ParseError:
        sys.exit("Could not parse XML input string from entry file.")

    entry = XmlEntry(entry_path, entry_root)
    return entry


class XmlEntry:
    """Класс для работы с XML записями и импортами"""

    def __init__(self, absolute_path, root_element, parent_entry: "XmlEntry" = None):
        self.path: Path = absolute_path
        self.root: Element = root_element
        self.parent: "XmlEntry" = parent_entry
        self.children: list = []
        self.is_import_executed = False
        self.import_element_index: int = None

    def has_parent_path(self, path):
        """Проверить наличие циклической зависимости"""
        current_parent = self.parent
        has_path = False
        while current_parent is not None and not has_path:
            has_path = current_parent.path == path
            current_parent = current_parent.parent

        return has_path

    def execute_import(self, xml_src_path):
        """Выполнить импорт зависимостей"""
        if self.is_import_executed:
            print("Import can be executed only once per entry")
            return

        import_elements = self.root.findall("./import")
        for import_element in import_elements:
            import_element_index = list(self.root).index(import_element)
            import_element_string = ET.tostring(import_element, encoding="unicode", method="xml")
            import_path = import_element.get("path")
            import_as = import_element.get("as")

            if import_path is None:
                sys.exit(
                    f'Attribute "path" is not found in {import_element_string}\nFailed to import in {self.path}'
                )

            if import_as is not None and import_as == "":
                sys.exit(
                    f'Attribute "as" in {import_element_string} can not be empty string\nFailed to import in {self.path}'
                )

            use_xml_src_path = False
            if import_path.startswith("@/"):
                import_path = import_path[2:]
                use_xml_src_path = True

            import_path = Path(import_path)
            if import_path.is_absolute():
                sys.exit(
                    f"{import_element_string} path must be relative\nFailed to import in {self.path}"
                )

            if import_path.suffix != ".xml":
                import_path = Path(f"{import_path}.xml")

            import_file_path = None
            try:
                if use_xml_src_path:
                    import_file_path = xml_src_path.joinpath(import_path).resolve()
                else:
                    import_file_path = self.path.parent.joinpath(import_path).resolve()

                if not import_file_path.is_file():
                    raise FileNotFoundError()

                # Проверяем что файл находится внутри xml_src_path
                is_relative = (
                    xml_src_path == import_file_path or xml_src_path in import_file_path.parents
                )
                if not is_relative:
                    raise FileNotFoundError()
            except Exception as e:
                print(e)
                sys.exit(
                    f"{import_element_string} must be valid file path inside xml_src_path\nFailed to import in {self.path}"
                )

            if self.has_parent_path(import_file_path):
                sys.exit(
                    f"{import_element_string} circular reference in xml_src_path\nFailed to import in {self.path}"
                )

            child_entry = get_entry_from_file(import_file_path)
            child_entry.parent = self
            child_entry.import_element_index = import_element_index
            child_entry.execute_import(xml_src_path)

            # Заменяем import элементы на содержимое импортированных файлов
            self.root.remove(import_element)
            index_counter = 0
            for child_element in list(child_entry.root):
                if import_as is not None:
                    if child_element.tag == "metadata":
                        child_element.set("name", import_as)
                    elif child_element.tag == "lang":
                        messages_element = child_element.find("messages")
                        if messages_element:
                            messages_element.set("name", import_as)

                self.root.insert(import_element_index + index_counter, child_element)
                index_counter += 1

            self.children.append(child_entry)
            print(f"imported - {import_file_path}")

        self.is_import_executed = True


def build_xml(project_root=None):
    """
    Собрать XML конфигурацию

    Args:
        project_root: Корневая директория проекта (по умолчанию текущая)
    """
    if project_root is None:
        project_root = Path.cwd()
    else:
        project_root = Path(project_root)

    xml_src_path = project_root / "xml" / "src"
    xml_build_path = project_root / "xml" / "build.xml"
    main_entry_path = xml_src_path / "main.xml"

    # Проверяем наличие необходимых файлов
    if not main_entry_path.exists():
        sys.exit(f"Main XML file not found: {main_entry_path}")

    # Создаем директорию для результата
    xml_build_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building XML from {xml_src_path}...")

    # Обрабатываем главный файл
    main_entry = get_entry_from_file(main_entry_path)
    main_entry.execute_import(xml_src_path)

    # Сохраняем результат
    ET.ElementTree(main_entry.root).write(
        xml_build_path, encoding="UTF-8", method="xml", xml_declaration=True
    )

    print(f"XML built successfully: {xml_build_path}")
    return xml_build_path


def main():
    """Главная функция сборщика XML"""
    import argparse

    parser = argparse.ArgumentParser(description="Build XML configuration for BILLmanager plugin")
    parser.add_argument("--project-root", help="Project root directory", default=".")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        result = build_xml(args.project_root)
        if args.verbose:
            print(f"Build completed: {result}")
    except Exception as e:
        print(f"Build failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
