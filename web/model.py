import asyncio, dao
from dao import Model, IntegerField, StringField

class Macro_Nutrition(Model):
    __table__ = 'macro_nutrition'

    food_id = IntegerField(primary_key=True, column_type='int')
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

    u =  loop.run_until_complete(Macro_Nutrition.findByKey(1))
    print(u)





test()