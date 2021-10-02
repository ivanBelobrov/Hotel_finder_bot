from peewee import *

db = SqliteDatabase('db/history.db')


class History(Model):
    id = PrimaryKeyField(unique=True)
    date_and_time = DateTimeField()
    user_id = IntegerField()
    command = CharField()
    hotels = CharField()

    class Meta:
        database = db
        order_by = 'id'


def create_db():
    with db:
        db.create_tables([History])


def new_record_db(user_id, time_stamp, command, hotels):
    with db:
        History.create(date_and_time=time_stamp, user_id=user_id, command=command, hotels=hotels)


def give_me_record_db(user):
    with db:
        history = History.select().where(History.user_id == user)
    return history
