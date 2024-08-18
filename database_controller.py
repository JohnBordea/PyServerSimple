from datetime import datetime

import mysql.connector
import bcrypt
import secrets

RED = "\033[91m"
RESET = "\033[0m"

PORT = 8080
# CCI = Customer Confidence Index
class DatabaseCCI:
    @staticmethod
    def get_cursor_and_cnx():
        cnx = mysql.connector.connect(user='proiectTW', password='proiectTW',
                              host='localhost',database='proiecttw')
        return (cnx.cursor(), cnx)

    @staticmethod
    def create_CCI_table():
        cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

        create_table_query = """
            CREATE TABLE cci (
                id INT AUTO_INCREMENT PRIMARY KEY,
                country_name VARCHAR(100),
                date DATE,
                index_value FLOAT
            )
        """

        try:
            # Execute the CREATE TABLE query
            cursor.execute(create_table_query)
            print("Table created successfully.")
        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def delete_CCI_table():
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            delete_table_query = "DROP TABLE IF EXISTS cci"
            cursor.execute(delete_table_query)
            cnx.commit()
            print("Table deleted successfully.")
            return True
        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def get_country_names():
        cursor, cnx = DatabaseCCI.get_cursor_and_cnx()
        query = "SELECT DISTINCT country_name FROM cci"
        cursor.execute(query)
        rows = cursor.fetchall()
        countries = []
        for row in rows:
            countries.append(row[0])
        cursor.close()
        cnx.close()
        return countries

    @staticmethod
    def get_years():
        cursor, cnx = DatabaseCCI.get_cursor_and_cnx()
        #query = "SELECT DISTINCT YEAR(date) AS distinct_years FROM cci ORDER BY distinct_years ASC;"
        query = "SELECT country_name, MIN(YEAR(date)) AS earliest_year, MAX(YEAR(date)) AS latest_year FROM cci GROUP BY country_name"
        cursor.execute(query)
        rows = cursor.fetchall()
        data = {}
        for row in rows:
            data[row[0]] = [row[1], row[2]]
        cursor.close()
        cnx.close()
        return data

    @staticmethod
    def get_data_from_id(id):
        cursor, cnx = DatabaseCCI.get_cursor_and_cnx()
        #query = "SELECT DISTINCT YEAR(date) AS distinct_years FROM cci ORDER BY distinct_years ASC;"
        query = "SELECT * FROM cci WHERE id=%s"
        values = (id,)
        cursor.execute(query, values)
        row = cursor.fetchone()
        data = {}
        if row:
            data = {
                "id":           row[0],
                "country_name": row[1],
                "date":         datetime.strftime(row[2], '%Y-%m-%d'),
                "index":        row[3]
            }
        cursor.close()
        cnx.close()
        return data

    @staticmethod
    def get_countries(countries, start_date=None, end_date=None):
        country_dict = {}

        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            # Build the SELECT query
            select_query = "SELECT * FROM cci WHERE country_name IN ("
            select_query += ",".join(["%s"] * len(countries)) + ")"
            select_values = tuple(countries)

            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            if start_date is not None and end_date is not None:
                select_query += " AND DATE_FORMAT(date, '%Y-%m') BETWEEN %s AND %s"
                select_values += (start_date, end_date)
            elif start_date is not None:
                select_query += " AND DATE_FORMAT(date, '%Y-%m') >= %s"
                select_values += (start_date,)
            elif end_date is not None:
                select_query += " AND DATE_FORMAT(date, '%Y-%m') <= %s"
                select_values += (end_date,)

            cursor.execute(select_query, select_values)
            rows = cursor.fetchall()

            # Process the rows and extract the required data
            for row in rows:
                date = datetime.strftime(row[2], '%Y-%m-%d')
                country_name = row[1]
                index_value = row[3]

                # create a dictionary with dates as keys
                # each date key maps to another dictionary where the country_name keys are unique, and their corresponding values are the index_value.
                if date not in country_dict:
                    country_dict[date] = {}

                country_dict[date][country_name] = index_value

        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
        finally:
            cursor.close()
            cnx.close()

        # Convert the dictionary to the desired list format
        country_list = [
            {"date": date, **values}
            for date, values in country_dict.items()
        ]
        return country_list

    @staticmethod
    def get_all_countries(start_date=None, end_date=None):
        country_dict = {}

        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            # Build the SELECT query
            select_query = "SELECT * FROM cci"
            select_values = ()
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            if start_date is not None and end_date is not None:
                select_query += " WHERE DATE_FORMAT(date, '%Y-%m') BETWEEN %s AND %s"
                select_values = (start_date, end_date)
            elif start_date is not None:
                select_query += " WHERE DATE_FORMAT(date, '%Y-%m') >= %s"
                select_values = (start_date,)
            elif end_date is not None:
                select_query += " WHERE DATE_FORMAT(date, '%Y-%m') <= %s"
                select_values = (end_date,)

            cursor.execute(select_query, select_values)
            rows = cursor.fetchall()

            # Process the rows and extract the required data
            for row in rows:
                date = datetime.strftime(row[2], '%Y-%m-%d')
                country_name = row[1]
                index_value = row[3]

                # create a dictionary with dates as keys
                # each date key maps to another dictionary where the country_name keys are unique, and their corresponding values are the index_value.
                if date not in country_dict:
                    country_dict[date] = {}

                country_dict[date][country_name] = index_value
            cursor.close()
            cnx.close()

        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")

        # Convert the dictionary to the desired list format
        country_list = [
            {"date": date, **values}
            for date, values in country_dict.items()
        ]

        return country_list

    @staticmethod
    def get_country_year(country, year):

        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            data = []
            sql = "SELECT * FROM cci WHERE country_name = '" + country + "'"
            #SELECT MIN(YEAR(`date`)) AS earliest_year, MAX(YEAR(`date`)) AS latest_year FROM `cci` WHERE `country_name` = 'NLD';
            cursor.execute(sql)

            rows = cursor.fetchall()

            for row in rows:
                if row[2].year == year:
                    data.append({
                        "id":    row[0],
                        "date":  datetime.strftime(row[2], '%Y-%m-%d'),
                        "index": row[3]
                    })
                    data.sort(key=lambda e: e['date'])

        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            data = []
        finally:
            cursor.close()
            cnx.close()

        return data

    @staticmethod
    def check_country_date(country, date, index):

        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            sql = "SELECT * FROM cci WHERE country_name = %s and date = %s"
            values = (country, date)
            cursor.execute(sql, values)

            row = cursor.fetchone()
            if row is not None:
                response = False
                print("Not added")
            else:
                response = True
                DatabaseCCI.create_country_index(country, date, index, cursor, cnx)
                print("added")

        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            response = True
        finally:
            cursor.close()
            cnx.close()

        return response

    @staticmethod
    def update_country_index(country_name, date, index):
        formatted_date = datetime.strptime(date.replace('"', ""), "%Y-%m")

        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            select_query = "SELECT id FROM cci WHERE country_name = %s AND date = %s"
            cursor.execute(select_query, (country_name, formatted_date))
            row = cursor.fetchone()

            if row is None:
                print(f'No entry was found for country_name="{country_name}" and date="{datetime.strftime(formatted_date, "%Y-%m")}"')
                return False

            entry_id = row[0]

            update_query = "UPDATE cci SET index_value = %s WHERE id = %s"
            cursor.execute(update_query, (index, entry_id))
            cnx.commit()

            return True

        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def update_country_index_by_id(id, index):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            update_query = "UPDATE cci SET index_value = %s WHERE id = %s"
            cursor.execute(update_query, (index, id))
            cnx.commit()

            return True

        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def create_country_index(country_name, date, index, cursor, cnx):
        # print(date)
        # formatted_date = datetime.strptime(date, '"%Y-%m"')
        try:
            #cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            insert_query = "INSERT INTO cci (country_name, date, index_value) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (country_name, date, index))
            cnx.commit()
            # print("Index value created successfully.")
            result = True
        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            result =  False
        #finally:
        #    cursor.close()
        #    cnx.close()

        return result

    @staticmethod
    def delete_country_index(country_name, date):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            delete_query = "DELETE FROM cci WHERE country_name = %s AND date = %s"
            cursor.execute(delete_query, (country_name, date))

            cnx.commit()
            # print("Index value deleted successfully.")
            return True
        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def load_country_index_from_csv(csv_file, start_page=0):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            with open(csv_file, 'r') as file:
                # read the first line (with titles)
                file.readline()

                for line in file:
                    values = line.split(',')
                    country_name = values[0].replace('"', "")
                    date = datetime.strptime(values[5].replace('"', ""), "%Y-%m")
                    index = float(values[6])
                    DatabaseCCI.create_country_index(country_name, date, index, cursor, cnx)

            print("Country index values loaded successfully from CSV.")
            return True
        except IOError as e:
            print(f"{RED}Error:{RESET} {e}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def get_download_file_as_csv(countries=None, start_date=None, end_date=None):

        try:
            cnx = mysql.connector.connect(user='proiectTW', password='proiectTW',
                              host='localhost', database='proiecttw')
            cursor = cnx.cursor()

            # Build the SELECT query
            select_query = "SELECT country_name, date, index_value FROM cci"
            select_values = None
            if countries:
                select_query += " WHERE country_name IN ("
                select_query += ",".join(["%s"] * len(countries)) + ")"
                select_values = tuple(countries)

            if start_date is not None and end_date is not None:
                if countries:
                    select_query += " AND"
                else:
                    select_query += " WHERE"
                select_query += " DATE_FORMAT(date, '%Y-%m') BETWEEN %s AND %s"
                if select_values:
                    select_values += (start_date, end_date)
                else:
                    select_values = (start_date, end_date)
            elif start_date is not None:
                if countries:
                    select_query += " AND"
                else:
                    select_query += " WHERE"
                select_query += " DATE_FORMAT(date, '%Y-%m') >= %s"
                if select_values:
                    select_values += (start_date,)
                else:
                    select_values = (start_date,)
            elif end_date is not None:
                if countries:
                    select_query += " AND"
                else:
                    select_query += " WHERE"
                select_query += " DATE_FORMAT(date, '%Y-%m') <= %s"
                if select_values:
                    select_values += (end_date,)
                else:
                    select_values = (end_date,)

            print(select_query)
            print(select_values)
            cursor.execute(select_query, select_values)
            rows = cursor.fetchall()

            csvfile = []

            csvfile.append(['country', 'date', 'value'])
            for row in rows:
                modified_row = list(row)  # Convert the tuple to a list for modification
                modified_row[1] = datetime.strftime(row[1], '%Y-%m')  # Modify the second element (index 1)
                # csv_row = ','.join(str(value) for value in modified_row)
                csvfile.append(modified_row)

            return csvfile

        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
        finally:
            cursor.close()
            cnx.close()

class DatabaseUser:
    @staticmethod
    def get_cursor_and_cnx():
        cnx = mysql.connector.connect(user='proiectTW', password='proiectTW',
                              host='localhost',database='proiecttw')
        return (cnx.cursor(), cnx)

    @staticmethod
    def create_user_table():
        try:
            cursor, cnx = DatabaseUser.get_cursor_and_cnx()

            cursor.execute('''CREATE TABLE IF NOT EXISTS user (
                            id INT(11) AUTO_INCREMENT PRIMARY KEY NOT NULL,
                            firstname VARCHAR(100) NOT NULL,
                            lastname VARCHAR(100) NOT NULL,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password VARCHAR(255) NOT NULL,
                            role enum("admin", "user") NOT NULL,
                            date_time date NOT NULL
                            )''')

            cnx.commit()  # Save the changes
            print("User table created successfully!")

        except mysql.connector.Error as err:
            print(f"{RED}Error creating table:{RESET} {err}")
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def delete_user_table():
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            cursor.execute('''DROP TABLE IF EXISTS user''')

            cnx.commit()  # Save the changes
            print("User table deleted successfully!")

        except mysql.connector.Error as err:
            print(f"{RED}Error deleting table:{RESET} {err}")
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def create_new_user(firstname, lastname, username, email, password):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            # Check if the username already exists in the table
            user = DatabaseUser.get_user_info(username=username)
            if user:
                print(f"Error creating new user: The username '{username}' already exists.")
                return {
                    "message": False,
                    "error": "user"
                }
            user = DatabaseUser.get_user_info(email=email)
            if user:
                print(f"Error creating new user: The email '{email}' already exists.")
                return {
                    "message": False,
                    "error": "email"
                }
            print(f'Create user function -> username={username} email={email} password={password}')
            # Insert the new user into the user table
            sql = "INSERT INTO user (firstname, lastname, username, email, password, role, date_time) VALUES (%s, %s, %s, %s, %s, 'user', now())"
            values = (firstname, lastname, username, email, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10)))
            cursor.execute(sql, values)

            cnx.commit()  # Save the changes
            print("New user created successfully!")

            user = DatabaseUser.get_user_info(username=username)
            return {
                    "message": True,
                    "data": user
                }

        except mysql.connector.Error as err:
            print(f"{RED}Error creating new user:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def delete_user(username):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            # Delete the user from the user table
            sql = "DELETE FROM user WHERE username = %s"
            value = (username,)
            cursor.execute(sql, value)

            cnx.commit()  # Save the changes
            print("User deleted successfully!")

        except mysql.connector.Error as err:
            print(f"{RED}Error{RESET} deleting user: {err}")
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def is_user_present(username, password):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            sql = "SELECT * FROM user WHERE (username = %s or email = %s)"
            value = (username, username)
            cursor.execute(sql, value)

            user_data = cursor.fetchone()

            if user_data:
                hashed_password = user_data[5]
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    user_info = {
                        "id":        user_data[0],
                        "firstname": user_data[1],
                        "lastname":  user_data[2],
                        "username":  user_data[3],
                        "email":     user_data[4],
                        "role":      user_data[6]
                    }
                else:
                    raise ValueError()
            else:
                print(f"No user found with the credentials '{username}'.")
                raise ValueError()

        except mysql.connector.Error as err:
            print(f"{RED}Error retrieving user information:{RESET} {err}")
            return False
        except ValueError as err:
            user_info = False
        finally:
            cursor.close()
            cnx.close()

        return user_info

    @staticmethod
    def get_user_info(id=None, username = None, email = None):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            if id:
                sql = "SELECT * FROM user WHERE id = %s"
                value = (id,)
            elif username:
                sql = "SELECT * FROM user WHERE username = %s"
                value = (username,)
            elif email:
                sql = "SELECT * FROM user WHERE email = %s"
                value = (email,)
            else:
                raise ValueError()
            cursor.execute(sql, value)

            user_data = cursor.fetchone()

            if user_data:
                user_info = {
                    "id":        user_data[0],
                    "firstname": user_data[1],
                    "lastname":  user_data[2],
                    "username":  user_data[3],
                    "email":     user_data[4],
                    "role":      user_data[6]
                }
            else:
                print(f"No user found with the credentials '{username}'.")
                raise ValueError()

        except mysql.connector.Error as err:
            print(f"{RED}Error retrieving user information:{RESET} {err}")
            user_info = False
        except ValueError as err:
            user_info = False
        finally:
            cursor.close()
            cnx.close()

        return user_info

    @staticmethod
    def get_all_user_info():
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            sql = "SELECT * FROM user"
            cursor.execute(sql)

            data = cursor.fetchall()
            users_data = []

            for element in data:
                users_data.append({
                    "id":        element[0],
                    "firstname": element[1],
                    "lastname":  element[2],
                    "username":  element[3],
                    "email":     element[4],
                    "role":      element[6]
                })

        except mysql.connector.Error as err:
            print(f"{RED}Error retrieving user information:{RESET} {err}")
            users_data = False
        except ValueError as err:
            users_data = False
        finally:
            cursor.close()
            cnx.close()

        return users_data

    @staticmethod
    def update_user_info(id, new_firstname=None, new_lastname=None, new_username=None, new_email=None, new_password=None):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            if id==None:
                raise ValueError()

            #check if username or password is in database
            if new_username:
                user = DatabaseUser.get_user_info(username=new_username)
                if user:
                    if id != user['id']:
                        raise ValueError()
            if new_email:
                user = DatabaseUser.get_user_info(email=new_email)
                if user:
                    if id != user['id']:
                        raise ValueError()

            # Prepare the update query based on the provided fields
            sql = "UPDATE user SET"
            values = []

            if new_firstname is not None:
                sql += " firstname = %s,"
                values.append(new_firstname)
            if new_lastname is not None:
                sql += " lastname = %s,"
                values.append(new_lastname)
            if new_username is not None:
                sql += " username = %s,"
                values.append(new_username)
            if new_email is not None:
                sql += " email = %s,"
                values.append(new_email)

            sql = sql.rstrip(",")

            # Add the WHERE clause to update the specific user
            sql += " WHERE id = %s"
            values.append(id)

            cursor.execute(sql, values)

            cnx.commit()  # Save the changes
            print("User information updated successfully!")
            result = True
        except mysql.connector.Error as err:
            print(f"{RED}Error updating user information: {err}{RESET}")
            result = False
        except ValueError as err:
            result = False
        finally:
            cursor.close()
            cnx.close()
        return result

    @staticmethod
    def update_user_admin(id=None, username=None, role=True):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            if id == None and username == None:
                raise ValueError()

            sql = "UPDATE user SET role = %s WHERE"
            values = []
            if role:
                values.append('admin')
            else:
                values.append('user')

            if id:
                sql = sql + " id = %s"
                values.append(id)
            elif username:
                sql = sql + " username = %s"
                values.append(username)

            cursor.execute(sql, values)

            cnx.commit()
            result = True

        except mysql.connector.Error as err:
            print(f"{RED}Error updating user information: {err}{RESET}")
            result = False
        except ValueError as err:
            result = False
        finally:
            cursor.close()
            cnx.close()
        return result

class DatabaseSession:
    @staticmethod
    def get_cursor_and_cnx():
        cnx = mysql.connector.connect(user='proiectTW', password='proiectTW',
                              host='localhost',database='proiecttw')
        return (cnx.cursor(), cnx)

    @staticmethod
    def create_table():
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            cursor.execute('''CREATE TABLE IF NOT EXISTS session (
                            id_user INT(11) NOT NULL,
                            token VARCHAR(255) NOT NULL,
                            creation_time date NOT NULL
                            )''')

            cnx.commit()  # Save the changes
            print("Table created successfully!")

        except mysql.connector.Error as err:
            print(f"{RED}Error creating table:{RESET} {err}")
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def delete_table_content():
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()
            # Delete the user from the user table
            cursor.execute('''DROP TABLE IF EXISTS session''')

            cnx.commit()  # Save the changes
            print("About cleared successfully!")

        except mysql.connector.Error as err:
            print(f"{RED}Error{RESET} clearing about: {err}")
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def create_new_session(user_id):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            session = DatabaseSession.get_session_info(id=user_id)
            if session:
                DatabaseSession.delete_session(id=user_id)

            token = secrets.token_hex(16)
            sql = f'INSERT INTO session (id_user, token, creation_time) VALUES ({user_id}, "{token}", DATE_FORMAT(NOW(),"%Y-%m-%d %h:%i:%s"))'
            #values = (user_id, token)
            cursor.execute(sql)

            cnx.commit()  # Save the changes
            print("New session added successfully!")

        except mysql.connector.Error as err:
            print(f"{RED}Error creating new user:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def get_session_info(id = None, token = None):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            if id:
                sql = "SELECT * FROM session WHERE id_user = %s"
                value = (id,)
            elif token:
                sql = "SELECT * FROM session WHERE token = %s"
                value = (token,)
            else:
                raise ValueError()
            cursor.execute(sql, value)

            user_data = cursor.fetchone()

            if user_data:
                user_info = {
                    "id":    user_data[0],
                    "token": user_data[1],
                    "time":  user_data[2]
                }
            else:
                print(f"No Session found.")
                raise ValueError()

        except mysql.connector.Error as err:
            print(f"{RED}Error retrieving session information:{RESET} {err}")
            user_info = False
        except ValueError as err:
            user_info = False
        finally:
            cursor.close()
            cnx.close()
        return user_info

    @staticmethod
    def delete_session(id=None, token=None):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            # Delete the user from the user table
            if id:
                sql = "DELETE FROM session WHERE id_user = %s"
                value = (id,)
            elif token:
                sql = "DELETE FROM session WHERE token = %s"
                value = (token,)
            else:
                raise ValueError()
            cursor.execute(sql, value)

            cnx.commit()  # Save the changes
            print("Session deleted successfully!")

        except mysql.connector.Error as err:
            print(f"{RED}Error{RESET} deleting user: {err}")
        finally:
            cursor.close()
            cnx.close()

class DatabaseCountryCode:
    @staticmethod
    def get_cursor_and_cnx():
        cnx = mysql.connector.connect(user='proiectTW', password='proiectTW',
                              host='localhost',database='proiecttw')
        return (cnx.cursor(), cnx)

    @staticmethod
    def create_code_table():
        cursor, cnx = DatabaseCountryCode.get_cursor_and_cnx()

        create_table_query = """
            CREATE TABLE country_code (
                id INT AUTO_INCREMENT PRIMARY KEY,
                country_code VARCHAR(100),
                country_name VARCHAR(100)
            )
        """

        try:
            # Execute the CREATE TABLE query
            cursor.execute(create_table_query)
            print("Table created successfully.")
        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def delete_code_table():
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            delete_table_query = "DROP TABLE IF EXISTS country_code"
            cursor.execute(delete_table_query)
            cnx.commit()
            print("Table deleted successfully.")
            return True
        except mysql.connector.Error as err:
            print(f"{RED}Error:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def get_country_names():
        cursor, cnx = DatabaseCCI.get_cursor_and_cnx()
        query = "SELECT * FROM country_code"
        cursor.execute(query)
        rows = cursor.fetchall()
        countries = {}
        for row in rows:
            countries[row[1]] = row[2]
        cursor.close()
        cnx.close()
        return countries

    @staticmethod
    def get_country_info(country_code = None, country_name = None):
        try:
            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            if country_code:
                sql = "SELECT * FROM country_code WHERE country_code = %s"
                value = (country_code,)
            elif country_name:
                sql = "SELECT * FROM country_code WHERE country_name = %s"
                value = (country_name,)
            else:
                raise ValueError()
            cursor.execute(sql, value)

            user_data = cursor.fetchone()

            if user_data:
                info = {
                    "id":           user_data[0],
                    "country_code": user_data[1],
                    "country_name": user_data[2]
                }
            else:
                print(f"No country found")
                raise ValueError()

        except mysql.connector.Error as err:
            print(f"{RED}Error retrieving user information:{RESET} {err}")
            info = False
        except ValueError as err:
            info = False
        finally:
            cursor.close()
            cnx.close()

        return info

    @staticmethod
    def create_new_country(country_code, country_name):
        try:
            country = DatabaseCountryCode.get_country_info(country_code=country_code)
            if country:
                print(f"Error creating new country.")
                return {
                    "message": False,
                    "error": "code"
                }
            country = DatabaseCountryCode.get_country_info(country_name=country_name)
            if country:
                print(f"Error creating new country.")
                return {
                    "message": False,
                    "error": "name"
                }

            cursor, cnx = DatabaseCCI.get_cursor_and_cnx()

            sql = "INSERT INTO country_code (country_code, country_name) VALUES (%s, %s)"
            values = (country_code, country_name)
            cursor.execute(sql, values)

            cnx.commit()

            country = DatabaseCountryCode.get_country_info(country_name=country_name)
            return {
                    "message": True,
                    "data": country
                }

        except mysql.connector.Error as err:
            print(f"{RED}Error creating new user:{RESET} {err}")
            return False
        finally:
            cursor.close()
            cnx.close()


def CCI_test():
    DatabaseCCI.delete_CCI_table()
    DatabaseCCI.create_CCI_table()
    DatabaseCCI.load_country_index_from_csv('example.csv')
    query = 'SELECT * FROM cci'

    cnx = mysql.connector.connect(user='proiectTW', password='proiectTW',
                              host='localhost', database='proiecttw')
    cursor = cnx.cursor()

    cursor.execute(query)
    print(cursor.fetchall())

def user_test():
    DatabaseUser.delete_user_table()
    DatabaseUser.create_user_table()
    DatabaseUser.create_new_user('Cristi', 'Josanu', 'cristi', 'cristi@gmail.com', bcrypt.hashpw('parolabuna'.encode('utf-8'), bcrypt.gensalt(10)))
    print(DatabaseUser.get_user_info(username='cristi'))
    DatabaseUser.update_user_admin('cristi')

def about_test():
    DatabaseSession.delete_table_content()
    DatabaseSession.create_table()
    DatabaseSession.create_new_session(1)
    DatabaseSession.create_new_session(2)
    DatabaseSession.create_new_session(3)
    DatabaseSession.delete_session(1)
    DatabaseSession.delete_session(2)
    DatabaseSession.delete_session(3)

def country_test():
    DatabaseCountryCode.delete_code_table()
    DatabaseCountryCode.create_code_table()
    isoCodes = {
        "NLD": "Netherlands",
        "CHE": "Switzerland",
        'FRA': "France",
        'POL': "Poland",
        'CZE': "Czech Republic",
        'JPN': "Japan",
        'OECDE': "OECDE",
        'AUS': "Australia",
        'OECD': "OECD",
        'SWE': "Sweden",
        'MEX': "Mexico",
        'GBR': "United Kingdom",
        'ZAF': "South Africa",
        'USA': "United States",
        'HUN': "Hungary",
        'PRT': "Portugal",
        'DNK': "Denmark",
        'ESP': "Spain",
        'LUX': "Luxembourg",
        'GRC': "Greece",
        'BRA': "Brazil",
        'SVK': "Slovakia",
        'CHN': "China",
        'BEL': "Belgium",
        'FIN': "Finland",
        'NZL': "New Zealand",
        'IDN': "Indonesia",
        'TUR': "Turkey",
        'AUT': "Austria",
        'ITA': "Italy",
        'IRL': "Ireland",
        'SVN': "Slovenia",
        'DEU': "Germany",
        'KOR': "South Korea",
        'EST': "Estonia",
        'ISR': "Israel",
        'RUS': "Russia",
        'LVA': "Latvia",
        'LTU': "Lithuania",
        'G7M': "G7M",
        'OEU': "OEU",
        'COL': "Colombia",
        'CHL': "Chile",
        'CRI': "Costa Rica",
        'IND': "India",
    }
    for key, value in isoCodes.items():
        DatabaseCountryCode.create_new_country(key, value)
    code = DatabaseCountryCode.get_country_info(country_code="NLD")
# delete_user('cristi')
# query = 'SELECT * FROM user'
# cursor.execute(query)
# print(cursor.fetchall())

#user_test()

#CCI_test()

#about_test()

#country_test()
