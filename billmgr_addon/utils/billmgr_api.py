# -*- coding: utf-8 -*-
# type: ignore

import httpx
from dataclasses import dataclass
from flask import request, current_app
from flask_login import current_user
import ipaddress
from typing import List, Union, Optional, Type
import ssl
import json
from ..utils.logging import setup_logger
from ..utils.serialization import CustomJSONEncoder

# Настройка логгера
logger = setup_logger(__name__)


class BillmgrError(Exception):
    """Базовая ошибка API BILLmanager"""
    def __init__(self, message, original_exception=None):
        self.message = message
        self.original_exception = original_exception

    def __str__(self):
        if self.message:
            return self.message
        else:
            return f'{self.__class__}: error occured'


class BillmgrRequestError(BillmgrError):
    """Ошибка HTTP запроса к API"""
    pass


class BillmgrApiError(BillmgrError):
    """Ошибка ответа API"""
    pass


def get_billmgr_api_as_current_user():
    """
    Получить API клиент для текущего пользователя
    
    Returns:
        BillmgrAPI: Клиент API для текущего пользователя
    """
    ip_address = ipaddress.ip_address(str(request.headers.get('X-Forwarded-For', request.remote_addr)))
    billmgr_api = BillmgrAPI(
        url=current_app.config.get('BILLMGR_API_URL'),
        interface=current_app.config.get('BILLMGR_API_USE_INTERFACE'),
        cookies={'billmgrses5': current_user.session_id},
        headers={
            'X-Forwarded-For': str(ip_address),
            'X-Forwarded-Secret': current_app.config.get('FORWARDED_SECRET')
        }
    )
    return billmgr_api


def get_billmgr_api_as_config_user():
    """
    Получить API клиент для пользователя из конфигурации
    
    Returns:
        BillmgrAPI: Клиент API для пользователя из конфига
    """
    billmgr_api = BillmgrAPI(
        auth_info=[
            current_app.config.get('BILLMGR_API_USER'),
            current_app.config.get('BILLMGR_API_PASSWORD')
        ],
        url=current_app.config.get('BILLMGR_API_URL'),
        interface=current_app.config.get('BILLMGR_API_USE_INTERFACE')
    )
    return billmgr_api


class BillmgrAPIResponse:
    """Ответ API BILLmanager"""

    def __init__(self, doc, default_format=None, result_type: str = None):
        if doc:
            self._doc = doc
        else:
            raise BillmgrApiError('Invalid response data format')

        self.default_format = default_format
        self.result_type = "item"
        if result_type is not None:
            self.result_type = result_type
    
    @property
    def doc(self):
        """Получить документ ответа"""
        return self._doc

    def _format_value(self, name, value, formatter_type=None):
        """
        Отформатировать значение согласно указанному форматтеру
        
        Args:
            name: Имя поля
            value: Значение
            formatter_type: Тип форматтера
            
        Returns:
            Отформатированное значение
        """
        formatter = None
        if formatter_type is None:
            if self.default_format and name in self.default_format:
                formatter = self.default_format[name]
        else:
            formatter = formatter_type

        if callable(formatter):
            return formatter(value)
        elif 'switch' == formatter:
            return value == 'on'
        else:
            return value

    def result(self, item_format=None):
        """
        Получить результат в зависимости от типа
        
        Args:
            item_format: Форматтеры для полей
            
        Returns:
            Результат (элемент или список)
        """
        if self.result_type == "item":
            return self.get_item(item_format=item_format)
        elif self.result_type == "list":
            return self.get_list(item_format=item_format)
        else:
            raise BillmgrApiError('Unknown result type')
        
    def raw_result(self):
        """Получить сырой результат"""
        return self.doc

    def get_list(self, item_format=None):
        """
        Получить список элементов
        
        Args:
            item_format: Форматтеры для полей
            
        Returns:
            List: Список элементов
        """
        items = []
        if 'p_elems' in self._doc:
            if 'elem' in self._doc:
                for elem in self._doc['elem']:
                    item = {}
                    for name, value in elem.items():
                        if '$orig' in value:
                            item[name] = value['$orig']
                        elif '$' in value:
                            item[name] = value['$']
                        else:
                            continue

                        formatter_type = None
                        if item_format and name in item_format:
                            formatter_type = item_format[name]
                        item[name] = self._format_value(name, item[name], formatter_type)

                    items.append(item)

            return items
        else:
            return None
    
    def get_item(self, item_format=None):
        """
        Получить один элемент
        
        Args:
            item_format: Форматтеры для полей
            
        Returns:
            Dict: Элемент
        """
        item = {}
        for name, value in self._doc.items():
            if '$' in value:
                item[name] = value['$']
            else:
                continue

            formatter_type = None
            if item_format and name in item_format:
                formatter_type = item_format[name]
            item[name] = self._format_value(name, item[name], formatter_type)

        return item


class BillmgrAPI:
    """Клиент API BILLmanager"""
    
    @dataclass
    class PreparedRequest:
        """Подготовленный запрос"""
        method: str
        url: str
        params: Optional[dict]
        json_data: Optional[dict]
        headers: Optional[dict]
        cookies: Optional[dict]
        timeout: Optional[int]

    class ApiRequest:
        """Базовый класс для запросов к API"""
        method: str
        func_name: str
        result_type: str = "item"  # item, list
        schema: Optional[type] = None

        def __init__(self):
            self.params = None
            self.data = None
            self.headers = None
            self.cookies = None

        def send(self, client: "BillmgrAPI", timeout=None) -> BillmgrAPIResponse:
            """
            Отправить синхронный запрос
            
            Args:
                client: Клиент API
                timeout: Таймаут запроса
                
            Returns:
                BillmgrAPIResponse: Ответ API
            """
            built_request = client.build_request(
                self.__class__.method, self.__class__.func_name, 
                params=self.params, data=self.data,
                headers=self.headers, cookies=self.cookies, 
                timeout=timeout, async_session=False
            )

            try:
                response: httpx.Response = client.request_session.send(built_request)
            except httpx.NetworkError as e:
                raise BillmgrRequestError('Network error occured', original_exception=e)
            except httpx.TimeoutException as e:
                raise BillmgrRequestError('Request has been interrupted by timeout', original_exception=e)
            except (httpx.RequestError, Exception) as e:
                raise BillmgrRequestError('Unknown error during request', original_exception=e)

            return client._handle_response(response, result_type=self.__class__.result_type)

        async def send_async(self, client: "BillmgrAPI", timeout=None) -> BillmgrAPIResponse:
            """
            Отправить асинхронный запрос
            
            Args:
                client: Клиент API
                timeout: Таймаут запроса
                
            Returns:
                BillmgrAPIResponse: Ответ API
            """
            built_request = client.build_request(
                self.__class__.method, self.__class__.func_name, 
                params=self.params, data=self.data,
                headers=self.headers, cookies=self.cookies, 
                timeout=timeout, async_session=True
            )

            try:
                response: httpx.Response = await client.async_request_session.send(built_request)
            except httpx.NetworkError as e:
                raise BillmgrRequestError('Network error occured', original_exception=e)
            except httpx.TimeoutException as e:
                raise BillmgrRequestError('Request has been interrupted by timeout', original_exception=e)
            except (httpx.RequestError, Exception) as e:
                raise BillmgrRequestError('Unknown error during request', original_exception=e)

            return client._handle_response(response, result_type=self.__class__.result_type)

    def __init__(self, url: str, session_id: Optional[str] = None, auth_info: Optional[list] = None, interface: Optional[str] = None,
                 verify_ssl: Union[bool, ssl.SSLContext] = True, headers: Optional[dict] = None,
                 cookies: Optional[dict] = None, timeout: Optional[float] = None):
        """
        Инициализировать клиент API
        
        Args:
            url: URL API BILLmanager
            session_id: ID сессии для авторизации
            auth_info: Данные авторизации [логин, пароль]
            interface: Интерфейс для подключения
            verify_ssl: Проверка SSL
            headers: Дополнительные заголовки
            cookies: Cookies для авторизации
            timeout: Таймаут запросов
        """
        self.url = url
        self.interface = interface
        self.headers = {}
        if headers:
            self.headers = headers

        self.cookies = {}
        if cookies:
            self.cookies = cookies

        self.verify_ssl = verify_ssl
        self.timeout = timeout
    
        self.session_id = session_id
        self.auth_info = None
        if auth_info:
            self.auth_info = [*auth_info]

        self.request_session: httpx.Client = None
        self.async_request_session: httpx.AsyncClient = None

    def start_session(self):
        """Начать синхронную сессию"""
        new_session = None
        if self.request_session is None:
            new_session = BillmgrAPI._get_request_session(
                self.url,
                interface=self.interface,
                headers=self.headers,
                cookies=self.cookies,
                verify_ssl=self.verify_ssl,
                async_session=False
            )
            self.request_session = new_session
        return new_session

    def close_session(self):
        """Закрыть синхронную сессию"""
        if self.request_session:
            self.request_session.close()
            self.request_session = None

    def start_async_session(self):
        """Начать асинхронную сессию"""
        new_session = None
        if self.async_request_session is None:
            new_session = BillmgrAPI._get_request_session(
                self.url,
                interface=self.interface,
                headers=self.headers,
                cookies=self.cookies,
                verify_ssl=self.verify_ssl,
                async_session=True
            )
            self.async_request_session = new_session
        return new_session

    async def close_async_session(self):
        """Закрыть асинхронную сессию"""
        if self.async_request_session:
            await self.async_request_session.aclose()
            self.async_request_session = None

    def __enter__(self):
        """Контекстный менеджер - вход"""
        self.start_session()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Контекстный менеджер - выход"""
        self.close_session()

    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.start_async_session()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Асинхронный контекстный менеджер - выход"""
        await self.close_async_session()

    @classmethod
    def _get_request_session(cls, url: str, interface: Optional[str] = None, verify_ssl: Union[bool, ssl.SSLContext] = True,
                             headers: Optional[dict] = None, cookies: Optional[dict] = None, async_session: Optional[bool] = None):
        """
        Создать HTTP сессию
        
        Args:
            url: URL API
            interface: Интерфейс для подключения
            verify_ssl: Проверка SSL
            headers: Заголовки
            cookies: Cookies
            async_session: Создать асинхронную сессию
            
        Returns:
            HTTP сессия (httpx.Client или httpx.AsyncClient)
        """
        # Привязка сессии к указанному локальному адресу
        transport = None
        addr = interface
        if addr:
            transport = httpx.HTTPTransport(local_address=addr)

        session = None
        if async_session:
            session = httpx.AsyncClient(verify=verify_ssl, transport=transport)
        else:
            session = httpx.Client(verify=verify_ssl, transport=transport)

        if headers:
            session.headers = headers

        session.headers.update({
            'Referer': url
        })
        if cookies:
            session.cookies = httpx.Cookies(cookies)
        
        return session

    def _prepare_request(self, method: str, func_name: str, params: Optional[dict] = None, data: Optional[dict] = None, cookies: Optional[dict] = None,
                     headers: Optional[dict] = None, timeout: Optional[float] = None) -> PreparedRequest:
        """
        Подготовить запрос к API
        
        Args:
            method: HTTP метод
            func_name: Имя функции API
            params: Параметры запроса
            data: Данные запроса
            cookies: Cookies
            headers: Заголовки
            timeout: Таймаут
            
        Returns:
            PreparedRequest: Подготовленный запрос
        """
        url = self.url

        request_params = {}
        request_data = {}
        request_headers = {}
        request_cookies = {}

        common_params = dict(
            func=func_name,
            out='sjson'
        )

        if self.session_id is not None:
            common_params['auth'] = self.session_id
        elif self.auth_info:
            login, password = self.auth_info
            common_params['authinfo'] = f'{login}:{password}'

        if method == 'GET':
            request_params.update(common_params)
        else:
            request_data.update(common_params)

        if params:
            request_params.update(params)

        if data:
            request_data.update(data)

        if headers:
            request_headers.update(headers)

        if cookies:
            request_cookies.update(cookies)

        request_timeout = self.timeout
        if timeout is not None:
            request_timeout = timeout

        return self.__class__.PreparedRequest(
            method=method, url=url, params=request_params, json_data=request_data,
            headers=request_headers, cookies=request_cookies, timeout=request_timeout
        )

    def build_request(self, method: str, func_name: str, params: Optional[dict] = None, data: Optional[dict] = None, cookies: Optional[dict] = None,
                     headers: Optional[dict] = None, timeout: Optional[float] = None, async_session: Optional[bool] = None):
        """
        Построить HTTP запрос
        
        Args:
            method: HTTP метод
            func_name: Имя функции API
            params: Параметры запроса
            data: Данные запроса
            cookies: Cookies
            headers: Заголовки
            timeout: Таймаут
            async_session: Использовать асинхронную сессию
            
        Returns:
            httpx.Request: Построенный запрос
        """
        request = self._prepare_request(method, func_name, params=params, data=data, cookies=cookies, headers=headers, timeout=timeout)
        request_session = None
        if async_session:
            request_session: httpx.AsyncClient = self.async_request_session
        else:
            request_session: httpx.Client = self.request_session

        built_request: httpx.Request = request_session.build_request(
            method, url=request.url, params=request.params, json=request.json_data,
            headers=request.headers, cookies=request.cookies, timeout=request.timeout
        )
        return built_request

    def _handle_response(self, response: httpx.Response, result_type: str = None) -> BillmgrAPIResponse:
        """
        Обработать ответ API
        
        Args:
            response: HTTP ответ
            result_type: Тип результата
            
        Returns:
            BillmgrAPIResponse: Обработанный ответ API
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise BillmgrRequestError(f'Server returned bad HTTP code {e.response.status_code}', original_exception=e)

        try:
            response_data = response.json()
        except (TypeError, json.JSONDecodeError) as e:
            logger.exception(e)
            raise BillmgrApiError('Invalid JSON response received')

        try:
            doc = response_data['doc']
        except KeyError:
            raise BillmgrApiError('Invalid response data format')
        
        if 'error' in doc:
            raise BillmgrApiError(f"Error message: {doc['error']['msg']['$']}")

        return BillmgrAPIResponse(doc, result_type=result_type)


class KeepAliveRequest(BillmgrAPI.ApiRequest):
    """Запрос для поддержания сессии активной"""
    method = "GET"
    func_name = "keepalive"
    result_type = "item"


class AccountDiscountinfoRequest(BillmgrAPI.ApiRequest):
    """Запрос информации о скидках аккаунта"""
    method = "GET"
    func_name = "account.discountinfo"
    result_type = "item"

    @staticmethod
    def get_active_promotion_discounts(response: BillmgrAPIResponse):
        """
        Парсинг ответа для получения активных промо-скидок пользователя
        
        Args:
            response: Ответ API
            
        Returns:
            List: Список активных промо-скидок
        """
        promotion_discounts = []
        result = response.raw_result()
        logger.debug(f"AccountDiscountinfoRequest() result {result}")
        for discounts_list in result["list"]:
            if discounts_list["$name"] == "promotion":
                discount = {}
                discount_elem_list = discounts_list.get("elem", [])
                for discount_elem in discount_elem_list:
                    discount["id"] = int(discount_elem["id"]["$"])
                    discount["name"] = discount_elem["name"]["name"]["$"]
                    discount["value"] = discount_elem["value"]["text"]["$"]
                    promotion_discounts.append(discount)
                    
        return promotion_discounts 