class User:
    _users = dict()

    def __init__(self, user_id):
        User._new_user(user_id)

    @classmethod
    def get_user_params(cls, user_id):
        return cls._users[user_id]
    @classmethod
    def get_users_list(cls):
        return cls._users.keys()

    @classmethod
    def _new_user(cls, user_id):
        if cls._users.get(user_id) is None:
            cls._users[user_id] = dict()


