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
from flask import render_template

cred = credentials.Certificate('static/computer-science-ia-floracare-firebase-adminsdk-rm6go-e589ffd970.json')
firebase_admin.initialize_app(cred)

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def connect_database():
    try:
        con = pymysql.connect(host="localhost", user="root", password="1234", database="userdata")
        mycursor = con.cursor()
        return con, mycursor
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        return None, None

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')




@app.route('/homepage')
def homepage():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('login'))

    try:
        # Select only the plants that belong to the logged-in user
        mycursor.execute("SELECT * FROM plants WHERE user_id=%s AND is_sold = FALSE", (session['user_id'],))
        plants = mycursor.fetchall()
        
        # Current time
        now = datetime.now()
        
        # Convert tuples to lists and add remaining time to each plant list
        plant_list = [list(plant) for plant in plants]
        for plant in plant_list:
            last_reset = plant[4]  # assuming index 4 is last_reset, which is a datetime
            watering_freq = plant[3]  # assuming index 3 is watering_frequency in hours
            next_watering_time = last_reset + timedelta(hours=watering_freq)
            remaining_time = (next_watering_time - now).total_seconds()
            plant.append(remaining_time)
        
        # Sort plants using bubble sort based on remaining_time
        # n = len(plant_list)
        print(plant_list)
        bubble_sort(plant_list, 4)
        # plant_list.sort(key=lambda x: x[4])
        # for i in range(n):
        #     for j in range(0, n-i-1):
        #         # If the plant[j] has more time left than plant[j+1], swap them
        #         if plant_list[j][-1] > plant_list[j+1][-1]:
        #             plant_list[j], plant_list[j+1] = plant_list[j+1], plant_list[j]
        
        # Render the sorted list
        return render_template('homepage.html', plants=plant_list)
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        return redirect(url_for('login'))
    finally:
        con.close()

def bubble_sort(data, key):
    n = len(data)
    # Traverse through all elements in the list
    for i in range(n):
        # Last i elements are already in place
        for j in range(0, n-i-1):
            # Traverse the list from 0 to n-i-1
            # Swap if the element found is greater than the next element
            if data[j][key] > data[j+1][key]:
                data[j], data[j+1] = data[j+1], data[j]



def calculate_total_cost(plant):
    """
    Calculates the total cost of the plant based on its initial costs and monthly cost.
    :param plant: A dictionary or object containing the plant's details.
    :return: Total cost of the plant.
    """
    # Initial costs
    initial_cost = plant['seed_cost'] + plant['soil_cost'] + plant['pot_cost']
    
    # Date calculations
    date_added = plant['date_added']  # This should be a datetime.date object
    current_date = datetime.now().date()

    # Calculate the difference in months (including fractional months)
    total_months = (current_date.year - date_added.year) * 12 + (current_date.month - date_added.month)
    days_difference = (current_date - date_added).days
    days_in_month = (date_added.replace(month=date_added.month % 12 + 1, day=1) - date_added).days
    fractional_month = days_difference / days_in_month
    
    # If the difference is within the same month
    total_months += fractional_month
    
    # Monthly cost calculation
    total_monthly_cost = plant['monthly_cost'] * total_months
    
    # Total cost = Initial cost + Monthly cost
    total_cost = initial_cost + total_monthly_cost
    return total_cost

@app.route('/calculate_profit/<int:plant_id>', methods=['GET', 'POST'])
def calculate_profit(plant_id):
    # Connect to the database
    con, mycursor = connect_database()
    if not con:
        print("Database connection failed")  # Debugging line
        return redirect(url_for('homepage'))

    print(f"Connected to database. Plant ID: {plant_id}")  # Debugging line

    if request.method == 'POST':
        print("POST request received")  # Debugging line

        # Get the profit percentage from the form
        try:
            profit_percentage = float(request.form['profit_percentage'])
            print(f"Profit percentage entered: {profit_percentage}")  # Debugging line
        except ValueError as e:
            print(f"Error converting profit percentage: {e}")  # Debugging line
            return redirect(url_for('homepage'))

        try:
            # Fetch the plant details from the database
            print(f"Fetching plant with ID: {plant_id} for user ID: {session['user_id']}")  # Debugging line
            mycursor.execute('SELECT * FROM plants WHERE id = %s AND user_id = %s AND is_sold = FALSE', (plant_id, session['user_id']))
            plant = mycursor.fetchone()

            if plant is None:
                print("Plant not found in the database")  # Debugging line
                return redirect(url_for('homepage'))

            # Convert decimal.Decimal values to float before calculations
            seed_cost = float(plant[6])
            soil_cost = float(plant[7])
            pot_cost = float(plant[8])
            monthly_cost = float(plant[9])
            date_added = plant[10]  # No need to convert date

            print(f"Plant details: seed_cost={seed_cost}, soil_cost={soil_cost}, pot_cost={pot_cost}, monthly_cost={monthly_cost}, date_added={date_added}")  # Debugging line

            # Calculate the total cost of the plant
            total_cost = calculate_total_cost({
                'seed_cost': seed_cost,
                'soil_cost': soil_cost,
                'pot_cost': pot_cost,
                'monthly_cost': monthly_cost,
                'date_added': date_added
            })
            total_cost = round(total_cost, 2)
            print(f"Total cost calculated: {total_cost}")  # Debugging line

            # Calculate the selling price based on the profit percentage
            selling_price = total_cost * (1 + (profit_percentage / 100))
            selling_price = round(selling_price, 2)
            print(f"Selling price calculated: {selling_price}")  # Debugging line

            # Render the confirmation page with the calculated selling price
            # Passing plant_id explicitly to the template
            return render_template('confirm_sale.html', plant_id=plant[0], plant=plant, selling_price=selling_price, total_cost=total_cost)

        except Exception as e:
            print(f"Error occurred: {e}")  # Debugging line
            return redirect(url_for('homepage'))

        finally:
            print("Closing database connection")  # Debugging line
            mycursor.close()
            con.close()

    print("GET request received, rendering form")  # Debugging line
    # If GET request, render the form for inputting profit percentage
    return render_template('calculate_profit.html', plant_id=plant_id)


@app.route('/analytics', methods=['GET'])
def analytics():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('homepage'))

    try:
        print("Connected to the database.")  # Debugging

        # Query 1: Get sold plants grouped by month
        mycursor.execute("""
            SELECT 
                MONTH(date_sold) AS month, 
                YEAR(date_sold) AS year, 
                SUM(total_cost) AS total_cost, 
                SUM(selling_price) AS total_revenue
            FROM plants_sold
            WHERE user_id = %s
            GROUP BY YEAR(date_sold), MONTH(date_sold)
        """, (session['user_id'],))

        sold_plants_data = mycursor.fetchall()
        print(f"Sold plants data fetched: {sold_plants_data}")  # Debugging

        # Query 2: Get unsold plants' monthly cost for the current month
        mycursor.execute("""
            SELECT 
                SUM(monthly_cost) AS total_cost
            FROM plants
            WHERE user_id = %s AND is_sold = FALSE
        """, (session['user_id'],))

        unsold_plants_cost_data = mycursor.fetchone()
        unsold_plants_cost = unsold_plants_cost_data[0] if unsold_plants_cost_data else 0
        print(f"Unsold plants cost: {unsold_plants_cost}")  # Debugging

        # Process the data for plotting
        months = []
        total_costs = []
        total_revenues = []
        profits = []

        for data in sold_plants_data:
            # Access tuple elements by index instead of string keys
            month_year = f"{data[0]}/{data[1]}"  # data[0] is month, data[1] is year
            total_cost = float(data[2]) + float(unsold_plants_cost)  # data[2] is total_cost
            total_revenue = float(data[3])  # data[3] is total_revenue
            profit = total_revenue - total_cost

            print(f"Month: {month_year}, Total Cost: {total_cost}, Total Revenue: {total_revenue}, Profit: {profit}")  # Debugging

            months.append(month_year)
            total_costs.append(total_cost)
            total_revenues.append(total_revenue)
            profits.append(profit)

        # Create Plotly bar chart
        fig = go.Figure()

        # Total Costs Bar
        fig.add_trace(go.Bar(
            x=months,
            y=total_costs,
            name='Total Costs',
            marker_color='#D32F2F'  # Darker red for a professional look
        ))

        # Total Revenues Bar
        fig.add_trace(go.Bar(
            x=months,
            y=total_revenues,
            name='Total Revenues',
            marker_color='#1976D2'  # Professional blue for revenue
        ))

        # Profits Bar
        fig.add_trace(go.Bar(
            x=months,
            y=profits,
            name='Profits',
            marker_color='#388E3C'  # Professional green for profits
        ))

        # Customize layout
        fig.update_layout(
            title='Monthly Analytics',
            title_font=dict(
                size=24,
                color='#004d40'  # Dark green for the title, matching theme
            ),
            xaxis_tickfont_size=14,
            yaxis=dict(
                title='Amount in $',
                titlefont=dict(size=16, color='#333'),  # Professional dark color for the axis title
                tickfont=dict(size=14, color='#555'),  # Subtle dark gray for the tick labels
            ),
            barmode='group',  # Show bars side by side
            xaxis_title='Month',
            yaxis_title='Amount ($)',
            legend=dict(
                x=0,
                y=1.0,
                bgcolor='rgba(255, 255, 255, 0)',  # Transparent background for legend
                bordercolor='rgba(255, 255, 255, 0)',
                font=dict(size=12, color='#333')  # Dark color for legend text
            ),
            plot_bgcolor='#f9f9f9',  # Light background for the plot area
            paper_bgcolor='#ffffff',  # White background for the outer area
            xaxis=dict(
                titlefont=dict(size=16, color='#333'),  # Professional color for x-axis
                tickfont=dict(size=14, color='#555'),  # Darker tick labels for x-axis
            )
        )

        # Convert Plotly figure to HTML div
        graph_html = pio.to_html(fig, full_html=False)

        print("Chart generated successfully.")  # Debugging
        return render_template('analytics.html', graph_html=graph_html)

    except Exception as e:
        print(f"Error occurred: {e}")  # Debugging
        flash(f"Database error: {e}", 'danger')
        return redirect(url_for('homepage'))

    finally:
        con.close()
        print("Database connection closed.")  # Debugging






@app.route('/sell_plant/<int:plant_id>', methods=['POST'])
def sell_plant(plant_id):
    try:
        # Retrieve the form data
        total_cost = float(request.form['total_cost'])
        selling_price = float(request.form['selling_price'])
        date_sold = datetime.now().date()
        print(f"Received total_cost: {total_cost}, selling_price: {selling_price}, date_sold: {date_sold}")  # Debugging

        # Connect to the database
        con, mycursor = connect_database()
        if not con:
            print("Database connection failed")  # Debugging
            return redirect(url_for('homepage'))

        print(f"Connected to the database for plant ID: {plant_id}")  # Debugging

        # Check if the plant exists and is not sold
        mycursor.execute('SELECT id FROM plants WHERE id = %s AND user_id = %s AND is_sold = FALSE', (plant_id, session['user_id']))
        plant = mycursor.fetchone()
        print(f"Fetched plant: {plant}")  # Debugging

        if plant is None:
            print("Plant not found in the database or already sold")  # Debugging
            return redirect(url_for('homepage'))

        # Insert plant details into the Plants_sold table (without plant_name)
        mycursor.execute('''
            INSERT INTO Plants_sold (plant_id, total_cost, selling_price, date_sold, user_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', (plant_id, total_cost, selling_price, date_sold, session['user_id']))
        print("Inserted plant into Plants_sold")  # Debugging

        # Mark the plant as sold in the plants table
        mycursor.execute('UPDATE plants SET is_sold = TRUE WHERE id = %s AND user_id = %s', (plant_id, session['user_id']))
        print("Marked plant as sold in plants table")  # Debugging

        # Commit the changes
        con.commit()
        print("Transaction committed")  # Debugging

        flash("Plant sold and removed successfully!", 'success')
        return redirect(url_for('homepage'))

    except Exception as e:
        print(f"Error occurred during sale: {e}")  # Debugging
        con.rollback()
        return redirect(url_for('homepage'))

    finally:
        if mycursor:
            mycursor.close()
        print("Database connection closed")  # Debugging
        if con:
            con.close()




@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('homepage'))

    try:
        # Use a JOIN statement to get the plant details from the 'plants' table and sold details from 'plants_sold' table
        mycursor.execute("""
            SELECT p.plant_name, ps.selling_price, ps.total_cost, ps.date_sold, p.location
            FROM plants_sold ps
            JOIN plants p ON ps.plant_id = p.id
            WHERE ps.user_id = %s
        """, (session['user_id'],))

        sold_plants = mycursor.fetchall()
        print(f"Fetched sold plants: {sold_plants}")  # Debugging

        if not sold_plants:
            flash("No plants sold yet!", 'info')
            return render_template('history.html', sold_plants=[])

        return render_template('history.html', sold_plants=sold_plants)

    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        return redirect(url_for('homepage'))
    finally:
        con.close()




@app.route('/editplant/<int:plant_id>', methods=['GET', 'POST'])
def editplant(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        location = request.form['location']
        frequency = request.form['frequency']
        
        print(f"POST data received: name={name}, location={location}, frequency={frequency}")

        # Convert costs to float
        try:
            seed_cost = float(request.form['seed_cost'])
            soil_cost = float(request.form['soil_cost'])
            pot_cost = float(request.form['pot_cost'])
            monthly_cost = float(request.form['monthly_cost'])
            print(f"Costs received: seed_cost={seed_cost}, soil_cost={soil_cost}, pot_cost={pot_cost}, monthly_cost={monthly_cost}")
        except ValueError as ve:
            print(f"Error converting costs: {ve}")
            flash("Invalid input for cost fields. Please enter valid numbers.", 'danger')
            return redirect(url_for('editplant', plant_id=plant_id))

        # Validate required fields
        if name == '' or location == '' or frequency == '':
            print("Validation failed: One or more required fields are missing")
            flash("All fields are required", 'danger')
            return redirect(url_for('editplant', plant_id=plant_id))

        try:
            # Update plant in the database
            print("Attempting to update the plant in the database")
            mycursor.execute("""
                UPDATE plants 
                SET plant_name=%s, location=%s, watering_frequency=%s, seed_cost=%s, soil_cost=%s, pot_cost=%s, monthly_cost=%s 
                WHERE id=%s AND user_id=%s
            """, (name, location, frequency, seed_cost, soil_cost, pot_cost, monthly_cost, plant_id, session['user_id']))
            
            con.commit()
            print("Plant updated successfully in the database")
            flash("Plant updated successfully!", 'success')
            return redirect(url_for('homepage'))
        except pymysql.Error as e:
            print(f"Database error during update: {e}")
            flash(f"Database error: {e}", 'danger')
            con.rollback()
        finally:
            con.close()
            print("Database connection closed after POST request")

    if request.method == 'GET':
        try:
            # Fetch plant details for pre-filling the form
            print(f"Fetching plant details for plant ID: {plant_id}")
            mycursor.execute("""
                SELECT id, plant_name, location, watering_frequency, seed_cost, soil_cost, pot_cost, monthly_cost 
                FROM plants 
                WHERE id=%s AND user_id=%s AND is_sold = FALSE
            """, (plant_id, session['user_id']))

            plant = mycursor.fetchone()
            print(f"Fetched plant details: {plant}")

            if plant:
                return render_template('editplant.html', plant=plant)
            else:
                flash("Plant not found", 'danger')
                return redirect(url_for('homepage'))
        except pymysql.Error as e:
            print(f"Database error during GET: {e}")
            flash(f"Database error: {e}", 'danger')
            return redirect(url_for('homepage'))
        finally:
            con.close()
            print("Database connection closed after GET request")




@app.route('/deleteplant/<int:plant_id>', methods=['POST'])
def deleteplant(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('login'))

    try:
        mycursor.execute("DELETE FROM plants WHERE id=%s AND user_id=%s", (plant_id, session['user_id']))
        con.commit()
        flash("Plant deleted successfully!", 'success')
        return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        if 'con' in locals():
            con.rollback()
    finally:
        con.close()

@app.route('/check_plant_health')
def planthealth():
    return render_template('planthealth.html')

@app.route('/plantadd')
def plantadd():
    return render_template('plantadd.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    password = request.form['password']
    

    if email == '' or password == '' :
        flash("All fields are required", 'danger')
        return redirect(url_for('signup'))

    if not re.match(r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$', email):
        flash("Enter a valid email", 'danger')
        return redirect(url_for('signup'))

    con, mycursor = connect_database()
    if not con:
        return redirect(url_for('signup'))
    
    try:
        mycursor.execute("CREATE DATABASE IF NOT EXISTS userdata")
        mycursor.execute("USE userdata")
        mycursor.execute("""
        CREATE TABLE IF NOT EXISTS credentials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(50),
            password VARCHAR(20),
            token VARCHAR(255)            
        )""")
        mycursor.execute("SELECT * FROM credentials WHERE email = %s", (email,))
        row = mycursor.fetchone()
        if row:
            flash("Account already exists! Please log in.", 'danger')
            return redirect(url_for('login'))

        # Insert email, password, and token into the database
        mycursor.execute("INSERT INTO credentials (email, password) VALUES (%s, %s)", (email, password))
        con.commit()
        flash("Registration was successful!", 'success')
        return redirect(url_for('login'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        if 'con' in locals():
            con.rollback()
    finally:
        con.close()

@app.route('/login', methods=['POST'])
def login_user():
    email = request.form.get('email')
    password = request.form.get('password')
    token = request.form.get('token')  # Retrieve the token from the form data
    print("Token to be used for notification:", token)

    if not email or not password:
        flash("All fields are required", 'danger')
        return redirect(url_for('login'))

    con, mycursor = connect_database()
    if not con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('login'))

    try:
        # Verify user credentials
        mycursor.execute("SELECT id FROM credentials WHERE email = %s AND password = %s", (email, password))
        user = mycursor.fetchone()
        if not user:
            flash("Invalid email or password", 'danger')
            return redirect(url_for('login'))

        # Update the token in the database
        user_id = user[0]  # Assuming 'id' is the first column
        mycursor.execute("UPDATE credentials SET token = %s WHERE id = %s", (token, user_id))
        con.commit()  # Commit the transaction

        # Store user details in session
        session['user_id'] = user_id
        session['token'] = token  # Store the user's Firebase token in the session

        flash("Login Successful!", 'success')
        return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
    finally:
        con.close()






@app.route('/add_plant', methods=['POST'])
def add_plant():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    # Get form data
    plant_name = request.form['plant_name']
    location = request.form['location']
    watering_frequency = request.form['watering_frequency']
    seed_cost = request.form['seed_cost']
    soil_cost = request.form['soil_cost']
    pot_cost = request.form['pot_cost']
    monthly_cost = request.form['monthly_cost']

    # Convert costs to float
    try:
        seed_cost = float(seed_cost)
        soil_cost = float(soil_cost)
        pot_cost = float(pot_cost)
        monthly_cost = float(monthly_cost)
    except ValueError:
        flash("Please enter valid numbers for the costs.", 'danger')
        return redirect(url_for('plantadd'))

    # Get the current date
    date_added = datetime.now().date()

    con, mycursor = connect_database()
    if not con:
        flash("Database connection failed", 'danger')
        return redirect(url_for('plantadd'))

    try:
        # Insert the new plant with the current date and cost details
        mycursor.execute("""
            INSERT INTO plants (plant_name, location, watering_frequency, seed_cost, soil_cost, pot_cost, monthly_cost, date_added, user_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (plant_name, location, watering_frequency, seed_cost, soil_cost, pot_cost, monthly_cost, date_added, session['user_id']))
        con.commit()
        flash("Plant added successfully!", 'success')
        return redirect(url_for('homepage'))
    except pymysql.Error as e:
        flash(f"Database error: {e}", 'danger')
        if 'con' in locals():
            con.rollback()
        return redirect(url_for('plantadd'))
    finally:
        con.close()





@app.route('/reset_timer/<int:plant_id>', methods=['POST'])
def reset_timer(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return jsonify({'status': 'error', 'message': 'You are not logged in!'}), 403

    con, mycursor = connect_database()
    if not con:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        # Update only the plant that belongs to the logged-in user
        mycursor.execute("UPDATE plants SET last_reset = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s", (plant_id, session['user_id']))
        con.commit()
        return jsonify({'status': 'success', 'message': 'Timer reset successfully'})
    except pymysql.Error as e:
        con.rollback()
        return jsonify({'status': 'error', 'message': f'Failed to reset timer: {e}'}), 500
    finally:
        con.close()


@app.route('/get_last_reset/<int:plant_id>', methods=['GET'])
def get_last_reset(plant_id):
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return jsonify({'status': 'error', 'message': 'You are not logged in!'}), 403

    con, mycursor = connect_database()
    if not con:
        return jsonify({'status': 'error', 'message': 'Database connection failed'}), 500

    try:
        mycursor.execute("SELECT last_reset FROM plants WHERE id = %s AND user_id = %s AND is_sold = FALSE", (plant_id, session['user_id']))
        last_reset = mycursor.fetchone()
        if last_reset:
            return jsonify({'status': 'success', 'last_reset': last_reset[0].strftime('%Y-%m-%d %H:%M:%S')})
        else:
            return jsonify({'status': 'error', 'message': 'Plant not found'}), 404
    except pymysql.Error as e:
        return jsonify({'status': 'error', 'message': 'Failed to fetch last reset time'}), 500
    finally:
        con.close()

@app.route('/search_plants', methods=['GET'])
def search_plants():
    if 'user_id' not in session:
        flash("You are not logged in!", 'danger')
        return redirect(url_for('login'))

    query = request.args.get('query', '')  # Get the search term from the query string
    con, mycursor = connect_database()
    if not con:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('homepage'))

    try:
        # Search for plants where the name or location matches the query and is owned by the logged-in user
        mycursor.execute("""
        SELECT * FROM plants 
        WHERE (plant_name LIKE %s OR location LIKE %s) AND user_id=%s AND is_sold = FALSE
        """, ('%' + query + '%', '%' + query + '%', session['user_id']))
        plants = mycursor.fetchall()
        return render_template('homepage.html', plants=plants)  # Render homepage with results
    except pymysql.Error as e:
        flash(f'Database error: {e}', 'danger')
        return redirect(url_for('homepage'))
    finally:
        con.close()


@app.route('/surprise')
def surprise():
    return render_template('surprise.html')






from datetime import datetime, timedelta

def check_and_notify():
    # Set up the database connection
    con = pymysql.connect(host='localhost',
                          user='root',
                          password='1234',
                          db='userdata',
                          charset='utf8mb4',
                          cursorclass=pymysql.cursors.DictCursor)  # Use DictCursor

    try:
        with con.cursor() as cursor:
            # Execute your query
            cursor.execute("""
                SELECT p.plant_name, p.location, p.watering_frequency, p.last_reset, c.token 
                FROM plants p 
                JOIN credentials c ON p.user_id = c.id
                WHERE p.is_sold = FALSE
            """)
            plants = cursor.fetchall()
            print("Fetched data type:", type(plants))

            # Process each plant
            for plant in plants:
                plant_name = plant['plant_name']
                location = plant['location']
                watering_frequency = plant['watering_frequency']  # Frequency now in minutes
                last_reset = plant['last_reset']  # This should be a datetime object
                token = str(plant['token'])  # Ensure token is treated as a string

                # Debugging the values
                print(f"\nProcessing plant: {plant_name}")
                print(f"Last reset: {last_reset}, Watering frequency (minutes): {watering_frequency}")

                # Check if last_reset is in the past
                if last_reset > datetime.now():
                    print(f"Error: last_reset {last_reset} is in the future!")
                    continue  # Skip plants with invalid last_reset

                # Calculate the next water time using minutes
                next_water_time = last_reset + timedelta(minutes=watering_frequency)
                print(f"Next water time: {next_water_time}, Current time: {datetime.now()}")

                # Check if it's time to water the plant
                if datetime.now() >= next_water_time:
                    print(f"Sending notification for plant: {plant_name}")
                    send_notification(token, plant_name, location)
                else:
                    print(f"Not time to water plant: {plant_name} yet. Next water time is in the future.")

    except Exception as e:
        print("Database error:", e)
    finally:
        if con:
            con.close()




scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="interval", minutes=1)  # Runs every hour
scheduler.start()


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




@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

@app.route('/firebase-messaging-sw.js')
def serve_firebase_sw():
    return send_from_directory(app.static_folder, 'firebase-messaging-sw.js')


@app.route('/checking_plant_health', methods=['GET', 'POST'])
def checking_plant_health():
    print('worjing1')
    model = tf.keras.models.load_model('trained_model_v2.h5')
    print('worjing2')
    
    if request.method == 'POST':
        file = request.files.get('file')  # Get the file from the request
        if file and file.filename != '':
            try:
                 file_stream = io.BytesIO(file.read())
                 file_stream.seek(0)  # Rewind to the beginning of the file stream

            # Load and preprocess the image using Keras
                 img = image.load_img(file_stream, target_size=(224, 224))
                 img_array = image.img_to_array(img)
                
            
            # Normalize using Keras specific to ResNet50V2
                 img_array = tf.keras.applications.resnet_v2.preprocess_input(img_array)

            # Create a batch of one (Keras models require batches)
                 img_array = np.expand_dims(img_array, axis=0)

            # Predict using the preloaded model
                 predictions = model.predict(img_array)
                 predicted_class = np.argmax(predictions)
                # Define your class_names somewhere in your module or script
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




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

    