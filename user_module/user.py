from typing import Dict, Any
from collections.abc import Iterable


class User:
    """
    Класс, описывающий пользователя.

    Args:
        user_id (int): передается id пользователя.

    Attributes:
        _users (dict): параметрамы каждого пользователя.
    """
    _users = dict()

    def __init__(self, user_id: int) -> None:
        User._new_user(user_id)

    @classmethod
    def get_user_params(cls, user_id: int) -> Dict[str, Any]:
        """
        Геттер для получения параметров пользователя.

        :param user_id: id пользователя
        :type: int
        :return: cls._users[user_id]
        :rtype: dict
        """
        return cls._users[user_id]

    @classmethod
    def get_users_list(cls) -> Iterable[int]:
        """
        Геттер для получения id всех пользователей.
        :return: cls._users.keys()
        :rtype: List(int)
        """
        return cls._users.keys()

    @classmethod
    def _new_user(cls, user_id: int) -> None:
        """
        Функция, которая создает новую запись о пользователе, если он не обнаружен в словаре.
        :param user_id: id пользователя
        :type: int
        """
        if cls._users.get(user_id) is None:
            cls._users[user_id] = dict()


