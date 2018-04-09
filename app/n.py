from flask import Flask, jsonify, request, render_template, redirect, url_for 
from flask_restless import APIManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
import os , hashlib 
from base64 import encodestring 
from model import * 


template_dir = os.path.abspath( "../template/" )
static_dir = os.path.abspath( "../static/" )

app = Flask( "Server" , template_folder = template_dir , static_folder = static_dir)
# Connecting to the database
app.config.from_pyfile ( 'config.py' )
db = SQLAlchemy( app ) # database object



# Adding routes over here 


# Restaurant
@app.route( "/restaurants/<name>" , methods=['GET' , 'POST' , 'PUT','DELETE'] )
def restaurants(name):
    if request.method == 'GET':
        restaurant = Restaurant.query.filter( name == name ).first()
        location = Location.query.filter( Location.business_id == restaurant.business_id).first()
        restaurant.location = location 
        result = restaurant_schema.dump( restaurant )

    elif request.method == 'PUT':
        update_rest = Restaurant.query.filter( name == name ).first()
        update_rest.update( request.args )
        db.session().commit()
        result = restaurant_schema.dump( update_rest )
    
    elif request.method == 'POST':
        args =  dict(request.args)
        new_rest = Restaurant(business_id= 'RNANDOM_STR' ,
                            name=name,
                            review_count=0 ,
                            is_open=1 ,
                            stars=0.0 )
        db.session().add( new_rest )
        db.session().commit()
        result = restaurant_schema.dump( new_rest )

    elif request.method == 'DELETE':
        deleted_rest = Restaurant.query.filter( name == name ).first()
        Restaurant.query.filter( name == name ).delete()
        result  = restaurant_schema.dump( deleted_rest)
    return jsonify(result.data )

@app.route("/restaurants/" , methods=['GET'])
def restaurant():
    restaurants = Restaurant.query.limit( 10 ).all() 
    result=[]
    for rest in restaurants:
        rest.location = Location.query.filter( 
            Location.business_id == rest.business_id).first()
    result = restaurants_schema.dump( restaurants )
    return jsonify( result.data )

@app.route("/restaurants/location/<name>", methods=['POST'])
def open_new_location( name ):
    restaurants = Restaurant.query.filter( name==name).first()
    args = request.args 
    
    new_location = Location(address=args['address'],
                            city = args['city'],
                            postal_code=args['postcode'],
                            phone_number=args['phone_number'],
                            business_id=restaurant.business_id)
    db.session().add( new_location )
    db.session().commit()
    
    result = restaurant_schema.dump( restaurants )
    return jsonify( result.data )


@app.route("/locations/<id>", methods=['GET' ,'PUT','DELETE'])
def location(id):
    location = Location.query.filter( Location.location_id == id ).first()
    result = location_schema.dump( location )
    if request.method == 'GET':
        return jsonify( result.data )
    elif request.method == 'PUT':
        location.update( request.args )
        db.session().commit() 
    elif request.method == 'DELETE':
        location.delete()
        db.session().commit() 
        
    return jsonify( result.data )    




if __name__ == "__main__":
    app.run( debug=True , port= 5050)
    