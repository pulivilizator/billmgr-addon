# -*- coding: utf-8 -*-

import re
from typing import Union

try:
    import MySQLdb
    MYSQL_AVAILABLE = True
except ImportError:
    try:
        import pymysql as MySQLdb
        MySQLdb.install_as_MySQLdb()
        MYSQL_AVAILABLE = True
    except ImportError:
        MYSQL_AVAILABLE = False
        MySQLdb = None

from flask import current_app, g, appcontext_pushed
from types import SimpleNamespace
import logging


def get_db(alias: str = None):
    """
    Получить экземпляр базы данных из контекста Flask
    
    Args:
        alias: Псевдоним подключения к БД (по умолчанию основное подключение)
        
    Returns:
        DB: Экземпляр базы данных
    """
    namespace_id = '_db'
    if alias is not None and alias != '':
        namespace_id = f'_db_{alias}'
    db_namespace = getattr(g, namespace_id)
    db_config = db_namespace.config
    
    if not db_namespace.instance:
        db_namespace.instance = DB(db_config=db_config)
    return db_namespace.instance


class FlaskDbExtension:
    """
    Расширение Flask для работы с базой данных
    
    Автоматически управляет подключениями к БД в контексте приложения.
    Поддерживает множественные подключения через aliases.
    """
    
    def __init__(self):
        self.db_config = None
        self.namespace_id = None

    def init_app(self, app, db_config=None, alias=None):
        """
        Инициализировать расширение с Flask приложением
        
        Args:
            app: Flask приложение
            db_config: Конфигурация БД (DBConfig)
            alias: Псевдоним для подключения
        """
        self.db_config = db_config
        if self.db_config is None:
            self.db_config = DBConfig.from_flask_app(app, prefix='DB')

        self.namespace_id = '_db'
        if alias is not None and alias != '':
            self.namespace_id = f'_db_{alias}'

        appcontext_pushed.connect(self.appcontext_pushed_handler, app)
        app.teardown_appcontext(self.teardown_appcontext_handler)

        logging.debug(f'DB extension initialized with "{self.namespace_id}" namespace')

    def appcontext_pushed_handler(self, sender):
        """Обработчик создания контекста приложения"""
        try:
            db_namespace = SimpleNamespace()
            db_namespace.config = self.db_config
            db_namespace.instance = None
            setattr(g, self.namespace_id, db_namespace)
        except Exception as e:
            logging.exception(e)

    def teardown_appcontext_handler(self, error):
        """Обработчик завершения контекста приложения"""
        db_namespace = getattr(g, self.namespace_id)
        if db_namespace.instance:
            db_namespace.instance.close()

    def on_extension_close(self):
        """Обработчик закрытия расширения"""
        logging.debug(f'DB extension with "{self.namespace_id}" namespace is closed')


class DBConfig:
    """
    Конфигурация подключения к базе данных
    
    Поддерживает чтение конфигурации из файлов панелей управления,
    Flask приложения или прямую инициализацию.
    """
    
    panel_config_locations = {
        'billmgr': '/usr/local/mgr5/etc/billmgr.conf.d/db.conf',
        'dcimgr': '/usr/local/mgr5/etc/dcimgr.conf.d/db.conf',
        'vmmgr': '/usr/local/mgr5/etc/vmmgr.conf.d/db.conf',
        'ispmgr': '/usr/local/mgr5/etc/ispmgr.conf.d/db.conf'
    }

    def __init__(self, host='localhost', database=None, user=None, password=None, use_unicode=True):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.use_unicode = use_unicode

    @classmethod
    def from_panel_config(cls, config_path, use_unicode=True):
        """
        Создать конфигурацию из файла панели управления
        
        Args:
            config_path: Путь к файлу конфигурации
            use_unicode: Использовать Unicode
            
        Returns:
            DBConfig: Экземпляр конфигурации
        """
        config = {}
        try:
            with open(config_path, 'r') as fh:
                read_data = fh.read()
            matches = re.findall(r"^((\w+) (\w+))", read_data, re.M)
            for line in matches:
                config[line[1]] = line[2]
        except Exception as e:
            raise

        return cls(
            host=config['DBHost'], 
            database=config['DBName'],
            user=config['DBUser'], 
            password=config['DBPassword'],
            use_unicode=use_unicode
        )

    @classmethod
    def from_panel_name(cls, panel_name, use_unicode=True):
        """
        Создать конфигурацию для известной панели управления
        
        Args:
            panel_name: Имя панели (billmgr, ispmgr, etc.)
            use_unicode: Использовать Unicode
            
        Returns:
            DBConfig: Экземпляр конфигурации
        """
        config_path = cls.panel_config_locations.get(panel_name, None)
        if config_path is None:
            raise ValueError('Unknown panel name')
        return cls.from_panel_config(config_path, use_unicode=use_unicode)

    @classmethod
    def from_flask_app(cls, app, prefix='DB', use_unicode=True):
        """
        Создать конфигурацию из настроек Flask приложения
        
        Args:
            app: Flask приложение
            prefix: Префикс настроек в config
            use_unicode: Использовать Unicode
            
        Returns:
            DBConfig: Экземпляр конфигурации
        """
        return cls(
            host=app.config.get(f'{prefix}_HOST', None),
            database=app.config.get(f'{prefix}_DATABASE', None),
            user=app.config.get(f'{prefix}_USER', None),
            password=app.config.get(f'{prefix}_PASSWORD', None),
            use_unicode=use_unicode
        )


class DBResult:
    """
    Обертка для результатов SQL запросов
    
    Предоставляет удобные методы для получения данных из курсора.
    """
    
    def __init__(self, cursor):
        self.cursor = cursor

    def one_or_none(self):
        """
        Получить одну запись или None
        
        Returns:
            dict or None: Первая запись результата или None
        """
        result = self.cursor.fetchone()
        self.cursor.close()
        return result

    def all(self) -> list:
        """
        Получить все записи результата
        
        Returns:
            list: Список всех записей
        """
        result = self.cursor.fetchall()
        if result:
            return [*result]
        else:
            return []

    def chunks(self, size=0):
        """
        Получить записи порциями
        
        Args:
            size: Размер порции
            
        Yields:
            list: Порция записей
        """
        try:
            if size > 0:
                while True:
                    rows = self.cursor.fetchmany(size)
                    if not rows:
                        break
                    yield rows
            else:
                raise ValueError('Chunk size can not be zero')
        except Exception as e:
            raise


class DB:
    """
    Основной класс для работы с базой данных
    
    Предоставляет методы для выполнения SQL запросов и управления подключением.
    """
    
    def __init__(self, **kwargs):
        self.connection = None
        self.connect(**kwargs)
        self.database = None

    def connect(self, db_config: DBConfig = None, host='localhost', user=None, password=None, database=None, use_unicode=True):
        """
        Установить подключение к базе данных
        
        Args:
            db_config: Объект конфигурации DBConfig
            host: Хост БД
            user: Пользователь БД
            password: Пароль БД
            database: Имя БД
            use_unicode: Использовать Unicode
            
        Returns:
            MySQLdb.Connection: Объект подключения
        """
        if db_config is None:
            db_config = DBConfig(
                host=host, database=database,
                user=user, password=password,
                use_unicode=use_unicode
            )
        
        if self.connection:
            self.connection.close()

        if not MYSQL_AVAILABLE:
            raise ImportError("MySQL client not available. Install with: pip install billmgr-addon or pip install billmgr-addon[pymysql]")
        
        try:
            self.connection = MySQLdb.connect(
                host=db_config.host, db=db_config.database,
                user=db_config.user, passwd=db_config.password,
                charset='utf8', use_unicode=db_config.use_unicode
            )
            return self.connection
        except Exception as e:
            raise

    def close(self):
        """Закрыть подключение к базе данных"""
        if self.connection:
            self.connection.close()
            self.connection = None

    @property
    def cursor(self):
        """Получить курсор для выполнения запросов"""
        return self.connection.cursor()

    def select_query(self, sql, values: dict = None):
        """
        Выполнить SELECT запрос
        
        Args:
            sql: SQL запрос
            values: Параметры запроса
            
        Returns:
            DBResult: Результат запроса
        """
        cursor = self.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql, values)
        return DBResult(cursor)

    def insert_query(self, sql, values: dict = None):
        """
        Выполнить INSERT запрос
        
        Args:
            sql: SQL запрос
            values: Параметры запроса
            
        Returns:
            int: ID вставленной записи
        """
        cursor = self.connection.cursor()
        cursor.execute(sql, values)
        self.connection.commit()
        return cursor.lastrowid

    def update_query(self, sql, values: dict = None):
        """
        Выполнить UPDATE запрос
        
        Args:
            sql: SQL запрос
            values: Параметры запроса
            
        Returns:
            int: Количество затронутых строк
        """
        cursor = self.connection.cursor()
        cursor.execute(sql, values)
        self.connection.commit()
        return cursor.rowcount

    def delete_query(self, sql, values: dict = None):
        """
        Выполнить DELETE запрос
        
        Args:
            sql: SQL запрос
            values: Параметры запроса
            
        Returns:
            int: Количество удаленных строк
        """
        cursor = self.connection.cursor()
        cursor.execute(sql, values)
        self.connection.commit()
        return cursor.rowcount

    def insert_many(self, sql, values_list: Union[list, tuple]):
        """
        Выполнить множественную вставку
        
        Args:
            sql: SQL запрос
            values_list: Список параметров для вставки
            
        Returns:
            int: Количество вставленных строк
        """
        cursor = self.connection.cursor()
        cursor.executemany(sql, values_list)
        self.connection.commit()
        return cursor.rowcount 