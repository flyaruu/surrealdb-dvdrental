import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
from datetime import datetime

from surrealdb import Surreal

async def import_tables():
    start_time = time.monotonic()
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="dvdrental",
        user="postgres",
        password="mysecretpassword")

    # cur = conn.cursor()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    async with Surreal("ws://localhost:8000/rpc") as db:
        await db.signin({"user": "root", "pass": "root"})
        await db.use("myns", "mydb")
        await import_countries(cur,db)
        await import_cities(cur,db)
        await import_address(cur,db)
        await import_customers(cur,db)
        await import_staff(cur,db)
        await import_store(cur,db)
        await import_language(cur,db)
        await import_category(cur,db)
        await import_film(cur,db)
        await import_actor(cur,db)
        await link_category(cur,db)
        await link_actor(cur,db)
        await import_inventory(cur,db)
        await import_rental(cur,db)
        
    print("done!")
    print('seconds: ', time.monotonic() - start_time)


async def import_language(cur: RealDictCursor, db: Surreal):
    await db.delete("language")
    cur.execute("select * from language")
    for row in cur.fetchall():
        record = {'language_id': row['language_id'],
                   'name': row['name'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(db,'language',row['language_id'], record)

async def import_category(cur: RealDictCursor, db: Surreal):
    await db.delete("category")
    cur.execute("select * from category")
    for row in cur.fetchall():
        record = {'category_id': row['category_id'],
                   'name': row['name'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(db,'category',row['category_id'], record)

async def import_film(cur: RealDictCursor, db: Surreal):
    await db.delete("film")
    cur.execute("select * from film")
    for row in cur.fetchall():
        film_id = row['film_id'];
        record = {'film_id': film_id,
            'title': row['title'],
            'description': row['description'],
            'release_year': row['release_year'],
            'language': "language:{}".format(row['language_id']),
            # 'category': "category:{}".format(row['category_id']),
            'rental_duration': row['rental_duration'],
            'rental_rate': float (row['rental_rate']),
            'length': row['length'],
            'replacement_cost': float(row['replacement_cost']),
            'last_update': row['last_update'].isoformat(),
            'special_features': row['special_features']
        }
        await import_object(db,'film',film_id, record)

async def import_actor(cur: RealDictCursor, db: Surreal):
    await db.delete("actor")
    cur.execute("select * from actor")
    for row in cur.fetchall():
        actor_id = row['actor_id'];
        record = {'actor_id': actor_id,
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'last_update': row['last_update'].isoformat()
        }
        # print(record);
        await import_object(db,'actor',actor_id, record)


async def link_category(cur: RealDictCursor, db: Surreal):
    cur.execute("select * from film_category")
    for row in cur.fetchall():
        await db.query(
            'UPDATE type::thing("film",$film_id) SET categories += type::thing("category",$category_id)'
            ,{
                'film_id':row['film_id'],
                'category_id':"category:{}".format(row['category_id'])
            }
        )

async def link_actor(cur: RealDictCursor, db: Surreal):
    cur.execute("select * from film_actor")
    for row in cur.fetchall():
        # print ("associating {} with {}".format(row['film_id'],row['actor_id']))
        query = "RELATE actor:{}->played_in->film:{}".format(row['actor_id'],row['film_id'])
        await db.query(query)
        query = "RELATE film:{}->features->actor:{}".format(row['film_id'],row['actor_id'])
        await db.query(query)

        # await db.query(
        # 'RELATE actor:$actor_id->played_in->film:$film_id'
        #     ,{
        #         'film_id':str(row['film_id']),
        #         'actor_id':str(row['actor_id'])
        #     }
        # )
        #     # """RELATE type::thing("actor",$actor_id)->played_in->type::thing("film",$film_id)"""

async def import_staff(cur: RealDictCursor, db: Surreal):
    await db.delete("staff")
    cur.execute("select * from staff")
    for row in cur.fetchall():
        record = {'staff_id': row['staff_id'],
                  'first_name': row['first_name'],
                  'last_name': row['last_name'],
                  'address_id': "address:{}".format(row['address_id']),
                  'email': row['email'],
                  'active': row['active'],
                  'username': row['username'],
                  'password': row['password'],
                  'last_update': row['last_update'].isoformat()
                  }
        await import_object(db,'staff',row['staff_id'], record)

async def import_store(cur: RealDictCursor, db: Surreal):
    await db.delete("store")
    cur.execute("select * from store")
    for row in cur.fetchall():
        record = {'store_id': row['store_id'],
                  'manager_staff_id': "staff:{}".format(row['manager_staff_id']),
                  'address_id': "address:{}".format(row['address_id']),
                  'last_update': row['last_update'].isoformat()
                  }
        await import_object(db,'store',row['store_id'], record)

async def import_customers(cur: RealDictCursor, db: Surreal):
    await db.delete("customer")
    cur.execute("select * from customer")
    for row in cur.fetchall():
        record = {'customer_id': row['customer_id'],
                  'first_name': row['first_name'],
                  'last_name': row['last_name'],
                  'email': row['email'],
                  'address_id': "address:{}".format(row['address_id']),
                  'create_date': row['create_date'].isoformat(),
                  'last_update': row['last_update'].isoformat()
                  }
        await import_object(db,'customer',row['customer_id'], record)

async def import_countries(cur: RealDictCursor, db: Surreal):
    await db.delete("country")
    cur.execute("select * from country")
    for row in cur.fetchall():
        record = {'country_id': row['country_id'],
                   'country': row['country'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(db,'country',row['country_id'], record)

async def import_cities(cur: RealDictCursor, db: Surreal):
    await db.delete("city")
    cur.execute("select * from city")
    for row in cur.fetchall():
        record = {'city_id': row['city_id'], 'city': row['city'], 'last_update': row['last_update'].isoformat(), 'country_id': "country:{}".format(row['country_id'])}
        await import_object(db,'city',row['city_id'], record)

async def import_address(cur: RealDictCursor, db: Surreal):
    await db.delete("address")
    cur.execute("select * from address")
    for row in cur.fetchall():
        record = {'address_id': row['address_id'],
                'address': row['address'], 
                'address2': row['address2'], 
                'district': row['district'], 
                'city_id': "city:{}".format(row['city_id']),
                'postal_code': row['postal_code'], 
                'phone': row['phone'], 
                'last_update': row['last_update'].isoformat()}
        await import_object(db,'address',row['address_id'], record)

async def import_inventory(cur: RealDictCursor, db: Surreal):
    await db.delete("inventory")
    cur.execute("select * from inventory")
    for row in cur.fetchall():
        record = {'inventory_id': row['inventory_id'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(db,'inventory',row['inventory_id'], record)
        query = "RELATE inventory:{}->film_instance->film:{}".format(row['inventory_id'],row['film_id'])
        await db.query(query)
        query = "RELATE inventory:{}->in_store->store:{}".format(row['inventory_id'],row['store_id'])
        await db.query(query)

async def import_rental(cur: RealDictCursor, db: Surreal):
    await db.delete("rental")
    cur.execute("select * from rental")
    for row in cur.fetchall():
        return_date = row['return_date']
        if (return_date != None):
            return_date = return_date.isoformat()
        rental_date = row['rental_date']
        if (rental_date != None):
            rental_date = rental_date.isoformat()
        record = {'rental_id': row['rental_id'],
                   'customer_id': row['customer_id'],
                   'inventory_id': row['inventory_id'],
                   'rental_date': rental_date,
                   'return_date': return_date,
                   'last_update': row['last_update'].isoformat(),
                   }
        query = """CREATE type::thing("rental",$rental_id) SET last_update = type::datetime($last_update),
             rental_date=type::datetime($rental_date),
             return_date=type::datetime($return_date)
        """
        result = await db.query(query, record)
#        query = "RELATE type::thing('rental',$rental_id)->customerrental->type::thing('customer',$customer_id)".format({'customer_id': str(row['customer_id']),'rental_id': str(row['rental_id'])})
        # query = """RELATE type::thing('rental',$r)->customerrental->type::thing('customer',$c)"""
        query = "RELATE rental:{}->customer_rental->customer:{}".format(record["rental_id"],record["customer_id"])
        result = await db.query(query)
        query = "RELATE rental:{}->inventory_rental->inventory:{}".format(record["rental_id"],record["inventory_id"])
        result = await db.query(query)

async def import_object(db: Surreal, table: str, key: str, data: dict):
    id = '{}:{}'.format(table,key)
    # await db.delete(id)
    await db.create(id,data)

if __name__ == "__main__":
    import asyncio

    asyncio.run(import_tables())