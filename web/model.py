import asyncio, dao
from dao import Model, IntegerField, StringField, FloatField

class User(Model):
    __table__ = 'user'

    user_id = IntegerField(primary_key=True, column_type='varchar(50)', default=dao.generate_uid())
    username = StringField(column_type='varchar(50)')
    password = StringField(column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    phone = StringField(column_type='varchar(50)')

class Food(Model):
    __table__ = 'food'

    food_id = IntegerField(primary_key=True, column_type='int')
    food_name = StringField(column_type='varchar(50)')
    unit = FloatField(column_type='float')
    unit_name = StringField(column_type='varchar(50)')
    energy = FloatField(column_type='float')
    carbohydrate = FloatField(column_type='float')
    protein = FloatField(column_type='float')
    fat = FloatField(column_type='float')

class Record(Model):
    __table__ = 'record'

    record_id = StringField(primary_key=True, column_type='varchar(50)', default=dao.generate_uid())
    food_id = IntegerField(column_type='int')
    user_id = StringField(column_type='varchar(50)')
    amount = FloatField(column_type='float')
    record_time = FloatField(column_type='float')


def test():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dao.create_connection(loop, db='diet_pal'))

    #u =  loop.run_until_complete(Macro_Nutrition.find('food_name=? or protein>?', ['Whey', 10]))
    #print(u)
    #u = User(username='huxhu', password='haha', email='h@g.c')
    #loop.run_until_complete(u.save())

#test()