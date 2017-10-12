import asyncio, dao
from dao import Model, IntegerField, StringField

class User(Model):
    __table__ = 'user'

    id = IntegerField(primary_key=True, column_type='Int')
    email = StringField(column_type='varchar(50)')
    passwd = StringField(column_type='varchar(50)')
    name = StringField(column_type='varchar(50)')
    image = StringField(column_type='varchar(500)')


def test():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dao.create_connection(loop, db='awesome'))

    u = User(name='Test', email='test1@example.com', passwd='1234567890', image='about:blank')

    loop.run_until_complete(u.save())
    # rs = loop.run_until_complete(select('select * from user;', ()))




test()