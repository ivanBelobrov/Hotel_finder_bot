class User:
    users = dict()

    def __init__(self, user_id):
        self.users = User._new_user(user_id)

    @classmethod
    def get_user_params(cls, user_id):
        return cls.users[user_id]

    @classmethod
    def _new_user(cls, user_id):
        if cls.users.get(user_id) is None:
            cls.users[user_id] = dict()


