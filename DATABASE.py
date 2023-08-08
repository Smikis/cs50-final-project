import sqlalchemy as sql
from sqlalchemy.sql import text

# Since this app was powered by Heroku, I used Heroku's Postgres database
# But I have commented out the code below because Heroku doesn't have a free plan anymore
# So the app doesn't run with the database anymore
# If you want to run the app with the database, you can use your own Postgres database

#engine = sql.create_engine('postgresql://jmcvecqsiondon:17c6494efc6d28c70608c58e384bce5a5e56b926eb49722ac5970d509e57c730@ec2-54-80-70-66.compute-1.amazonaws.com:5432/dbecgcb7b9rbq4')
#db = engine.connect()

def SQL(query, args={}):
    #if "SELECT" in query:
    #    data = db.execute(text(query), args).mappings().all()
    #    return data
    #else:
    #    db.execute(text(query), args)
    return None