# -*- coding: utf-8 -*-

"""
Пример плагина для демонстрации WSGI развертывания
"""

from billmgr_addon import get_db
from billmgr_addon.core.request_types import MgrRequest
from billmgr_addon.core.response import MgrErrorResponse, MgrSuccessResponse

# Импортируем базовые классы напрямую для избежания проблем с линтером
from billmgr_addon.core.router import ActionEndpoint, FormEndpoint, ListEndpoint
from billmgr_addon.core.ui import MgrForm


class ServersList(ListEndpoint):
    """Список виртуальных серверов"""

    async def get(self, mgr_list, mgr_request):
        # Пример данных
        servers = [
            {
                "id": 1,
                "name": "web-server-01",
                "ip": "192.168.1.10",
                "cpu": 4,
                "ram": 8192,
                "disk": 100,
                "status": "running",
            },
            {
                "id": 2,
                "name": "db-server-01",
                "ip": "192.168.1.20",
                "cpu": 8,
                "ram": 16384,
                "disk": 500,
                "status": "running",
            },
            {
                "id": 3,
                "name": "backup-server",
                "ip": "192.168.1.30",
                "cpu": 2,
                "ram": 4096,
                "disk": 1000,
                "status": "stopped",
            },
        ]

        mgr_list.set_data_rows(servers)
        return mgr_list


class ServerForm(FormEndpoint):
    """Форма создания/редактирования сервера"""

    async def get(self, form: MgrForm, mgr_request: MgrRequest):
        # Настройка полей формы
        form.add_text_field("name", required=True)
        form.add_text_field("ip", required=True)
        form.add_select_field(
            "cpu",
            options=[
                {"value": 1, "label": "1 CPU"},
                {"value": 2, "label": "2 CPU"},
                {"value": 4, "label": "4 CPU"},
                {"value": 8, "label": "8 CPU"},
            ],
        )
        form.add_select_field(
            "ram",
            options=[
                {"value": 2048, "label": "2 GB"},
                {"value": 4096, "label": "4 GB"},
                {"value": 8192, "label": "8 GB"},
                {"value": 16384, "label": "16 GB"},
            ],
        )
        form.add_text_field("disk", field_type="number", min_value=10, max_value=1000)

        # Если редактирование - загружаем данные
        if mgr_request.params.get("elid"):
            server_id = mgr_request.params["elid"]
            # Здесь бы загружали данные из БД
            form.set_field_value("name", f"server-{server_id}")

        return form

    async def setvalues(self, form: MgrForm, mgr_request: MgrRequest):
        # Валидация данных
        name = mgr_request.params.get("name")
        if not name or len(name) < 3:
            return MgrErrorResponse(msg="Имя сервера должно быть не менее 3 символов")

        # Сохранение в БД
        # db = get_db('billmgr')
        # db.insert_query(...)

        return MgrSuccessResponse(msg="Сервер успешно создан")


class ServerRestart(ActionEndpoint):
    """Перезапуск сервера"""

    async def get(self, mgr_request: MgrRequest):
        server_id = mgr_request.params.get("elid")
        if not server_id:
            return MgrErrorResponse(msg="Не указан ID сервера")

        # Здесь бы выполняли действие через API
        # await restart_server(server_id)

        return MgrSuccessResponse(msg=f"Сервер {server_id} перезапускается")


class HealthCheck(ActionEndpoint):
    """Проверка здоровья для мониторинга"""

    async def get(self, mgr_request: MgrRequest):
        checks = {"status": "healthy", "database": "unknown", "version": "1.0.0"}

        # Проверка БД
        try:
            db = get_db("billmgr")
            db.select_query("SELECT 1").one()
            checks["database"] = "connected"
        except Exception as e:
            checks["database"] = f"error: {str(e)}"
            checks["status"] = "unhealthy"

        if checks["status"] == "healthy":
            return MgrSuccessResponse(msg="OK", data=checks)
        else:
            return MgrErrorResponse(msg="Health check failed", data=checks)


# Список всех эндпоинтов плагина
endpoints = [
    ServersList("servers.list"),
    ServerForm("servers.edit"),
    ServerRestart("servers.restart"),
    HealthCheck("health"),
]
