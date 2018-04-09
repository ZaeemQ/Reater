from app import db , app
from sqlalchemy.types import ARRAY as Array
from flask import Flask, jsonify, abort, request
from flask_marshmallow import Marshmallow
from flask_marshmallow.sqla import HyperlinkRelated
from flask_marshmallow import fields 
from base64 import encodestring 
from marshmallow import Schema, fields, pprint

ma = Marshmallow( app )

import random , os ,string , faker
def random_generator( size=10 ,chars = string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size) )


fake = faker.Faker()


class Location(db.Model):
    __tablename__='location'
    address         = db.Column(db.String)
    city            = db.Column(db.String)
    state           = db.Column(db.String)
    postal_code     = db.Column(db.String)
    latitude        = db.Column(db.Float)
    longtitude      = db.Column(db.Float)

    location_id = db.Column(db.Integer , primary_key=True )
    first_open_date = db.Column(db.DateTime) 
    manager_name = db.Column(db.String)
    phone_number = db.Column(db.String(10))
    hour_open = db.Column( Array( db.String( 7)))
    hour_close = db.Column( Array( db.String( 7)))

    # restaurant id is a foreign key
    business_id  = db.Column(db.String (22), db.ForeignKey('restaurant.business_id'))
    business = db.relationship('Restaurant',backref='Restaurant')
    def __init__(self ,address, city , post_code , business_id ,
        lat = None , lon=None  ):
        self.address = address
        self.city = city
        self.postal_code =post_code
        self.phone_number = random_generator()
        self.business_id =business_id
        self.manager_name = random_generator()
        if lat : self.latitude = lat
        if lon : self.longtitude = lon
        self.first_open_date = fake.date_time_between( start_date='-50y',end_date= 'now')

    def update ( self , args ): 
        for key , value in args.items():
            if key == 'address' : self.name=value
            if key == 'city': self.city = value 
            if key == 'state' : self.state = value 
            if key == 'post_code': self.postcode = value
            if key == 'phone_number': self.phone_number = int(value)
            if key == 'hour_open': self.hour_open.append( value )
            if key == 'hour_close': self.hour_close.append( value )
            
class MenuItem(db.Model):
    __tablename__='menuitem'
    item_id  = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String) 

    # starter, main, desert 
    category = db.Column(db.String) 
    description  = db.Column(db.String)
    price  = db.Column(db.Integer)

    # restaurant id is a foreign key
    business_id  = db.Column(db.String (22), db.ForeignKey('restaurant.business_id'))

    # M menu item  has N ratings
    ratings = db.relationship('Rating') 
    def __init__ ( self  ,
                   name  ,  item_type , description ,  
                   price , business_id ): 
        self.item_id = db.session.execute('''
            select count(*) from menuitem     
            ''').fetchall ()[0][0]+1
        self.name = name 
        self.description = description 
        self.price = price 
        self.business_id = business_id
        self.category = item_type
                
class Rater(db.Model):
    __tablename__='rater'

    #mapper
    user_id = db.Column(db.String (22), primary_key=True)
    email = db.Column(db.String (120) , unique=True )

    # an alias such as SuperSizeMe
    name = db.Column(db.String)

    # show when this rater first joined the website
    join_date = db.Column(db.DateTime)

    # type of rater (staff, online, food critic)
    rater_type = db.Column(db.Integer) 

    # takes a value between 1 and 5
    # the value db.Modeld on the number of people who found 
    # this  rater’s opinion helpful, and the default value is 1 (lowest).
    reputation = db.Column(db.Integer) 

    # 1 rater writes N ratings
    ratings = db.relationship('Rating')

    def __init__(self, user_id, name, join_date, reputation , rater_type):
        self.user_id = user_id
        self.name = name
        self.join_date = join_date
        self.reputation = reputation
        self.rater_type = rater_type  # (blog, online, food critic)
        self.email = random_generator(size=4)+"@gmail.com"

class Rating(db.Model):
    __tablename__='rating'

    #mapper
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String (22), db.ForeignKey('rater.user_id'))
    business_id  = db.Column(db.String (22), db.ForeignKey('restaurant.business_id'))
    date = db.Column(db.DateTime)
    menu_id = db.Column( db.Integer , db.ForeignKey( 'menuitem.item_id'))
    
    # price, food, mood, staff attributes may 
    # take a value between 1(low) to 5(high)
    price = db.Column(db.Integer)
    mood = db.Column(db.Integer)
    comments =db.Column(db.String)

    def __init__(self, user_id, business_id, date, comments , price  ,mood , menu_id):
        self.user_id = user_id
        self.business_id = business_id
        self.date = date
        self.comments = comments
        self.price = price 
        self.menu_id = menu_id
        self.mood = mood 

class Restaurant(db.Model,object):
    __tablename__='restaurant'

    business_id = db.Column(db.String (22), primary_key=True)
    name = db.Column(db.String)

    stars = db.Column(db.Float) 
    review_count = db.Column(db.Integer)

    # 0 for closed, 1 for open
    is_open = db.Column(db.Integer)

    # type  attribute contains details about the cuisine, 
    # such as Italian, Indian, Middle Eastern, and so on.
    food_type = db.Column( Array( db.String))
    hours = db.Column( Array( db.String( 20 ))) # [ "Mon", "Tue" ... ]

    URL = db.Column(db.String)

    # 1 restaurant has N ratings
    ratings = db.relationship('Rating')

    # 1 restaurant has N locations
    locations = db.relationship('Location' ,backref='restaurant' , lazy=True)

    # 1 restaurant serves M menu items
    items = db.relationship('MenuItem' , backref = 'restaurant' , lazy=True)

    def __init__(self  , b_id,
                name   , review_count,
                is_open, stars, 
                hours  , food_type=None , location=None ) :

        self.business_id=b_id
        self.name=name
        self.stars = stars
        self.review_count=review_count
        self.is_open=is_open
        self.hours = [ hour for day , hour in hours.items()  ]
        if food_type: self.food_type = food_type 
        if location: self.location = location 
        self.URL =  "https://"+random_generator(size=9)+".com"


    def update ( self , args ):
        for key , value in dict(args).items():
            if key == 'name' : self.name=value
            if key == 'food_type': self.food_type.append( value )
            if key == 'rating' : self.ratings = value 
            if key == 'review_count': self.review_count = value
            if key == 'location': self.location = Location(value)
  
    def open ( self ): 
        self.open = not self.open
    
    def addReview( self ):
        self.review = self.review+1

class MenuItemSchema(ma.Schema):
    name = fields.String()
    description = fields.String()
    price = fields.String() 

class LocationSchema(ma.Schema):
    address = fields.String()
    city = fields.String()
    post_code = fields.String()

class RestaurantSchema( ma.Schema ):
    business_id = fields.String()
    name = fields.String()
    is_open = fields.Integer()
    food_type = fields.List(fields.String())
    URL = fields.String() 
    location = fields.Nested( LocationSchema  )
    menus = fields.Nested( MenuItemSchema )
    

class RaterSchema(ma.Schema):
    class Meta:
        fields = ('user_id','name')

class RatingSchema(ma.Schema):
    class Meta:
        fields = ('user_id ', 'date ')

class RatingItemSchema(ma.Schema):
    class Meta:
        fields = ('item_id','date')


# Formating the right models 
restaurants_schema = RestaurantSchema( many=True )
restaurant_schema = RestaurantSchema()


locations_schema = LocationSchema(many = True)
location_schema = LocationSchema()

menuitems_schema = MenuItemSchema(many = True)
menuitem_schema = MenuItemSchema()

raters_schema = RaterSchema(many = True)
rater_schema = RaterSchema()

ratings_schema = RatingSchema(many = True)
rating_schema = RatingSchema()

ratingitems_schema = RatingItemSchema(many = True)
ratingitem_schema = RatingItemSchema()

