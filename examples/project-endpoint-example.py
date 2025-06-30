# -*- coding: utf-8 -*-

"""
Пример создания собственных базовых классов для специфичных задач

Демонстрирует как создать собственные базовые классы для эндпоинтов
в случае специфичных требований (проекты, подписки, аккаунты).

В данном примере показано как создать систему для управления 
"хостинг-аккаунтами" с собственной логикой авторизации.

ПРИМЕЧАНИЕ: Это упрощенный пример для демонстрации концепции.
В реальном проекте используйте правильные типы и импорты.
"""

from billmgr_addon.core.router import MgrEndpoint, ListEndpoint, FormEndpoint, MgrRequest
from billmgr_addon.core.response import MgrOkResponse, MgrErrorResponse
from billmgr_addon.core.ui._list import MgrList
from billmgr_addon.core.ui.form import MgrForm
from billmgr_addon.db import get_db


class HostingAccountNotFoundError(Exception):
    """Исключение когда хостинг-аккаунт не найден"""
    pass


class HostingAccountMixin:
    """Миксин для добавления логики работы с хостинг-аккаунтами"""
    
    def _get_hosting_account(self, user_id):
        """Получаем данные хостинг-аккаунта пользователя"""
        # Simplified example - implement actual DB query
        return {
            'item_id': 123,
            'account_id': 'acc_456',
            'domain': 'example.com',
            'quota': 1000
        }


class HostingRequiredEndpoint(MgrEndpoint, HostingAccountMixin):
    """Базовый класс для эндпоинтов, требующих хостинг-аккаунт"""
    
    async def _handle_request(self, mgr_request):
        try:
            hosting_account = self._get_hosting_account(mgr_request.auth_user)
            mgr_request.hosting_account = hosting_account
        except HostingAccountNotFoundError:
            return MgrRedirectResponse("form", "hosting.create_account_form")
        
        return await super()._handle_request(mgr_request)


class HostingRequiredListEndpoint(ListEndpoint, HostingAccountMixin):
    """Базовый класс для списков, требующих хостинг-аккаунт"""
    
    async def _handle_request(self, mgr_request):
        try:
            hosting_account = self._get_hosting_account(mgr_request.auth_user)
            mgr_request.hosting_account = hosting_account
        except HostingAccountNotFoundError:
            from billmgr_addon.core.response import MgrRedirectResponse
            return MgrRedirectResponse("form", "hosting.create_account_form")
        
        return await super()._handle_request(mgr_request)


class HostingRequiredFormEndpoint(FormEndpoint, HostingAccountMixin):
    """Базовый класс для форм, требующих хостинг-аккаунт"""
    
    async def _handle_request(self, mgr_request):
        try:
            hosting_account = self._get_hosting_account(mgr_request.auth_user)
            mgr_request.hosting_account = hosting_account
        except HostingAccountNotFoundError:
            from billmgr_addon.core.response import MgrRedirectResponse
            return MgrRedirectResponse("form", "hosting.create_account_form")
        
        return await super()._handle_request(mgr_request)


# Примеры использования

class HostingFileList(HostingRequiredListEndpoint):
    """Список файлов в хостинг-аккаунте"""
    
    async def get(self, mgr_list: MgrList, mgr_request: MgrRequest):
        hosting_account = mgr_request.hosting_account
        
        # Здесь мы бы обращались к API хостинг-провайдера
        # Для примера просто возвращаем тестовые данные
        files = [
            {"id": 1, "name": "index.html", "size": "2.5 KB", "modified": "2024-01-15"},
            {"id": 2, "name": "style.css", "size": "1.2 KB", "modified": "2024-01-14"},
            {"id": 3, "name": "script.js", "size": "850 B", "modified": "2024-01-13"},
        ]
        
        mgr_list.set_data_rows(files)
        mgr_list.set_metadata("title", f"Files - {hosting_account['domain']}")
        
        return mgr_list


class HostingCreateFileForm(HostingRequiredFormEndpoint):
    """Форма создания файла в хостинг-аккаунте"""
    
    async def get(self, form: MgrForm, mgr_request: MgrRequest):
        hosting_account = mgr_request.hosting_account
        
        # Предзаполняем форму данными аккаунта
        form.set_data_value("domain", hosting_account['domain'])
        form.set_data_value("quota_used", f"{hosting_account['quota']} MB")
        
        return form
    
    async def setvalues(self, form: MgrForm, mgr_request: MgrRequest):
        return await super().setvalues(form, mgr_request)
    
    async def new(self, mgr_request: MgrRequest):
        hosting_account = mgr_request.hosting_account
        filename = mgr_request.params.get("filename")
        content = mgr_request.params.get("content", "")
        
        # Здесь мы бы создавали файл через API хостинг-провайдера
        print(f"Creating file {filename} in account {hosting_account['account_id']}")
        
        return MgrOkResponse()
    
    async def edit(self, mgr_request: MgrRequest):
        hosting_account = mgr_request.hosting_account
        file_id = mgr_request.params.get("elid")
        content = mgr_request.params.get("content")
        
        # Здесь мы бы обновляли файл через API
        print(f"Updating file {file_id} in account {hosting_account['account_id']}")
        
        return MgrOkResponse()


class HostingQuotaCheck(HostingRequiredEndpoint):
    """Простое действие - проверка квоты хостинг-аккаунта"""
    
    async def get(self, mgr_request: MgrRequest):
        hosting_account = mgr_request.hosting_account
        
        # Здесь мы бы получали актуальную информацию о квоте через API
        quota_info = {
            "domain": hosting_account['domain'],
            "quota_total": hosting_account['quota'],
            "quota_used": hosting_account['quota'] * 0.7,  # Для примера 70% использовано
            "quota_available": hosting_account['quota'] * 0.3
        }
        
        # Возвращаем JSON ответ для AJAX запросов
        from flask import jsonify
        return jsonify(quota_info)


# Список эндпоинтов для регистрации в роутере
ENDPOINTS = [
    ("hosting.file_list", HostingFileList),
    ("hosting.create_file_form", HostingCreateFileForm), 
    ("hosting.quota_check", HostingQuotaCheck),
]


if __name__ == "__main__":
    print("Custom Base Classes Example")
    print("Собственные базовые классы для эндпоинтов с хостинг-аккаунтами:")
    for route, endpoint_class in ENDPOINTS:
        print(f"  {route} -> {endpoint_class.__name__}")
    
    print("\nПреимущества:")
    print("  - Полный контроль над логикой авторизации")
    print("  - Адаптация под конкретную схему БД")  
    print("  - Переиспользование кода через миксины")
    print("  - Простота понимания и модификации") 
    print("Это упрощенный пример для демонстрации концепции.") 