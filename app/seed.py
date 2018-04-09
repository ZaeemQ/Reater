from sqlalchemy import create_engine
import os , sys , json , glob , itertools 
from random import randint

from sqlalchemy.orm import sessionmaker 
from timeit import timeit

import pandas as pd 
from pandas.io import sql 

try:
    from config import * 
except ModuleNotFoundError :
    print ( '''Please provide config.py for database connection:
                in which include:
                        host_name : ip addr for host
                        port      : port num for db
                        database  : name of db 
                        password  : password of dbadminstrator
                        user      : name pf dbadminstrator
                And 
                import os 
                basedir = os.path.abspath( os.path.dirname( __file__ ) )
                SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://{}:{}@{}:{}/{}".format( 
                        user, password , host_name , port , database )
            ''')
    sys.exit( -1 )

FOOD_description = [ "Amazing food and make with fish and salad.", 
                     "Baked with beef and mushroom and fish" ,
                     "Wrap with ham and baked with caskate iron chesse",
                     "Blend with mushroom and nuts and folded with meat in bake", 
                     "Reversed sears steak and alfredio sources", 
                     "Pastry baked steak in beef wellington" ]


# Importing model 
from model import *
from app import db  

sess = db.session() 
# db.create_all() 
# db.session.commit() 

gen_int = lambda x : randint ( 0 , x - 1)
auto_sample = lambda x : x % 300

def parse_restaurant( bucket , l_bucket, line , restaurant_id = None   ):
    item = json.loads( line ) 
    current_location = Location( item['address'],item['city'] ,
                                item['postal_code']  , 
                                item['business_id'] ,lat=item['latitude'], lon=item['longitude'])
    
    l_bucket.append( current_location )
    rest = Restaurant( 
                    item['business_id'], item['name']   , item['review_count'],
                    item['is_open' ]   , item[ 'stars' ],
                    item[ 'hours' ]    , food_type=item['categories'] , location=current_location )
    bucket.append( rest )
    
    restaurant_id.append ( item[ 'business_id' ] )
    

def parse_review( bucket  , line , user_id , rest_id , menu_id):
    item = json.loads( line )
    bucket.append ( Rating( user_id[ gen_int( len ( user_id ) ) ],
                                rest_id[ gen_int( len ( rest_id ) ) ],
                                item['date']   ,item['text'] , 
                                gen_int( 30 ) ,gen_int( 5 ) , menu_id[ gen_int (len( menu_id )) ]) )


def parse_user ( bucket , line , user_id ):
    item = json.loads ( line )
    bucket.append( Rater( item[ 'user_id' ]      ,item[ 'name' ],
                          item[ 'yelping_since' ],item[ 'average_stars' ] ,
                          gen_int(3) ))
    user_id.append ( item['user_id']) 
    
# read the csv file and insertting the data to the database
def read_csv_file ( file_folder    = "../dataset/" , 
                    file_name      = None  , 
                    restaurant_id  = None  , save = True ): 
    drop_columns = [ "menus_appeared" , "times_appeared" , 
                     "times_appeared" , "last_appeared"  ,
                     "first_appeared" ]
    menu_id =[]   
    category_id = [ 'Appetizers' , 'Entrees' , 'Desserts','Beverages']
    restaurant_id.remove( 'XIeu6wabop6VabOVFNVHIg' )
    if file_name and file_folder:
        file_ = os.path.join( file_folder , file_name )
        data = pd.read_csv( file_ )
        if not save: return list (data["item_id"])
        data.dropna( axis = 1 , how = 'any' , inplace = True )
        data.drop( columns = drop_columns , axis = 1 , inplace=True)
        data[ 'category' ]    = data.item_id.apply( lambda x : category_id[ gen_int( len( category_id ) ) ] )
        data[ 'business_id' ] = data.item_id.apply( lambda x : restaurant_id[ auto_sample( x ) ] )
        data[ 'price' ] = data.item_id.apply ( lambda x : gen_int ( 30 ) )
        data[ 'description' ] = data.item_id.apply ( lambda x : FOOD_description[gen_int(6)])
        if save :
            data.to_sql( "menuitem" , db.engine , if_exists='append' , index=False )
        return list(data['item_id'])
    

# Initializes the database 

def init_db( num_data = 300 , insert_threshhold = 100 , inserting=True):
    bus_bucket , location_bucket , user_bucket  = [] , [] , [] 
    user_id ,rating_bucket , rest_id  = [], [] , []

    print ( "Inserting data ......")
    
    print ( "Adding locations and busiensses ...... ")  
    
    
    with open("../dataset/business.json","r", buffering = insert_threshhold ) as businesses :        
        for count , business in enumerate( businesses.readlines() ):
            if count > num_data : break
            parse_restaurant( bus_bucket ,location_bucket, business  ,  
                restaurant_id= rest_id )
            
            if len( bus_bucket ) == insert_threshhold : 
                sess.add_all( bus_bucket )
                sess.commit()
                sess.add_all( location_bucket )
                sess.commit()
                location_bucket , bus_bucket = [] , [] 
                 
    # inserting menu_item 
    print ( "Adding menus........")
    menu_id = read_csv_file( file_name= "Dish.csv"  , restaurant_id= rest_id, save=True) 
    
    # inserting user 
    print ( "Adding users ...... ")
    with open("../dataset/user.json" , "r", buffering = insert_threshhold ) as rater:
        for count , rater in enumerate ( rater ):
            if count > num_data : break 
            parse_user( user_bucket , rater , user_id )
            if len( user_bucket ) == insert_threshhold :
                sess.add_all( user_bucket )
                user_bucket = [] 
                sess.commit() 
    
    user_id.remove( 'aRBFKDKgIfqtn83ZI4oNSQ' ) # avoid adding review issues 
    
    print ( "Adding reviews ...... ")
    with open("../dataset/review.json" , "r", buffering = 1000 ) as rating:
        for count , rater in enumerate (rating):
            if count  == num_data * 10 : break  
            parse_review ( rating_bucket , rater , user_id , rest_id ,menu_id )
            if  len(rating_bucket ) == insert_threshhold and inserting: # if the size of value reaches thresh hold 
                sess.add_all( rating_bucket )
                rating_bucket = []
                sess.commit() 
    


if __name__ == "__main__":
    db.create_all()
    db.session.commit() 
    init_db() 