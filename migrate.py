'''Migrate the classic dvdrental database to a (hopefully) sensible datamodel in SurrealDB'''
import os
import time
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor
from surrealdb import Surreal
from dotenv import load_dotenv

async def import_tables():
    """migrate database from pg to surreal"""
    postgres_host = os.getenv("POSTGRES_HOST")
    if postgres_host is None:
        print("Loading .env file")
        load_dotenv()
    start_time = time.monotonic()
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        database=os.getenv("POSTGRES_DATABASE"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    # cur = conn.cursor()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    async with Surreal(os.getenv("SURREAL_URL")) as dest_db:
        await dest_db.signin({
            "user": os.getenv("SURREAL_USER"),
            "pass": os.getenv("SURREAL_PASSWORD")
        })
        await dest_db.use(os.getenv("SURREAL_NAMESPACE"), os.getenv("SURREAL_DATABASE"))
        await import_countries(cur,dest_db)
        await import_cities(cur,dest_db)
        await import_address(cur,dest_db)
        await import_customers(cur,dest_db)
        await import_staff(cur,dest_db)
        await import_store(cur,dest_db)
        await import_language(cur,dest_db)
        await import_category(cur,dest_db)
        await import_film(cur,dest_db)
        await import_actor(cur,dest_db)
        await link_category(cur,dest_db)
        await link_actor(cur,dest_db)
        await import_inventory(cur,dest_db)
        await import_rental(cur,dest_db)
    print("done!")
    print('seconds: ', time.monotonic() - start_time)


async def import_language(cur: RealDictCursor, dest_db: Surreal):
    """migrate language table"""
    await dest_db.delete("language")
    cur.execute("select * from language")
    for row in cur.fetchall():
        record = {'language_id': row['language_id'],
                   'name': row['name'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(dest_db,'language',row['language_id'], record)

async def import_category(cur: RealDictCursor, dest_db: Surreal):
    """migrate category table"""
    await dest_db.delete("category")
    cur.execute("select * from category")
    for row in cur.fetchall():
        record = {'category_id': row['category_id'],
                   'name': row['name'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(dest_db,'category',row['category_id'], record)

async def import_film(cur: RealDictCursor, dest_db: Surreal):
    """migrate film table"""
    await dest_db.delete("film")
    cur.execute("select * from film")
    for row in cur.fetchall():
        film_id = row['film_id']
        record = {'film_id': film_id,
            'title': row['title'],
            'description': row['description'],
            'release_year': row['release_year'],
            'language': f'language:{row["language_id"]}',
            'rental_duration': row['rental_duration'],
            'rental_rate': float (row['rental_rate']),
            'length': row['length'],
            'replacement_cost': float(row['replacement_cost']),
            'last_update': row['last_update'].isoformat(),
            'special_features': row['special_features']
        }
        await import_object(dest_db,'film',film_id, record)

async def import_actor(cur: RealDictCursor, dest_db: Surreal):
    """migrate actor table"""
    await dest_db.delete("actor")
    cur.execute("select * from actor")
    for row in cur.fetchall():
        actor_id = row['actor_id']
        record = {'actor_id': actor_id,
            'first_name': row['first_name'],
            'last_name': row['last_name'],
            'last_update': row['last_update'].isoformat()
        }
        await import_object(dest_db,'actor',actor_id, record)


async def link_category(cur: RealDictCursor, dest_db: Surreal):
    """migrate film_category table, by creating record pointers from film -> category"""

    cur.execute("select * from film_category")
    for row in cur.fetchall():
        await dest_db.query(
            '''UPDATE type::thing("film",$film_id) 
                SET categories += type::thing("category",$category_id)
            '''
            ,{
                'film_id':row['film_id'],
                # 'category_id':"category:{}".format(row['category_id'])
                'category_id':f'category:{row["category_id"]}'
            }
        )

async def link_actor(cur: RealDictCursor, dest_db: Surreal):
    '''Associate movies and actors (bidirectionally)'''
    cur.execute("select * from film_actor")
    for row in cur.fetchall():
        # is this necessary?
        # + I didn't manage to properly use parameters, now I'm just stitching the query
        # together, which might introduce a vulnerability for SQL-injection like attacks
        query = f"RELATE actor:{row['actor_id']}->played_in->film:{row['film_id']}"
        await dest_db.query(query)
        query = f"RELATE film:{row['film_id']}->features->actor:{row['actor_id']}"
        await dest_db.query(query)

async def import_staff(cur: RealDictCursor, dest_db: Surreal):
    '''import staff table, use record pointers to address'''
    await dest_db.delete("staff")
    cur.execute("select * from staff")
    for row in cur.fetchall():
        record = {'staff_id': row['staff_id'],
                  'first_name': row['first_name'],
                  'last_name': row['last_name'],
                  'address_id': f"address:{row['address_id']}",
                  'email': row['email'],
                  'active': row['active'],
                  'username': row['username'],
                  'password': row['password'],
                  'last_update': row['last_update'].isoformat()
                  }
        await import_object(dest_db,'staff',row['staff_id'], record)

async def import_store(cur: RealDictCursor, dest_db: Surreal):
    '''import staff table, use record pointers to address + staff'''
    await dest_db.delete("store")
    cur.execute("select * from store")
    for row in cur.fetchall():
        record = {'store_id': row['store_id'],
                  'manager_staff_id': f"staff:{row['manager_staff_id']}",
                  'address_id': f"address:{row['address_id']}",
                  'last_update': row['last_update'].isoformat()
                  }
        await import_object(dest_db,'store',row['store_id'], record)

async def import_customers(cur: RealDictCursor, dest_db: Surreal):
    '''import customer table, use record pointers to address'''
    await dest_db.delete("customer")
    cur.execute("select * from customer")
    for row in cur.fetchall():
        record = {'customer_id': row['customer_id'],
                  'first_name': row['first_name'],
                  'last_name': row['last_name'],
                  'email': row['email'],
                  'address_id': f"address:{row['address_id']}",
                  'create_date': row['create_date'].isoformat(),
                  'last_update': row['last_update'].isoformat()
                  }
        await import_object(dest_db,'customer',row['customer_id'], record)

async def import_countries(cur: RealDictCursor, dest_db: Surreal):
    '''import country table'''
    await dest_db.delete("country")
    cur.execute("select * from country")
    for row in cur.fetchall():
        record = {'country_id': row['country_id'],
                   'country': row['country'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(dest_db,'country',row['country_id'], record)

async def import_cities(cur: RealDictCursor, dest_db: Surreal):
    '''import city table, use record pointer to country'''
    await dest_db.delete("city")
    cur.execute("select * from city")
    for row in cur.fetchall():
        record = {
            'city_id': row['city_id'],
            'city': row['city'],
            'last_update': row['last_update'].isoformat(),
            'country_id': f"country:{row['country_id']}"
        }
        await import_object(dest_db,'city',row['city_id'], record)

async def import_address(cur: RealDictCursor, dest_db: Surreal):
    '''import address table, use record pointer to city'''
    await dest_db.delete("address")
    cur.execute("select * from address")
    for row in cur.fetchall():
        record = {'address_id': row['address_id'],
                'address': row['address'], 
                'address2': row['address2'], 
                'district': row['district'], 
                'city_id': f"city:{row['city_id']}",
                'postal_code': row['postal_code'], 
                'phone': row['phone'], 
                'last_update': row['last_update'].isoformat()}
        await import_object(dest_db,'address',row['address_id'], record)

async def import_inventory(cur: RealDictCursor, dest_db: Surreal):
    '''import inventory table, relate to film and store using graph edges'''
    await dest_db.delete("inventory")
    cur.execute("select * from inventory")
    for row in cur.fetchall():
        record = {'inventory_id': row['inventory_id'],
                   'last_update': row['last_update'].isoformat()
                   }
        await import_object(dest_db,'inventory',row['inventory_id'], record)
        query = f"RELATE inventory:{row['inventory_id']}->film_instance->film:{row['film_id']}"
        await dest_db.query(query)
        query = f"RELATE inventory:{row['inventory_id']}->in_store->store:{row['store_id']}"
        await dest_db.query(query)

async def import_rental(cur: RealDictCursor, dest_db: Surreal):
    '''import rentals, relate to inventory and customer using graph edges'''
    await dest_db.delete("rental")
    cur.execute("select * from rental")
    for row in cur.fetchall():
        return_date = row['return_date']
        if return_date is not None:
            return_date = return_date.isoformat()
        rental_date = row['rental_date']
        if rental_date is not None:
            rental_date = rental_date.isoformat()
        record = {'rental_id': row['rental_id'],
                   'customer_id': row['customer_id'],
                   'inventory_id': row['inventory_id'],
                   'rental_date': rental_date,
                   'return_date': return_date,
                   'last_update': row['last_update'].isoformat(),
                   }
        query = """CREATE type::thing("rental",$rental_id)
            SET last_update = type::datetime($last_update),
                rental_date=type::datetime($rental_date),
                return_date=type::datetime($return_date)
        """
        await dest_db.query(query, record)
        rental_id = record['rental_id']
        query = f"RELATE rental:{rental_id}->customer_rental->customer:{record['customer_id']}"
        await dest_db.query(query)
        query = f"RELATE rental:{rental_id}->inventory_rental->inventory:{record['inventory_id']}"
        await dest_db.query(query)

async def import_object(dest_db: Surreal, table: str, key: str, data: dict):
    '''shortcut for import. bit silly now'''
    await dest_db.create(f'{table}:{key}',data)

if __name__ == "__main__":
    asyncio.run(import_tables())
