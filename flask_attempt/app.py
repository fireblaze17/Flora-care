from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response, send_from_directory
import pymysql
import re
from datetime import datetime, timedelta
import pymysql.cursors
import firebase_admin
from firebase_admin import credentials, messaging
from apscheduler.schedulers.background import BackgroundScheduler
import tensorflow as tf
import numpy as np
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import io 
import keras
import plotly.graph_objs as go
import plotly.io as pio
import pandas as pd

cred = credentials.Certificate('static/computer-science-ia-floracare-firebase-adminsdk-rm6go-e589ffd970.json')
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

class Database:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.con = None
        self.cursor = None

    def connect(self):
        try:
            self.con = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
            self.cursor = self.con.cursor()
        except pymysql.Error as e:
            flash(f"Database error: {e}", 'danger')
            self.con, self.cursor = None, None

    def close(self):
        if self.con:
            self.con.close()

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except pymysql.Error as e:
            flash(f"Database error: {e}", 'danger')
            return None

class Plant:
    def __init__(self, plant_id, plant_name, location, watering_frequency, last_reset, is_sold, seed_cost, soil_cost, pot_cost, monthly_cost, date_added):
        self.plant_id = plant_id
        self.plant_name = plant_name
        self.location = location
        self.watering_frequency = watering_frequency
        self.last_reset = last_reset
        self.is_sold = is_sold
        self.seed_cost = seed_cost
        self.soil_cost = soil_cost
        self.pot_cost = pot_cost
        self.monthly_cost = monthly_cost
        self.date_added = date_added
    def to_dict(self):
        return {
            'plant_id': self.plant_id,
            'plant_name': self.plant_name,
            'location': self.location,
            'watering_frequency': self.watering_frequency,
            'is_sold': self.is_sold,
            'seed_cost': self.seed_cost,
            'soil_cost': self.soil_cost,
            'pot_cost': self.pot_cost,
            'monthly_cost': self.monthly_cost,
        
        }

    @classmethod
    def get_plant_by_id(cls, plant_id, user_id):
        db = Database(host="localhost", user="root", password="1234", database="userdata")
        db.connect()
        if not db.con:
            return None
        try:
            plant_data = db.execute_query("SELECT * FROM plants WHERE id = %s AND user_id = %s AND is_sold = FALSE", (plant_id, user_id))
            if plant_data:
                return cls(plant_data[0][0], plant_data[0][1], plant_data[0][2], plant_data[0][3], plant_data[0][4], plant_data[0][5], plant_data[0][6], plant_data[0][7], plant_data[0][8], plant_data[0][9], plant_data[0][10])
            else:
                return None
        finally:
            db.close()

    def get_last_reset(self):
        db = Database(host="localhost", user="root", password="1234", database="userdata")
        db.connect()
        if not db.con:
            return None
        try:
            last_reset_data = db.execute_query("SELECT last_reset FROM plants WHERE id = %s AND user_id = %s AND is_sold = FALSE", (self.plant_id, session['user_id']))
            if last_reset_data:
                return last_reset_data[0][0]
            else:
                return None
        finally:
            db.close()

    def reset_timer(self):
        db = Database(host="localhost", user="root", password="1234", database="userdata")
        db.connect()
        if not db.con:
            return False
        try:
            db.cursor.execute("UPDATE plants SET last_reset = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s", (self.plant_id, session['user_id']))
            db.con.commit()
            return True
        except pymysql.Error as e:
            db.con.rollback()
            return False
        finally:
            db.close()

    def save_to_database(self):
        db = Database(host="localhost", user="root", password="1234", database="userdata")
        db.connect()
        if not db.con:
            return False
        try:
            if self.plant_id is None:
                db.cursor.execute("""
                    INSERT INTO plants (plant_name, location, watering_frequency, seed_cost, soil_cost, pot_cost, monthly_cost, date_added, user_id, is_sold) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (self.plant_name, self.location, self.watering_frequency, self.seed_cost, self.soil_cost, self.pot_cost, self.monthly_cost, self.date_added, session['user_id'], self.is_sold))
                self.plant_id = db.cursor.lastrowid
            else:
                db.cursor.execute("""
                    UPDATE plants 
                    SET plant_name = %s, location = %s, watering_frequency = %s, seed_cost = %s, soil_cost = %s, pot_cost = %s, monthly_cost = %s
                    WHERE id = %s AND user_id = %s
                """, (self.plant_name, self.location, self.watering_frequency, self.seed_cost, self.soil_cost, self.pot_cost, self.monthly_cost, self.plant_id, session['user_id']))
            db.con.commit()
            return True
        except pymysql.Error as e:
            db.con.rollback()
            flash(f"Database error: {e}", 'danger')
            return False
        finally:
            db.close()



    def delete_from_database(self):
        db = Database(host="localhost", user="root", password="1234", database="userdata")
        db.connect()
        if not db.con:
            return False
        try:
            db.cursor.execute("DELETE FROM plants WHERE id = %s AND user_id = %s", (self.plant_id, session['user_id']))
            db.con.commit()
            return True
        except pymysql.Error as e:
            db.con.rollback()
            flash(f"Database error: {e}", 'danger')
            return False
        finally:
            db.close()
    @staticmethod
    def bubble_sort(plants):
        n = len(plants)
        for i in range(n):
            for j in range(0, n - i - 1):
                next_watering_time_j = plants[j].last_reset + timedelta(minutes=plants[j].watering_frequency)
                next_watering_time_j1 = plants[j + 1].last_reset + timedelta(minutes=plants[j + 1].watering_frequency)
                remaining_time_j = (next_watering_time_j - datetime.now()).total_seconds()
                remaining_time_j1 = (next_watering_time_j1 - datetime.now()).total_seconds()
                if remaining_time_j > remaining_time_j1:
                    plants[j], plants[j + 1] = plants[j + 1], plants[j]


class User:
    def __init__(self, user_id, email):
        self.user_id = user_id
        self.email = email
        self.plants = []

    @classmethod
    def get_user_by_credentials(cls, email, password):
        db = Database(host="localhost", user="root", password="1234", database="userdata")
        db.connect()
        if not db.con:
            return None
        try:
            user_data = db.execute_query("SELECT id, email FROM credentials WHERE email = %s AND password = %s", (email, password))
            if user_data:
                return cls(user_data[0][0], user_data[0][1])
            else:
                return None
        finally:
            db.close()

    def load_plants(self):
        self.plants = []
        db = Database(host="localhost", user="root", password="1234", database="userdata")
        db.connect()
        if not db.con:
            return
        try:
            plant_data_list = db.execute_query("SELECT * FROM plants WHERE user_id = %s AND is_sold = FALSE", (self.user_id,))
            for plant_data in plant_data_list:
                self.plants.append(Plant(plant_data[0], plant_data[1], plant_data[2], plant_data[3], plant_data[4], plant_data[5], plant_data[6], plant_data[7], plant_data[8], plant_data[9], plant_data[10]))
        finally:
            db.close()



@app.route('/')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/login', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']
    token = request.form.get('token')

    if not email or not password:
        flash("All fields are required", 'danger')
        return redirect(url_for('login'))

    user = User.get_user_by_credentials(email, password)
    if not user:
        flash("Invalid email or password", 'danger')
        return redirect(url_for('login'))

    # Store user details in session
    session['user_id'] = user.user_id
    session['email'] = user.email
    session['token'] = token

    # Update the token in the database
    db = Database(host="localhost", user="root", password="1234", database="userdata")
    db.connect()
    if db.con:
        try:
            db.cursor.execute("UPDATE credentials SET token = %s WHERE id = %s", (token, user.user_id))
            db.con.commit()
        except pymysql.Error as e:
            flash(f"Database error: {e}", 'danger')
        finally:
            db.close()

    flash("Login successful!", 'success')
    return redirect(url_for('homepage'))

@app.route('/homepage')
def homepage():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    user = User(session['user_id'], session['email'])
    user.load_plants()
    Plant.bubble_sort(user.plants)  # Sort the plants based on watering time

    # Convert each Plant object to a dictionary
    plant_list = [plant.to_dict() for plant in user.plants]

    return render_template('homepage.html', plants=plant_list)







@app.route('/editplant/<int:plant_id>', methods=['GET', 'POST'])
def editplant(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    plant = Plant.get_plant_by_id(plant_id, session['user_id'])
    if not plant:
        flash("Plant not found", 'danger')
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        plant.plant_name = request.form['plant_name']
        plant.location = request.form['location']
        plant.watering_frequency = request.form['watering_frequency']
        plant.seed_cost = float(request.form['seed_cost'])
        plant.soil_cost = float(request.form['soil_cost'])
        plant.pot_cost = float(request.form['pot_cost'])
        plant.monthly_cost = float(request.form['monthly_cost'])

        if plant.save_to_database():
            flash("Plant updated successfully!", 'success')
        else:
            flash("Failed to update plant!", 'danger')
        return redirect(url_for('homepage'))

    return render_template('editplant.html', plant=plant)

@app.route('/add_plant', methods=['GET', 'POST'])
def plantadd():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        plant_name = request.form['plant_name']
        location = request.form['location']
        watering_frequency = request.form['watering_frequency']
        seed_cost = float(request.form['seed_cost'])
        soil_cost = float(request.form['soil_cost'])
        pot_cost = float(request.form['pot_cost'])
        monthly_cost = float(request.form['monthly_cost'])
        date_added = datetime.now().date()
        plant = Plant(None, plant_name, location, watering_frequency, None, False, seed_cost, soil_cost, pot_cost, monthly_cost, date_added)

        if plant.save_to_database():
            flash("Plant added successfully!", 'success')
        else:
            flash("Failed to add plant!", 'danger')

        return redirect(url_for('homepage'))

    return render_template('plantadd.html')

@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    db = Database(host="localhost", user="root", password="1234", database="userdata")
    db.connect()
    if not db.con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('homepage'))

    try:
        sold_plants = db.execute_query("""
            SELECT p.plant_name, ps.selling_price, ps.total_cost, ps.date_sold, p.location
            FROM plants_sold ps
            JOIN plants p ON ps.plant_id = p.id
            WHERE ps.user_id = %s
        """, (session['user_id'],))

        return render_template('history.html', sold_plants=sold_plants if sold_plants else [])
    finally:
        db.close()

from datetime import datetime, timedelta

from datetime import datetime, timedelta

@app.route('/calculate_profit/<int:plant_id>', methods=['GET', 'POST'])
def calculate_profit(plant_id):
    plant = Plant.get_plant_by_id(plant_id, session['user_id'])
    if not plant:
        flash("Plant not found", 'danger')
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        try:
            profit_percentage = float(request.form['profit_percentage'])
        except ValueError:
            flash("Invalid profit percentage", 'danger')
            return redirect(url_for('calculate_profit', plant_id=plant_id))

        # Convert costs to float to avoid Decimal and float type mismatch issues
        seed_cost = float(plant.seed_cost)
        soil_cost = float(plant.soil_cost)
        pot_cost = float(plant.pot_cost)
        monthly_cost = float(plant.monthly_cost)

        # Get the date when the plant was added
        date_added = plant.date_added

        # Get the current date
        current_date = datetime.now().date()

        # Calculate the last day of the previous month once
        last_day_of_previous_month = (current_date.replace(day=1) - timedelta(days=1)).day

        # Calculate the total difference in years, months, and days
        year_difference = current_date.year - date_added.year
        month_difference = current_date.month - date_added.month
        day_difference = current_date.day - date_added.day

        # If the day difference is negative, adjust for fractional months
        if day_difference < 0:
            # Adjust by going back one month
            month_difference -= 1
            # Adjust the day difference by adding the days in the previous month
            day_difference += last_day_of_previous_month

        # Handle crossing into a new year (e.g., from December to January)
        if month_difference < 0:
            year_difference -= 1
            month_difference += 12

        # Calculate the total number of months, including fractional months
        total_months_passed = year_difference * 12 + month_difference + (day_difference / last_day_of_previous_month)

        # Calculate the total cost
        initial_cost = seed_cost + soil_cost + pot_cost
        total_monthly_cost = total_months_passed * monthly_cost
        total_cost = initial_cost + total_monthly_cost

        # Calculate selling price
        selling_price = total_cost * (1 + (profit_percentage / 100))
        selling_price = round(selling_price, 2)

        return render_template('confirm_sale.html', plant=plant, total_cost=round(total_cost, 2), selling_price=selling_price, plant_id=plant_id)

    return render_template('calculate_profit.html', plant=plant, plant_id=plant_id)





@app.route('/sell_plant/<int:plant_id>', methods=['POST'])
def sell_plant(plant_id):
    plant = Plant.get_plant_by_id(plant_id, session['user_id'])
    if not plant:
        flash("Plant not found", 'danger')
        return redirect(url_for('homepage'))

    total_cost = float(request.form['total_cost'])
    selling_price = float(request.form['selling_price'])
    date_sold = datetime.now().date()

    db = Database(host="localhost", user="root", password="1234", database="userdata")
    db.connect()
    if not db.con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('homepage'))

    try:
        db.cursor.execute('''
            INSERT INTO plants_sold (plant_id, total_cost, selling_price, date_sold, user_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', (plant.plant_id, total_cost, selling_price, date_sold, session['user_id']))
        db.cursor.execute('UPDATE plants SET is_sold = TRUE WHERE id = %s AND user_id = %s', (plant.plant_id, session['user_id']))
        db.con.commit()
        flash("Plant sold successfully!", 'success')
    except pymysql.Error as e:
        db.con.rollback()
        flash(f"Failed to sell plant: {e}", 'danger')
    finally:
        db.close()

    return redirect(url_for('homepage'))

from datetime import datetime

from datetime import datetime, timedelta

@app.route('/analytics', methods=['GET'])
def analytics():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    db = Database(host="localhost", user="root", password="1234", database="userdata")
    db.connect()
    if not db.con:
        flash("Database connection failed", 'danger')
        print("couldn't connect")
        return redirect(url_for('homepage'))

    try:
        # Fetch all sold plants' data
        db.cursor.execute('''
            SELECT date_sold, total_cost, selling_price
            FROM Plants_sold
            WHERE user_id = %s
        ''', (session['user_id'],))
        sold_plants_data = db.cursor.fetchall()
        print('Fetched sold data')

        # Fetch all unsold plants' data
        db.cursor.execute('''
            SELECT date_added, seed_cost, soil_cost, pot_cost, monthly_cost
            FROM plants
            WHERE user_id = %s AND is_sold = FALSE
        ''', (session['user_id'],))
        unsold_plants_data = db.cursor.fetchall()
        print('Fetched unsold data')

        # Initialize dictionary to store monthly totals
        monthly_totals = {}
        print("Initialized dictionary to store monthly totals")

        # Step 1: Process sold plants data
        for data in sold_plants_data:
            date_sold = data[0]  # datetime object
            total_cost_sold = float(data[1])
            total_revenue_sold = float(data[2])
            print('Processed sold plants data')

            # Extract month and year from the date_sold
            month_year_sold = date_sold.strftime("%m/%Y")
            print('Month and year extracted')

            # Initialize the dictionary for that month/year if not already there
            if month_year_sold not in monthly_totals:
                monthly_totals[month_year_sold] = {
                    "total_cost": 0,
                    "total_revenue": 0,
                    "profit": 0
                }
                print("Initialized dict for month/year")

            # Add sold plant costs and revenue to respective month
            monthly_totals[month_year_sold]["total_cost"] += total_cost_sold
            monthly_totals[month_year_sold]["total_revenue"] += total_revenue_sold
            print("Added sold plant cost and revenue to respective month")

        # Step 2: Process unsold plants
        current_date = datetime.now().date()  # Current date as date object
        print('Current date:', current_date)

        for plant in unsold_plants_data:
            date_added = plant[0]  # datetime.date object
            initial_cost = float(plant[1]) + float(plant[2]) + float(plant[3])
            monthly_cost = float(plant[4])
            print('Initial cost calc for unsold done')

            # Debug print
            print(f"date_added: {date_added}, type: {type(date_added)}")

            # No need to parse date_added since it's already a date object

            # Extract year and month from the date_added
            month_year_added = date_added.strftime("%m/%Y")
            print(f"month_year_added: {month_year_added}")

            # Add initial cost only in the month the plant was added
            if month_year_added not in monthly_totals:
                monthly_totals[month_year_added] = {
                    "total_cost": 0,
                    "total_revenue": 0,
                    "profit": 0
                }
                print('Added initial cost in the month the plant was added')

            monthly_totals[month_year_added]["total_cost"] += initial_cost

            # Add monthly costs for each month after the plant was added, including the current month
            date_pointer = date_added.replace(day=1)
            end_date = current_date.replace(day=1)
            print(f"Start date_pointer: {date_pointer}, End date: {end_date}")

            while date_pointer <= end_date:
                month_year = date_pointer.strftime("%m/%Y")
                if month_year not in monthly_totals:
                    monthly_totals[month_year] = {
                        "total_cost": 0,
                        "total_revenue": 0,
                        "profit": 0
                    }
                monthly_totals[month_year]["total_cost"] += monthly_cost
                # Move to the next month
                year = date_pointer.year + (date_pointer.month // 12)
                month = date_pointer.month % 12 + 1
                date_pointer = date_pointer.replace(year=year, month=month)
                print(f"Moved to next month: {date_pointer}")

        # Step 3: Calculate profits for each month
        for month_year in monthly_totals:
            monthly_totals[month_year]["profit"] = (
                monthly_totals[month_year]["total_revenue"] - monthly_totals[month_year]["total_cost"]
            )

        # Prepare data for passing to the frontend
        months = []
        total_costs = []
        total_revenues = []
        profits = []

        # Sort the months chronologically
        sorted_months = sorted(monthly_totals.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"))

        for month_year in sorted_months:
            data = monthly_totals[month_year]
            months.append(month_year)
            total_costs.append(data["total_cost"])
            total_revenues.append(data["total_revenue"])
            profits.append(data["profit"])

        # Create the bar chart with Plotly
        fig = go.Figure()
        fig.add_trace(go.Bar(x=months, y=total_costs, name='Total Costs', marker_color='#D32F2F'))
        fig.add_trace(go.Bar(x=months, y=total_revenues, name='Total Revenues', marker_color='#1976D2'))
        fig.add_trace(go.Bar(x=months, y=profits, name='Profits', marker_color='#388E3C'))
        fig.update_layout(title='Monthly Analytics', xaxis_title='Month', yaxis_title='Amount ($)', barmode='group')

        # Generate the graph HTML to render in the template
        graph_html = pio.to_html(fig, full_html=False)

        return render_template('analytics.html', graph_html=graph_html)

    except Exception as e:
        print(f"An error occurred: {e}")
        flash(f"An error occurred while processing your request: {e}", 'danger')
        return redirect(url_for('homepage'))

    finally:
        db.close()



@app.route('/planthealth', methods=['GET', 'POST'])
def planthealth():
    model = tf.keras.models.load_model('../trained_model_v2.h5')

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename != '':
            try:
                file_stream = io.BytesIO(file.read())
                file_stream.seek(0)
                img = image.load_img(file_stream, target_size=(224, 224))
                img_array = image.img_to_array(img)
                img_array = tf.keras.applications.resnet_v2.preprocess_input(img_array)
                img_array = np.expand_dims(img_array, axis=0)
                predictions = model.predict(img_array)
                predicted_class = np.argmax(predictions)

                class_names = [
                    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
                    'Blueberry___healthy', 'Cherry_(including_sour)___Powdery_mildew', 
                    'Cherry_(including_sour)___healthy', 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 
                    'Corn_(maize)___Common_rust_', 'Corn_(maize)___Northern_Leaf_Blight', 'Corn_(maize)___healthy', 
                    'Grape___Black_rot', 'Grape___Esca_(Black_Measles)', 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 
                    'Grape___healthy', 'Orange___Haunglongbing_(Citrus_greening)', 'Peach___Bacterial_spot',
                    'Peach___healthy', 'Pepper,_bell___Bacterial_spot', 'Pepper,_bell___healthy', 
                    'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy', 
                    'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew', 
                    'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot', 
                    'Tomato___Early_blight', 'Tomato___Late_blight', 'Tomato___Leaf_Mold', 
                    'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites Two-spotted_spider_mite', 
                    'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus',
                    'Tomato___healthy'
                ]
                prediction_text = class_names[predicted_class]

                return render_template('planthealth.html', prediction=prediction_text)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        else:
            return render_template('planthealth.html', prediction='No image selected or uploaded')
    return render_template('planthealth.html')

@app.route('/search_plants', methods=['GET'])
def search_plants():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    query = request.args.get('query')
    user = User(session['user_id'], session['email'])
    user.load_plants()

    # Search for plants that match the query
    filtered_plants = [plant for plant in user.plants if query.lower() in plant.plant_name.lower()]

    # Convert Plant objects to dictionaries
    filtered_plant_list = [plant.to_dict() for plant in filtered_plants]

    return render_template('homepage.html', plants=filtered_plant_list)




@app.route('/deleteplant/<int:plant_id>', methods=['POST'])
def deleteplant(plant_id): 
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    plant = Plant.get_plant_by_id(plant_id, session['user_id'])
    if not plant:
        flash("Plant not found", 'danger')
        return redirect(url_for('homepage'))

    if plant.delete_from_database():
        flash("Plant deleted successfully!", 'success')
    else:
        flash("Failed to delete plant!", 'danger')

    return redirect(url_for('homepage'))


@app.route('/firebase-messaging-sw.js')
def serve_firebase_sw():
    return send_from_directory(app.static_folder, 'firebase-messaging-sw.js')

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

def send_notification(token, plant_name, location):
    message = messaging.Message(
        notification=messaging.Notification(
            title="Watering Reminder",
            body=f"Time to water {plant_name} at {location}",
        ),
        token=token,
    )

    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print('Failed to send message:', str(e))

def check_and_notify():
    print('Running check_and_notify...')
    db = Database(host="localhost", user="root", password="1234", database="userdata")
    db.connect()
    if not db.con:
        return
    try:
        now = datetime.now()
        plants_to_notify = db.execute_query("SELECT p.id, p.plant_name, p.location, p.watering_frequency, p.last_reset, c.token FROM plants p JOIN credentials c ON p.user_id = c.id WHERE p.is_sold = FALSE", ())
        
        for plant in plants_to_notify:
            plant_id, plant_name, location, watering_frequency, last_reset, token = plant

            # Update to use watering_frequency as minutes
            next_watering_time = last_reset + timedelta(minutes=watering_frequency)

            # Debugging statements
            print(f'Checking plant: {plant_name}')
            print(f'Last reset: {last_reset}, Watering frequency (minutes): {watering_frequency}')
            print(f'Next watering time: {next_watering_time}, Current time: {now}')

            if now >= next_watering_time:
                print(f'Sending notification for plant: {plant_name}')
                send_notification(token, plant_name, location)
    except Exception as e:
        print("Database error:", e)
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="interval", minutes=1)
scheduler.start()





@app.route('/get_last_reset/<int:plant_id>', methods=['GET'])
def get_last_reset_route(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return jsonify({'status': 'error', 'message': 'You are not logged in!'}), 403

    plant = Plant.get_plant_by_id(plant_id, session['user_id'])
    if not plant:
        return jsonify({'status': 'error', 'message': 'Plant not found'}), 404

    last_reset = plant.get_last_reset()
    if last_reset:
        return jsonify({'status': 'success', 'last_reset': last_reset.strftime('%Y-%m-%d %H:%M:%S')})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to fetch last reset time'}), 500

@app.route('/reset_timer/<int:plant_id>', methods=['POST'])
def reset_timer_route(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return jsonify({'status': 'error', 'message': 'You are not logged in!'}), 403

    plant = Plant.get_plant_by_id(plant_id, session['user_id'])
    if not plant:
        return jsonify({'status': 'error', 'message': 'Plant not found'}), 404

    if plant.reset_timer():
        return jsonify({'status': 'success', 'message': 'Timer reset successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to reset timer'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)