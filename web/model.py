import asyncio, dao
from dao import Model, IntegerField, StringField

class User(Model):
    __table__ = 'user'

    user_id = IntegerField(primary_key=True, column_type='varchar(50)', default=dao.generate_uid())
    username = StringField(column_type='varchar(50)')
    password = StringField(column_type='varchar(50)')
    email = StringField(column_type='varchar(50)')
    phone = StringField(column_type='varchar(50)')

class Macro_Nutrition(Model):
    __table__ = 'macro_nutrition'

    food_id = IntegerField(primary_key=True, column_type='varchar(50)')
    food_name = StringField(column_type='varchar(50)')
    unit = StringField(column_type='int')
    unit_name = StringField(column_type='varchar(50)')
    energy = StringField(column_type='float')
    carbohydrate = StringField(column_type='float')
    protein = StringField(column_type='float')
    fat = StringField(column_type='float')


def test():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(dao.create_connection(loop, db='diet_pal'))

    #u =  loop.run_until_complete(Macro_Nutrition.find('food_name=? or protein>?', ['Whey', 10]))
    #print(u)
    #u = User(username='huxhu', password='haha', email='h@g.c')
    #loop.run_until_complete(u.save())

#test()