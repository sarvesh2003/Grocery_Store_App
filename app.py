from flask import Flask, render_template, request, redirect, session
import sqlite3
import re
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
valid_user  = False
valid_admin = False
category_list = []
@app.route('/', methods=['GET', 'POST'])
def user_login():
    # Getting the contents from user to validate
    if request.method == 'POST':
        user_username = str(request.form['uname'])
        user_password = str(request.form['pass'])
        connection = sqlite3.connect('user_login.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        flag = False
        if rows:
         for row in rows:
            if(user_username == row[0] and user_password == row[1]):
               flag = True
        connection.close()
        if(flag == True):
           session['username'] = user_username
           valid_user = True # This user can access further contents
           return redirect('/user_dashboard')
        else:
           return redirect('/user_login_failure')
        # Logic to check the entered values with the values in db
    return render_template('user_login_page.html')

@app.route('/user_register', methods=['GET', 'POST'])
def user_registration():
   # Add username and password into the database
    # Adding the user content to list
    if request.method == 'POST':
        print(request.form['uname'])
        user_username = str(request.form['uname'])
        user_password = str(request.form['pass'])
        validation_flag = False # True - not as per format
        ##### Validation #####
        if(len(user_username) < 8 or len(user_password) < 8):
           validation_flag = True
         
        # Check if the username contains only letters, numbers, or underscores
        if(re.match(r'^\w+$', user_username) is None):
           validation_flag = True
        
        # Check if the password contains at least one uppercase letter, one lowercase letter, and one digit
        if(re.search(r'[A-Z]', user_password) and re.search(r'[a-z]', user_password) and re.search(r'\d', user_password) is None):
           validation_flag = True
        
        if(validation_flag == True):
           print("Follow the format")
           return render_template('user_registration.html')        
        # Check if username already exists #
        connection = sqlite3.connect('user_login.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        flag = False
        if rows:
         for row in rows:
            if(user_username == row[0]):
               flag = True
        connection.close()
        ##
        if(flag):
           print("Username already exists")
         #   flash("Username already exists")
         #   return redirect('/user_register')
           return render_template('username_present_already.html')
        if(not flag):
            # do this when username is not present in the database
            connection = sqlite3.connect('user_login.db')
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users VALUES (?,?)", (user_username, user_password, ))
            connection.commit()
            connection.close()
        return redirect('/')
    return render_template('user_registration.html')

@app.route('/user_logout')
def logout():
    session.clear()
    return redirect('/') # Go to user login page

@app.route('/user_login_failure')
def failure_msg():
   return render_template('failure_msg.html')

@app.route('/cart_checkout', methods=['GET', 'POST'])
def cart_checkout():
   # Update the product_data data as user got some items
   connection = sqlite3.connect('cart_info.db')
   cursor = connection.cursor()
   user_name = session.get('username')
   cursor.execute("SELECT * FROM cart WHERE username=?", (user_name,))
   product = cursor.fetchall() # take product ids from this and then open the product_data database to change the amount
   # p[1] -> product_id, p[2] -> amount
   connection.commit()
   connection.close()
   connection2 = sqlite3.connect('product_data.db')
   cursor2 = connection2.cursor()
   for p in product:
      cursor2.execute("SELECT amount FROM products WHERE id=?", (p[1],))
      print(p)
      current_amount = cursor2.fetchone()
      if current_amount:
         # Calculate the new amount after subtracting p[4]
         new_amount = current_amount[0] - int(p[2])
         if(new_amount < 0):
            print("Not allowed to buy this much products for {}".format(p[1]))
            name = p[1]
            amount = current_amount[0]
            return render_template('/amount_of_goods_negative.html', name=name, amount=amount)
         # Update the product_data.db with the new amount
         cursor2.execute("UPDATE products SET amount=? WHERE id=?", (new_amount, p[1],))
         print("sucessfully updated")
      else:
         print(f"Product {p[1]} not found in the product_data.db.")
   connection2.commit()
   connection2.close()
   # Remove the contents from the cart_info database
   connection = sqlite3.connect('cart_info.db')
   cursor = connection.cursor()
   user_name = session.get('username')
   cursor.execute("DELETE FROM cart WHERE username=?", (user_name,))
   connection.commit()
   connection.close()
   return render_template("cart_checkout.html")

@app.route('/user_profile')
def user_profile():
   user_name = session.get('username')
   return render_template("user_profile.html", user_name=user_name)

@app.route('/user_dashboard')
def user_dashboard():
  
   categories = {}
   connection = sqlite3.connect('product_data.db')
   cursor = connection.cursor()
   cursor.execute("SELECT * FROM products")
   rows = cursor.fetchall()
   if rows:
      for row in rows:
         category = row[2]
         if category not in categories:
            categories[category] = []
         categories[category].append(row)
   return render_template("user_after_login.html", categories=categories)

@app.route('/user_searched_item', methods=['GET', 'POST'])
def user_searched_item():
   # Only searched items
   categories = {}
   print(request.method)
   if request.method == 'POST':
      print("Inside user_searched_item")
      searched_item = str(request.form['psearch'])
      connection = sqlite3.connect('product_data.db')
      cursor = connection.cursor()
      cursor.execute("SELECT * FROM products")
      rows = cursor.fetchall()
      # Determine whether it is category or product
      searched_category = False # list of all categories
      searched_product = False # list of all products
      print("Hello")
      if rows:
         for row in rows:
            if searched_item.lower() == str(row[2]).lower():
               
               print(str(row[2]).lower() == searched_item.lower())
               searched_category = True
               break
            elif searched_item.lower() == str(row[1]).lower():
               searched_product = True
               break
      # Send only that part for displaying
      if searched_category:
         print("It is a category")
         if rows:
            for row in rows:
               # display that category and products in that category
               if searched_item.lower() == str(row[2]).lower():
                  category = row[2]
                  if category not in categories:
                     categories[category] = []
                  categories[category].append(row)
         
      elif searched_product:
         print("It is a product")
         if rows:
            for row in rows:
               # display that particular product with category
               if searched_item.lower() == str(row[1]).lower():
                  category = row[2]
                  if category not in categories:
                     categories[category] = []
                  categories[category].append(row)
                  break
      # if rows:
      #    for row in rows:
      #       category = row[2]
      #       if category not in categories:
      #          categories[category] = []
      #       categories[category].append(row)
   return render_template("user_after_login.html", categories=categories)

count = 0
@app.route('/user_buy_products/<int:product_id>', methods=['GET', 'POST'])
def user_buy_products(product_id):
    # Check the database for price per unit
    connection = sqlite3.connect('product_data.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    product_title = product[1]
    per_value = int(product[3])
    user_name = session.get('username')
    quantity = 0
    if request.method == 'POST':
         count = count + 1
         quantity = int(request.form['quantity'])
         print(count)
         total = quantity * product[3]
         connection.close()
         # total = quantity * 2
    else:
        total = 0
    return render_template('user_buy_products.html', total=total, product_id=product_id, per_value = per_value, product_title=product_title, user_name=user_name)

@app.route('/add_cart_info_to_db/<int:product_id>', methods=['GET','POST'])
def add_cart_info_to_db(product_id):
   if request.method == 'POST':
      quantity = str(request.form['quantity'])
      connection2 = sqlite3.connect('product_data.db')
      cursor2 = connection2.cursor()
      cursor2.execute("SELECT amount FROM products WHERE id=?", (product_id,))
      available_quantity = int(cursor2.fetchone()[0])
   
      # Add in cart_info database
      user_name = session.get('username')
      connection = sqlite3.connect('cart_info.db')
      cursor = connection.cursor()
      # Check if the user bought the product already - yes -> update there
      cursor.execute("SELECT * FROM cart WHERE username=? and product_id=?", (user_name, product_id,))
      product = cursor.fetchone()
      new_quantity = 0
      if product:
            print(product[0])
            new_quantity = product[2]
            cursor.execute("UPDATE cart SET quantity=? where product_id=?", (int(new_quantity)+int(quantity), product_id,))
      else:
         cursor.execute("INSERT INTO cart VALUES (?,?,?)", (user_name, product_id, quantity,))
      connection.commit()
      connection.close()
      print("Successfully inserted into database")
   return render_template('add_cart_db.html')


@app.route('/cart_view')
def cart_view():
   # Show the contents of the cart
   connection = sqlite3.connect('cart_info.db')
   cursor = connection.cursor()
   user_name = session.get('username')
   cursor.execute("SELECT * FROM cart WHERE username=?", (user_name,))
   product = cursor.fetchall()
   connection.commit()
   connection.close()
   # Grand Total calculation
   grand_total = 0
   if product:
      for p in product:
         print("Pid:", p[1]) # pid
         print("Quantity:", p[2]) # quanitity
         connection2 = sqlite3.connect('product_data.db')
         cursor2 = connection2.cursor()
         cursor2.execute("SELECT price_per_unit FROM products WHERE id=?", (p[1],))
         product2 = cursor2.fetchone()
         grand_total = grand_total + int(product2[0])*int(p[2])
         print("Grand total:" , grand_total)
         connection2.commit()
         connection2.close()

   return render_template('cart.html', product=product, user_name=user_name, grand_total=grand_total)

@app.route('/delete_from_cart/<int:product_id>')
def delete_from_cart(product_id):
   connection = sqlite3.connect('cart_info.db')
   cursor = connection.cursor()
   user_name = session.get('username')
   cursor.execute("DELETE FROM cart WHERE username=? and product_id=?", (user_name,product_id,))
   connection.commit()
   connection.close()
   print("deleted sucessfully")
   return redirect("/user_dashboard")

@app.route('/edit_quantity/<int:product_id>', methods=['GET','POST'])
def edit_quantity(product_id):
   if request.method == 'POST':
      new_quantity = str(request.form['new_quantity'])
      connection = sqlite3.connect('cart_info.db')
      cursor = connection.cursor()
      user_name = session.get('username')
      cursor.execute("UPDATE cart SET quantity=? where username=? and product_id=?", (new_quantity, user_name,product_id,))
      connection.commit()
      connection.close()
      return redirect("/cart_view")
   print("Edited quantity sucessfully")
   return render_template("/cart_quantity_edit.html", product_id=product_id)

@app.route('/admin_profile')
def admin_profile():
   user_name = session.get('username')
   return render_template("admin_profile.html", user_name=user_name)


@app.route('/admin_logout')
def admin_logout():
    session.clear()
    return redirect('/admin_login') # Go to admin login page

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    # Getting the contents from user to validate
    if request.method == 'POST':
        admin_username = str(request.form['uname'])
        admin_password = str(request.form['pass'])
        connection = sqlite3.connect('admin_login.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM admin")
        rows = cursor.fetchall()
        flag = False
        if rows:
         for row in rows:
            if(admin_username == row[0] and admin_password == row[1]):
               flag = True
        connection.close()
        if(flag == True):
           session['username'] = admin_username
           valid_admin = True # Can access further contents
           return redirect('/admin_dashboard')
        else:
           return redirect('/admin_login_failure')
        # Logic to check the entered values with the values in db
    return render_template('admin_login_page.html')

# @app.route('/admin_login_success')
# def admin_success_msg():
#    return render_template("admin_success_msg.html")

@app.route('/admin_login_failure')
def admin_failure_msg():
   return render_template("admin_failure_msg.html")

@app.route('/admin_dashboard')
def admin_dashboard():
   # Render categories to show
   categories = {}
   connection = sqlite3.connect('product_data.db')
   cursor = connection.cursor()
   cursor.execute("SELECT * FROM products")
   rows = cursor.fetchall()
   if rows:
      for row in rows:
         category = row[2]
         print("Loop : ", category)
         if category not in categories:
            categories[category] = []
         categories[category].append(row)
   # category_list1 from categories db
   # category_list - global variable
   connection = sqlite3.connect('category_list.db')
   cursor = connection.cursor()
   cursor.execute("SELECT * FROM categories")
   product = cursor.fetchall()
   category_list1 = []
   for p in product:
      print("In DB: ", p[0])
      category_list1.append(p[0])
   connection.close()

   for i in category_list1:
      if i not in categories:
         category = i
         categories[category] = []
   return render_template('admin_after_login.html', categories=categories)

@app.route('/delete_category/<string:cat_name>', methods=['POST'])
def delete_category(cat_name):
   # If products are present in that category, dont delete
   # ----- Checking -----
   connection = sqlite3.connect('product_data.db')
   cursor = connection.cursor()
   cursor.execute("SELECT Category from products where Category=?", (cat_name, ))
   product_list = cursor.fetchall()
   can_i_delete = True
   if(len(product_list) > 0):
      print("You have many products in this category. so can't delete that")
      can_i_delete = False
   connection.commit()
   connection.close()
   if(can_i_delete):
      connection = sqlite3.connect('category_list.db')
      cursor = connection.cursor()
      cursor.execute("DELETE FROM categories where category=?", (cat_name,))
      connection.commit()
      print("Deleted category")
      connection.close()
   return redirect('/admin_dashboard')

@app.route('/edit_category/<string:cat_name>', methods=['GET', 'POST'])
def edit_category(cat_name):
   if request.method == 'POST':
      new_name = str(request.form['new_name'])
      # Update in category list
      connection = sqlite3.connect('category_list.db')
      cursor = connection.cursor()
      cursor.execute("UPDATE categories SET category=? WHERE category=?", (new_name, cat_name))
      connection.commit()
      connection.close()
      # Update in products_data also as it contains the category column
      connection = sqlite3.connect('product_data.db')
      cursor = connection.cursor()
      cursor.execute("UPDATE products SET Category=? WHERE Category=?", (new_name, cat_name))
      connection.commit()
      connection.close()
      return redirect('/admin_dashboard')

   return render_template('edit_category.html', cat_name=cat_name)

@app.route('/admin_add_new_products',  methods=['GET', 'POST'])
def admin_p_add():
   # Adding the contents which we got from the form
   if request.method == 'POST':
        product_name = str(request.form['pname'])
        product_category = str(request.form['cat'])
        if product_category == '':
           print("Enter Category - It is must")
           return redirect('/admin_dashboard')
        product_price_per_unit = int(request.form['ppu'])
        product_avail = str(request.form['amount'])
        product_img = str(request.form['imlink'])
        product_id = str(request.form['pid'])
        product_man = str(request.form['mdate'])
        product_exp = str(request.form['exdate'])
        # Add in products db
        connection = sqlite3.connect('product_data.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO products VALUES (?,?, ?, ?, ?, ?, ?, ?)", (product_id, product_name, product_category, product_price_per_unit, product_avail, product_img, product_man, product_exp))
        connection.commit()
        connection.close()
        print("ADDED IN PRODUCTS TABLE")
        # Add the category in the category_list (check and then add)
        connection = sqlite3.connect('category_list.db')
        cursor = connection.cursor()
        cursor.execute("SELECT * from categories")
        product = cursor.fetchall()
        should_i_insert = True
        for p in product:
           if(product_category == p[0]):
              should_i_insert = False
              break
        if(should_i_insert):
         cursor.execute("INSERT INTO categories VALUES (?)", (product_category,))
         print("ADDED IN CATEGORIES TABLE")
        else:
           print("ALREADY CATEGORY PRESENT")
        connection.commit()
        connection.close()
        return redirect('/admin_dashboard')
   return render_template('admin_add_new_products.html')

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    connection = sqlite3.connect('product_data.db')
    cursor = connection.cursor()
    # If this is the only product in a particular category, delete the category from the category_list db
    cursor.execute("SELECT Category from products where id=?", (product_id,))
    product = cursor.fetchall()
    new_product = cursor.fetchall()
    for p in product:
       # will be executed only once
       cursor.execute("SELECT * from products where category=?", (p[0],))
       new_product = cursor.fetchall()
    len_of_product = 0
    for p in new_product:
       len_of_product += 1
    print(len_of_product)
    if(len_of_product == 1):
       # delete this category from category_list db
       for p in product:
          print("Going to delete {} from category_list".format(p[0]))
          connection2 = sqlite3.connect('category_list.db')
          cursor2 = connection2.cursor()
          cursor2.execute('DELETE FROM categories where Category=?', (p[0],))
          connection2.commit()
          connection2.close()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    connection.commit()
    connection.close()
    print("Deleted Product sucessfully")
    return redirect('/admin_dashboard')

@app.route('/edit_product/<int:product_id>', methods=['GET','POST'])
def edit_product(product_id):
   # First fetch the record
   connection = sqlite3.connect('product_data.db')
   cursor = connection.cursor()
   cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
   product = cursor.fetchone()
   connection.close()
   print(product)
   if request.method == 'POST':
      # Variables from form
      product_name_new = str(request.form['prname'])
      product_category_new = str(request.form['cat'])
      if request.form['ppu'] == '':
         product_price_per_unit_new = -1
      if request.form['ppu'] != '':
         product_price_per_unit_new = int(request.form['ppu'])
      product_avail_new = str(request.form['amount'])
      product_img_new = str(request.form['imlink'])
      product_id_new = str(request.form['pid'])
      product_man_new = str(request.form['mdate'])
      product_exp_new = str(request.form['exdate'])
      # Considering only the values provided by admin and not blank values
      if len(product_name_new)==0:
         product_name_new = product[1]
      if len(product_category_new)==0:
         product_category_new = product[2]
      if product_price_per_unit_new == -1:
         product_price_per_unit_new = product[3]
      if len(product_avail_new)==0:
         product_avail_new = product[4]
      if len(product_img_new)==0:
         product_img_new = product[5]
      if len(product_id_new)==0:
         product_id_new = product[0]
      if len(product_man_new)==0:
         product_man_new = product[6]
      if len(product_exp_new)==0:
         product_exp_new = product[7]
      print(product_name_new, product_category_new, product_price_per_unit_new, product_avail_new, product_img_new, product_man_new, product_exp_new, product_id_new)
      connection = sqlite3.connect('product_data.db')
      cursor = connection.cursor()
      cursor.execute("UPDATE products SET Name=? , Category=? , price_per_unit=? , amount=? , img_link=? , man=? , exp=? WHERE ID=?", (product_name_new, product_category_new, product_price_per_unit_new, product_avail_new, product_img_new, product_man_new, product_exp_new,product_id_new, ))
      connection.commit()
      connection.close()
      print("Edited")
      return redirect('/admin_dashboard')
   return render_template('/edit_product.html'.format(product_id), product=product, product_id=product_id)

@app.route('/admin_add_new_category', methods=['GET', 'POST'])
def admin_add_new_category():
   if request.method == 'POST':
      category_name = str(request.form['cname'])
      if category_name != "":
         # Add in category_list db
         connection = sqlite3.connect('category_list.db')
         cursor = connection.cursor()
         cursor.execute("INSERT INTO categories VALUES (?)", (category_name, ))
         connection.commit()
         connection.close()
         category_list.append(category_name)
      return redirect('/admin_dashboard')
   return render_template('admin_add_new_category.html')

@app.route('/admin_searched_item', methods=['GET', 'POST'])
def admin_searched_item():
   # Only searched items
   categories = {}
   print(request.method)
   if request.method == 'POST':
      print("Inside admin_searched_item")
      searched_item = str(request.form['asearch'])
      connection = sqlite3.connect('product_data.db')
      cursor = connection.cursor()
      cursor.execute("SELECT * FROM products")
      rows = cursor.fetchall()
      # Determine whether it is category or product
      searched_category = False # list of all categories
      searched_product = False # list of all products
      print("Hello")
      if rows:
         for row in rows:
            if searched_item.lower() == str(row[2]).lower():
               
               print(str(row[2]).lower() == searched_item.lower())
               searched_category = True
               break
            elif searched_item.lower() == str(row[1]).lower():
               searched_product = True
               break
      # Send only that part for displaying
      if searched_category:
         print("It is a category")
         if rows:
            for row in rows:
               # display that category and products in that category
               if searched_item.lower() == str(row[2]).lower():
                  category = row[2]
                  if category not in categories:
                     categories[category] = []
                  categories[category].append(row)
         
      elif searched_product:
         print("It is a product")
         if rows:
            for row in rows:
               # display that particular product with category
               if searched_item.lower() == str(row[1]).lower():
                  category = row[2]
                  if category not in categories:
                     categories[category] = []
                  categories[category].append(row)
                  break
   return render_template("admin_after_login.html", categories=categories)

if __name__=="__main__":
    app.run(debug=True)