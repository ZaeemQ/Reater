from flask import Flask, jsonify, request, render_template, redirect, url_for ,flash
from flask_restless import APIManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func 
from sqlalchemy import desc ,or_ ,asc
from forms import RestySearchForm 
from random import randint
import os 
from model import *

gen_int = lambda x : randint ( 0 , x - 1)
SECRET_KEY = os.urandom(24)

map_role =  dict([('0' , "Staff"), ('1',"Blogger") , ('2' ,"Food Critics")])

# random string generator
import random  
import string
def random_generator( size=10 ,chars = string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size) )


template_dir = os.path.abspath( "../template/" )
static_dir = os.path.abspath( "../static/" )

app = Flask( "Server" , template_folder = template_dir , static_folder = static_dir)
# Connecting to the database
app.config.from_pyfile ( 'config.py' )
app.config['SECRET_KEY']=SECRET_KEY
db = SQLAlchemy( app ) # database object


######### Create Read Update Delete ###########################

######### RESTAURANT ######### 

# show all restaurants
@app.route('/')
@app.route('/restaurant/' , methods=['GET','POST'])
def restaurants():
    restaurants = db.session.query(Restaurant).limit(12).all()
    for rest in restaurants:
        rest.location= Location.query.filter(
            Location.business_id == rest.business_id).first()
    cates = db.session.query(Restaurant.food_type.distinct().label("food_type"))
    all_cate = [ row.food_type for row in cates.all()]
    filters = list ( set([ y for x in all_cate for y in x ] ))
    random.shuffle( filters )
    
    # search bar
    form = RestySearchForm(request.form)

    return render_template('restaurants.html', restaurants = restaurants ,
                                               categories=filters[:5],
                                               form = form,
                                               cated=True)

@app.route('/sign_up/' , methods=['GET','POST'])
def register():
    return render_template( 'register.html')

@app.route('/restaurant/<catergories>')
def cateRestaurants(catergories):
    form = RestySearchForm(request.form)
    restaurant_ = Restaurant.query.filter(
        Restaurant.food_type.any(catergories)).all()
    
    # cated as false for skipping the category display
    return render_template('restaurants.html' , restaurants = restaurant_ , 
                                                catergories=catergories ,
                                                form = form,
                                                cated = False )

# create a new restaurant
@app.route('/restaurant/new/', methods=['GET','POST'])
def newRestaurant():
    if request.method == 'POST':
        location= Location( address = request.form['address'],
                            city = request.form['city'],
                            state = request.form['state'],
                            postal_code=request.form['post_code'])
        newRestaurant = Restaurant(name=request.form['name'],
                                    b_id=random_generator(),
                                    review_count=0,
                                    is_open = 0,
                                    stars=0,
                                    food_type=request.form['food_type'],
                                    location=location)
        db.session.add( location )
        db.session.add(newRestaurant)
        db.session.commit()
        return redirect(url_for('restaurants'))
    else:
        return render_template('newRestaurant.html')

# update a restaurant
@app.route('/restaurant/<string:business_id>/edit/',methods=['GET','POST'])
def editRestaurant(business_id):
    editedRestaurant = db.session.query(
        Restaurant).filter_by(business_id=business_id).one()
    if request.method == 'POST':
            if request.form['name']:
                editedRestaurant.name = request.form['name']
                return redirect(url_for('restaurants'))
    else:
            return render_template(
                'editRestaurant.html', restaurant = editedRestaurant)
    

# Delete the restaurant
@app.route('/restaurant/<string:business_id>/delete/', methods=['GET', 'POST'])
def deleteRestaurant(business_id):
    restaurantToDelete = db.session.query(
        Restaurant).filter_by(business_id=business_id).one()
    if request.method == 'POST':
        db.session.delete(restaurantToDelete)
        db.session.commit()
        return redirect(
            url_for('restaurants'))
    else:
        return render_template(
            'deleteRestaurant.html', restaurant=restaurantToDelete)


############# MenuItem #########
# Show Menu
@app.route('/restaurant/<string:business_id>')
@app.route('/restaurant/<string:business_id>/menu', methods=['GET','POST'])
def showMenu(business_id):
    location = Location.query.filter( Location.business_id == business_id ).all()
    restaurant = Restaurant.query.filter( Restaurant.business_id == business_id ).first()
    items = db.session.query(MenuItem).filter_by(
        business_id=business_id).limit(8)
    all_cate_avg =dict(db.session.query(
        MenuItem.category,func.avg(MenuItem.price)).group_by( MenuItem.category ).all())
    for key ,value in  all_cate_avg.items():
        all_cate_avg[key] = format( float( value ) , '.2f')
    
    most_expensive = db.session.query(MenuItem).order_by(
        desc(MenuItem.price)
    ).limit(1).first() 
    # select * from  MenuItem group by 
    
    return render_template('showMenu.html', items=items, 
                                            hours=restaurant.hours,
                                            business_id=business_id,
                                            restaurant=restaurant, 
                                            location=location,
                                            avg = all_cate_avg ,
                                            exp=most_expensive)

# Create a new menu item
@app.route(
    '/restaurant/<string:business_id>/menu/new/', methods=['GET', 'POST'])
def newMenuItem(business_id):
    if request.method == 'POST':
        newItem = MenuItem(name=request.form['name'], 
            description=request.form['description'], price=request.form['price'], item_type=request.form['category'], business_id=business_id)

        db.session.add(newItem)
        db.session.commit()

        return redirect(url_for('showMenu', business_id=business_id))
    else:
        return render_template('newmenuitem.html', business_id=business_id)


# Update a menu item
@app.route('/restaurant/<string:business_id>/menu/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editMenuItem(business_id, item_id):
    editedItem = db.session.query(MenuItem).filter_by(item_id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['name']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.category = request.form['course']
        db.session.add(editedItem)
        db.session.commit()
        return redirect(url_for('showMenu', business_id=business_id))
    else:

        return render_template(
            'editmenuitem.html', business_id=business_id, item_id=item_id, item=editedItem)

# Delete a menu item
@app.route('/restaurant/<string:business_id>/menu/<int:item_id>/delete',methods=['GET', 'POST'])
def deleteMenuItem(business_id, item_id):
    itemToDelete = db.session.query(MenuItem).filter_by(item_id=item_id).one()
    if request.method == 'POST':
        db.session.delete(itemToDelete)
        db.session.commit()
        return redirect(url_for('showMenu', business_id=business_id))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete, business_id=business_id,item_id=itemToDelete.item_id)

@app.route('/restaurant/<string:business_id>/rater_staff/')
def staff_poor_review( business_id ):
    # TODO not testing 
    result =  db.session.execute('''
    select rater.name , location.first_open_date , rating.mood from rater join 
    ( location join rating on location.business_id = rating.business_id)
    on rating.user_id = rater.user_id where rater.rater_type = '0' 
    group by rater.name ,location.first_open_date , rating.mood
    having rating.mood <= avg( rating.mood)''' ).fetchall()
    return render_template('')

@app.route('/restaurant/best/<string:catergory>/')
def best_catergory(catergory ):
    # TODO not testing 
    Best_cate = db.session.execute('''
    select rating,food_cate.cate_type from rating join ( 
	select unnest(restaurant.food_type) as cate_type, restaurant.business_id as b_id
	from restaurant
    ) as food_cate on rating.business_id = food_cate.b_id 
    where food_cate.cate_type='{}' 
    group by ( food_cate.cate_type , rating.mood , rating.* )
    having ( rating.mood >= avg(rating.mood) )
    order by rating.mood desc
    '''.format( catergory )).fetchall()
    pass 

#############  Raters #########
# show some raters in one page
# show answers for the last part in the same page
@app.route('/')
@app.route('/raters/')
def showRaters():
    counts = func.count(Rating.user_id).label("count_rating")
    rater = db.session.query( 
        Rater ,Restaurant, MenuItem ,Rating,
        MenuItem.item_id ,  Rater.user_id ,
        Rating.menu_id , Rating.business_id ,
        func.count(Rating.user_id).label("count_rating")).\
    filter(Rating.user_id == Rater.user_id).\
    filter(Restaurant.business_id == Rating.business_id).\
    filter(MenuItem.item_id == Rating.menu_id ).\
        group_by(Rater.name,Rater.user_id,
                 Restaurant.business_id  ,
                 MenuItem.item_id,
                 Rating.menu_id,
                 Rating.business_id,
                 Rating.id 
                 ).order_by( asc(counts)
    ).first()

    return render_template('raters.html', rater = rater[0], 
                                          restaurant=rater[1],
                                          item=rater[2],
                                          rating=rater[3])

    

# CRUD for raters

@app.route('/raterlist/' , methods=['GET','POST'])
def raterList():
    raterlist = db.session.execute( 
        '''
        select rater.name,rater.join_date, count(rating) , rater.user_id from rater join 
        rating on rater.user_id = rating.user_id group by
        rater.user_id 
        '''
    ).fetchall()
    rater_list = [ list(rater) for rater in raterlist]
    return render_template('raterlist.html',raterlist=raterlist)
 
# Create a new rater
@app.route('/raterlist/new/', methods=['GET', 'POST'])
def newRater():
    if request.method == 'POST':
        newRater = Rater(name=request.form['name'],
                        join_date=request.form['join_date'],
                        user_id=random_generator(),
                        reputation= gen_int(5),
                        rater_type=str( gen_int(3))
                        )
        db.session.add(newRater)
        db.session.commit()
 
        return redirect(url_for('raterList'))
    else:
        return render_template('newRater.html')    

# Update a rater
@app.route('/raterlist/<string:user_id>/edit/',methods=['GET','POST'])
def editRater(user_id):
    e_rater = db.session.query(
        Rater).filter_by(user_id=user_id).one()
    if request.method == 'POST':
            if request.form['name']:
                e_rater.name = request.form['name']
                return redirect(url_for('raterList'))
    else:
            return render_template(
                'editRater.html',e_rater=e_rater, user_id=e_rater.user_id)

# Delete a rater
@app.route('/raterlist/<string:user_id>/delete', methods=['GET', 'POST'])
def deleteRater(user_id):
    d_rater = db.session.query(
        Rater).filter_by(user_id=user_id)
    
    if request.method == 'POST':
        db.session.delete(d_rater)
        db.session.commit()
        return redirect(
            url_for('raterList'))
    else:
        return render_template(
            'deleteRater.html',rater=d_rater)

    

@app.route("/restaurants/search" , methods=['GET' ,'POST'])
def search():
    pass 
    
#############  Ratings #########
@app.route('/ratings/<string:business_id>/')
@app.route('/ratings/<string:business_id>/ratings')
def showRatings(business_id): 
    avg = format (float ( db.session.query( 
        func.avg(Rating.mood) ,  Rating.business_id
    ).filter( business_id == Rating.business_id ).group_by(
        Rating.business_id).first()[0]),".2f")
    
    result = db.session.query( 
        Rater  , Rating ).\
    filter( business_id == Rating.business_id).\
    filter(Rater.user_id == Rating.user_id ).group_by( 
         Rater , 
         Rating.id,
         Rating.date,
         Rating.comments,
        Rating.business_id).limit(20).all()
    result = [ list( x ) for x in  result  ]

    
    return render_template('ratings.html',ratings=result,total=avg )
@app.route('/restaurant/')
@app.route('/restaurant/news/')
def news():
    raterlist = db.session.execute( '''select rater.name, count(rating) as ratings
from rater join rating on rater.user_id=rating.user_id 
group by rater.name''' ).fetchall()

# restaurants
    restaurants = db.session().query( 
        Restaurant ,Rating , Location).\
    filter(
        func.extract('year',Rating.date) == '2015').\
    filter( 
        Location.business_id == Restaurant.business_id)\
    .limit(5).all() 
    restaurant , _ , location = zip(*restaurants)
    
    # raters
    raters = db.session().query( 
        Rater , func.min(Rating.mood) , 
        Location , Restaurant
    ).filter( 
        func.upper(Rater.name).like('Peter'.upper()) # since 0 is Staff in our description 
    ).filter( 
        Rating.business_id == Location.business_id
    ).filter(
        Restaurant.business_id == Rating.business_id
    ).group_by(
        Rater.user_id,
        Rating.mood,
        Location.location_id,
        Restaurant.business_id,
        Rating.date
    ).order_by( 
        asc(Rating.mood) ,
        func.DATE(Rating.date)).limit(20).all()
    
    # rest_spec
    rest_spec= raters[len(raters)-1][3]
    other_critics = db.session.query( 
        Restaurant,Rating.date , Rating.mood
    ).filter(
        Restaurant.business_id == rest_spec.business_id 
    ).group_by( 
        Restaurant.business_id,
        Rating.id,
        Rating.date
    ).order_by( Rating.date ).limit(10).all()

    Best_cate = db.session.execute('''
        select rating,food_cate.cate_type from rating join ( 
        select unnest(restaurant.food_type) as cate_type, restaurant.business_id as b_id
        from restaurant
        ) as food_cate on rating.business_id = food_cate.b_id 
        where food_cate.cate_type='{}' 
        group by ( food_cate.cate_type , rating.mood , rating.* )
        having ( rating.mood >= avg(rating.mood) )
        order by rating.mood desc
    '''.format( "Active Life")).fetchall()
    os.system("clear")

    return render_template('news.html' , restaurant=restaurant[0], 
                                         location = location[0] , 
                                         johns=raters[0],
                                         others=other_critics)

if __name__ == "__main__":
    app.run( port=5634,debug=True )
