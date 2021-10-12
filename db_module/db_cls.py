import datetime
from peewee import *
from peewee import ModelSelect

db = SqliteDatabase('db/history.db')


class History(Model):
    """
    Класс, описывающий модель быза данных.

    Attributes:
        id: поле для порядкового номера записи
        date_and_time: поле для даты и времени
        user_id: поле для id пользователя
        command: поле для введенной команды пользователем
        hotels: поле для перечисленя отелей
    """
    id = PrimaryKeyField(unique=True)
    date_and_time = DateTimeField()
    user_id = IntegerField()
    command = CharField()
    hotels = CharField()

    class Meta:
        """
        Метакласс для класса History

        Attributes:
            database: используемая БД
            order_by: элмент по которому будет идти сортировка в БД
        """
        database = db
        order_by = 'id'


def create_db() -> None:
    """Функция создает БД"""
    with db:
        db.create_tables([History])


def new_record_db(user_id: int, time_stamp: datetime.datetime, command: str, hotels: str) -> None:
    """
    Функция, которая создает новую запись в БД.

    :param user_id: id пользователя
    :type: int
    :param time_stamp: дата и время
    :type: int
    :param command: введенная команда
    :type: str
    :param hotels: полученные по запросу отели
    :type: str
    """
    with db:
        History.create(date_and_time=time_stamp, user_id=user_id, command=command, hotels=hotels)


def give_me_record_db(user: int) -> ModelSelect:
    """
    Функция, которая возвращает все записи с переданным id пользователя.

    :param user: id  пользователя
    :type: int
    :return: все найденные записи в БД с переданным id пользователя
    :rtype: ModelSelect
    """
    with db:
        history = History.select().where(History.user_id == user)
    return history
