# -*- coding: utf-8 -*-

from typing import Iterable, Optional
from collections import defaultdict

from flask import current_app
from flask_login import UserMixin
from dataclasses import dataclass
from time import time
import ipaddress

from ..db import get_db
from ..utils.billmgr_api import BillmgrAPI, BillmgrError, KeepAliveRequest


@dataclass
class User(UserMixin):
    """
    Пользователь BILLmanager с поддержкой ролей и уровней доступа
    """
    id: int
    name: str
    realname: str
    session_id: str
    auth_level: int

    def get_id(self) -> str:
        """Получить ID пользователя для Flask-Login"""
        return self.session_id

    def has_roles(self, roles: Optional[Iterable[str]]) -> bool:
        """
        Проверить наличие ролей у пользователя
        
        Args:
            roles: Список требуемых ролей
            
        Returns:
            bool: True если пользователь имеет все требуемые роли
        """
        if not roles:
            return True

        roles = set(roles)
        db = get_db('billmgr')

        core_user_row = db.select_query("""
            SELECT *
            FROM core_users
            WHERE core_users.name = CAST(%(user_id)s AS CHAR)
        """, {'user_id': self.id}).one_or_none()

        if not core_user_row:
            return False

        if core_user_row.get('super') == 'on':
            return True

        full_access_mask = 7
        values = {'user_id': self.id}
        in_clause = self._build_in_clause('role_', roles, values)

        query = f"""
            SELECT cf.name  AS func_name,
                   cf.access
            FROM core_users u
            JOIN core_funcs cf
                ON cf.users = u.id
            WHERE u.name = CAST(%(user_id)s AS CHAR)
              AND cf.name IN ({in_clause})

            UNION

            SELECT cf.name AS func_name,
                   cf.access
            FROM core_users u
            JOIN core_members m
                ON m.user_id = u.id
            JOIN core_users g
                ON g.id = m.group_id
            JOIN core_funcs cf
                ON cf.users = g.id
            WHERE u.name = CAST(%(user_id)s AS CHAR)
              AND cf.name IN ({in_clause})
        """

        permission_rows = db.select_query(query, values).all()

        roles_access = defaultdict(list)
        for row in permission_rows:
            roles_access[row['func_name']].append(row['access'])

        for role in roles:
            if role not in roles_access:
                return False

            has_full_access_for_role = any(
                (access_val & full_access_mask) == full_access_mask
                for access_val in roles_access[role]
            )
            if not has_full_access_for_role:
                return False

        return True

    @staticmethod
    def _build_in_clause(prefix: str, values_iter: Iterable[str], param_dict: dict) -> str:
        """
        Построить IN-clause для SQL запроса
        
        Args:
            prefix: Префикс для параметров
            values_iter: Значения для IN
            param_dict: Словарь параметров
            
        Returns:
            str: Строка с placeholders для IN-clause
        """
        placeholders = []
        for i, val in enumerate(values_iter):
            param_name = f"{prefix}{i}"
            placeholders.append(f"%({param_name})s")
            param_dict[param_name] = val
        return ", ".join(placeholders)


def load_billmgr_user(request: Request) -> Optional[User]:
    """
    Загрузить пользователя из сессии BILLmanager
    
    Функция для загрузки пользователя из сессии.
    Вызывается перед обработчиком запроса при использовании @login_required.
    
    Args:
        request: Flask request объект
        
    Returns:
        User or None: Пользователь или None если авторизация неуспешна
    """
    user = None
    session_id = request.cookies.get('billmgrses5')
    
    if not session_id:
        return None
        
    db = get_db('billmgr')

    # Получаем данные пользователя из сессии
    user_row = db.select_query("""
    SELECT core_session.id AS core_session_id
        , core_session.name AS core_session_name
        , core_session.ip AS core_session_ip
        , core_session.atime AS core_session_atime
        , user.id AS user_id
        , user.name AS name
        , user.realname AS realname
        , user.level AS level
        , allowed_ip_ranges_param.ext_value AS allowed_ip_ranges
        , totp_status_param.core_session IS NOT NULL AS has_totp_status
        , totp_status_param.ext_value AS totp_status
    FROM core_session
    JOIN user
        ON user.id = CAST(core_session.name AS SIGNED INTEGER)
    LEFT OUTER JOIN core_session_ext AS allowed_ip_ranges_param
        ON allowed_ip_ranges_param.core_session = core_session.id
        AND allowed_ip_ranges_param.ext_name = 'allowed_ip_ranges'
    LEFT OUTER JOIN totp
        ON totp.user = user.id
    LEFT OUTER JOIN core_session_ext AS totp_status_param
        ON totp_status_param.core_session = core_session.id
        AND totp_status_param.ext_name = 'totp_status'
    WHERE core_session.id = %(session_id)s
        AND user.enabled = 'on'
    """, {
        'session_id': session_id
    }).one_or_none()

    if not user_row:
        return None

    user = User(
        id=user_row['user_id'],
        name=user_row['name'],
        realname=user_row['realname'],
        session_id=user_row['core_session_id'],
        auth_level=user_row['level']
    )

    # Проверка IP ограничений
    ip_address = ipaddress.ip_address(str(request.headers.get('X-Forwarded-For', request.remote_addr)))
    allowed_ip_ranges = user_row['allowed_ip_ranges']
    
    if allowed_ip_ranges:
        is_ip_allowed = False
        allowed_ip_ranges_list = allowed_ip_ranges.split()
        
        # В режиме отладки разрешаем localhost
        if current_app.debug:
            allowed_ip_ranges_list.append('127.0.0.1')

        for allowed_ip_string in allowed_ip_ranges_list:
            if '-' in allowed_ip_string:
                # Диапазон IP
                ip_range = allowed_ip_string.split('-')
                ip_range_start = ipaddress.ip_address(ip_range[0]) 
                ip_range_end = ipaddress.ip_address(ip_range[1]) 
                is_ip_allowed = is_ip_allowed or (ip_range_start <= ip_address <= ip_range_end)
            else:
                # Сеть или отдельный IP
                ip_network = ipaddress.ip_interface(str(allowed_ip_string)).network
                is_ip_allowed = is_ip_allowed or (ip_address in ip_network)
            
            if is_ip_allowed:
                break
                
        if not is_ip_allowed:
            return None

    # Проверка двухфакторной аутентификации
    if user_row['has_totp_status'] and user_row['totp_status'] != 'on':
        return None

    # Поддержание сессии активной
    core_session_atime = user_row.get('core_session_atime', None)
    if core_session_atime:
        idle_seconds = int(time()) - int(core_session_atime)
        idle_minutes_limit = 0
        
        if idle_seconds > (idle_minutes_limit * 60):
            headers = {
                'X-Forwarded-For': str(ip_address),
                'X-Forwarded-Secret': current_app.config.get('FORWARDED_SECRET')
            }
            
            # Обновляем время последней активности
            try:
                billmgr_api = BillmgrAPI(
                    url=current_app.config.get('BILLMGR_API_URL'),
                    interface=current_app.config.get('BILLMGR_API_USE_INTERFACE'),
                    cookies={'billmgrses5': session_id},
                    headers=headers
                )
                with billmgr_api:
                    KeepAliveRequest().send(billmgr_api)
            except (BillmgrError, Exception):
                # Игнорируем ошибки keep-alive для стабильности
                pass

    return user 