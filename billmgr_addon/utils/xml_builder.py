# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from xml.etree.ElementTree import Element


class XMLBuilder:
    """
    Сборщик XML файлов для BILLmanager плагинов

    Собирает XML файлы из директории xml/src в единый build.xml файл,
    обрабатывая импорты и подстановки.
    """

    def __init__(self, src_path: Optional[Path] = None, build_path: Optional[Path] = None):
        """
        Инициализировать сборщик

        Args:
            src_path: Путь к исходным XML файлам (по умолчанию xml/src)
            build_path: Путь к собранному XML (по умолчанию xml/build.xml)
        """
        self.cwd_path = Path.cwd()
        self.xml_src_path = src_path or self.cwd_path / "xml" / "src"
        self.xml_build_path = build_path or self.cwd_path / "xml" / "build.xml"
        self.main_entry_path = self.xml_src_path / "main.xml"

    def build(self) -> Path:
        """
        Собрать XML файлы

        Returns:
            Path: Путь к собранному XML файлу
        """
        if not self.main_entry_path.exists():
            raise FileNotFoundError(f"Главный XML файл не найден: {self.main_entry_path}")

        # Создаем директорию для сборки если её нет
        self.xml_build_path.parent.mkdir(parents=True, exist_ok=True)

        # Получаем главную запись и выполняем импорты
        main_entry = self._get_entry_from_file(self.main_entry_path)
        main_entry.execute_import()

        # Записываем результат
        ET.ElementTree(main_entry.root).write(self.xml_build_path, encoding="UTF-8", method="xml")

        return self.xml_build_path

    def _get_entry_from_file(self, entry_path: Path) -> "XmlEntry":
        """
        Получить XML запись из файла

        Args:
            entry_path: Путь к XML файлу

        Returns:
            XmlEntry: Объект XML записи
        """
        if not entry_path.is_absolute():
            raise ValueError(f"Entry file path {entry_path} must be absolute")

        if not entry_path.exists():
            raise FileNotFoundError(f"Entry XML file is not found in {entry_path}")

        try:
            with open(entry_path, "r", encoding="utf-8") as f:
                content = f.read()
            entry_root = ET.fromstring(content)
        except ET.ParseError as e:
            raise ValueError(f"Could not parse XML input from {entry_path}: {e}")

        entry = XmlEntry(entry_path, entry_root)
        return entry


class XmlEntry:
    """
    Запись XML файла с поддержкой импортов
    """

    def __init__(
        self, absolute_path: Path, root_element: Element, parent_entry: Optional["XmlEntry"] = None
    ):
        """
        Инициализировать XML запись

        Args:
            absolute_path: Абсолютный путь к файлу
            root_element: Корневой XML элемент
            parent_entry: Родительская запись
        """
        self.path = Path(absolute_path)
        self.root = root_element
        self.parent = parent_entry
        self.children = []
        self.is_import_executed = False
        self.import_element_index = None

    def has_parent_path(self, path: Path) -> bool:
        """
        Проверить есть ли путь среди родителей (для предотвращения циклических ссылок)

        Args:
            path: Путь для проверки

        Returns:
            bool: True если путь найден среди родителей
        """
        current_parent = self.parent
        while current_parent is not None:
            if current_parent.path == path:
                return True
            current_parent = current_parent.parent
        return False

    def execute_import(self) -> None:
        """
        Выполнить импорты в XML файле
        """
        if self.is_import_executed:
            print("Import can be executed only once per entry")
            return

        xml_src_path = (
            self.path.parent.parent if self.path.parent.name == "src" else self.path.parent
        )

        import_elements = self.root.findall("./import")
        for import_element in import_elements:
            import_element_index = list(self.root).index(import_element)
            import_element_string = ET.tostring(import_element, encoding="unicode", method="xml")
            import_path = import_element.get("path")
            import_as = import_element.get("as")

            if import_path is None:
                raise ValueError(
                    f'Attribute "path" is not found in {import_element_string}\nFailed to import in {self.path}'
                )

            if import_as is not None and import_as == "":
                raise ValueError(
                    f'Attribute "as" in {import_element_string} can not be empty string\nFailed to import in {self.path}'
                )

            # Обработка путей начинающихся с @/
            use_xml_src_path = False
            if import_path.startswith("@/"):
                import_path = import_path[2:]
                use_xml_src_path = True

            import_path = Path(import_path)
            if import_path.is_absolute():
                raise ValueError(
                    f"{import_element_string} path must be relative\nFailed to import in {self.path}"
                )

            # Добавляем расширение .xml если его нет
            if import_path.suffix != ".xml":
                import_path = Path(f"{import_path}.xml")

            # Определяем полный путь к импортируемому файлу
            try:
                if use_xml_src_path:
                    import_file_path = xml_src_path.joinpath(import_path).resolve()
                else:
                    import_file_path = self.path.parent.joinpath(import_path).resolve()

                if not import_file_path.is_file():
                    raise FileNotFoundError()

                # Проверяем что файл находится в правильной директории
                is_relative = (
                    xml_src_path == import_file_path or xml_src_path in import_file_path.parents
                )
                if not is_relative:
                    raise FileNotFoundError()

            except Exception:
                raise ValueError(
                    f"{import_element_string} must be valid file path inside xml_src_path\nFailed to import in {self.path}"
                )

            # Проверяем циклические ссылки
            if self.has_parent_path(import_file_path):
                raise ValueError(
                    f"{import_element_string} circular reference in xml_src_path\nFailed to import in {self.path}"
                )

            # Создаем дочернюю запись и выполняем импорт
            child_entry = XMLBuilder()._get_entry_from_file(import_file_path)
            child_entry.parent = self
            child_entry.import_element_index = import_element_index
            child_entry.execute_import()

            # Заменяем элемент import на содержимое импортированного файла
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
