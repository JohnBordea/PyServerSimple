import datetime
import http.server
import json
import socketserver
import ssl
from urllib.parse import urlparse, parse_qs

from database_controller import DatabaseCCI, DatabaseUser, DatabaseSession, DatabaseCountryCode

PORT = 8000

CERTIFICATE_FILE = 'ssl_keys/server-signed-cert.pem'
PRIVATE_KEY_FILE = 'ssl_keys/server-key.pem'

def format_data_params(request_params):
    start_date = None
    end_date = None
    country_list = None
    if 'startDate' in request_params and request_params['startDate'] != '':
        start_date = request_params['startDate'][0]
    if 'endDate' in request_params and request_params['endDate'] != '':
        end_date = request_params['endDate'][0]
    if 'countries' in request_params and request_params['countries'] != '':
        country_list = str(request_params['countries']).replace("[", '').replace("]", '').replace("'", '').replace(
            '"', '').split(',')
    return country_list, start_date, end_date


class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def is_user_logged_in(self) -> bool:
        cookies = self.headers.get_all('Cookie')
        if cookies:
            cookie = cookies[0].split("; ")
            for item in cookie:
                x = item.split("=")
                if x[0] == 'token':
                    data = DatabaseSession.get_session_info(token=x[1])
                    if data:
                        return True
                    else:
                        return False
        return False

    def user_log_out(self):
        cookies = self.headers.get_all('Cookie')
        if cookies:
            cookie = cookies[0].split("; ")
            for item in cookie:
                x = item.split("=")
                if x[0] == 'token':
                    DatabaseSession.delete_session(token=x[1])
                #self.send_header('Set-Cookie', f'{x[0]}=deleted; expires=Thu, 01 Jan 1970 00:00:00 GMT')

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/":
            if self.is_user_logged_in():
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open('index.html', 'rb') as file:
                    self.wfile.write(file.read())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                with open('mainPage.html', 'rb') as file:
                    self.wfile.write(file.read())
        elif path == "/index.html":
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        elif path == "/mainPage.html":
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        elif path == "/login.html":
            if self.is_user_logged_in():
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                super().do_GET()
        elif path == "/logout.html":
            self.user_log_out()
            self.send_response(302)
            self.send_header('Location', '/')
            self.end_headers()
        elif path == "/edit.html" or path == "/edit-user.html" or path == "/edit-cci.html" or path == "/edit-cci-index.html":
            if not self.is_user_logged_in():
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                super().do_GET()

        elif path == '/api/data':
            request_params = parse_qs(parsed_url.query)

            country_list, start_date, end_date = format_data_params(request_params)
            
            if country_list is not None:
                response_body = json.dumps(DatabaseCCI.get_countries(country_list, start_date=start_date, end_date=end_date))
            else:
                response_body = json.dumps(DatabaseCCI.get_all_countries(start_date=start_date, end_date=end_date))
            #print(f'response_body={response_body}')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Send the JSON response
            self.wfile.write(response_body.encode())
        elif path == '/api/data/years':
            request_params = parse_qs(parsed_url.query)

            country_body = DatabaseCountryCode.get_country_names()
            years_body = DatabaseCCI.get_years()
            response_body = {
                'country': country_body,
                'years': years_body
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode())
        elif path == '/api/data/year':
            request_params = parse_qs(parsed_url.query)

            response_body = DatabaseCCI.get_country_year(request_params['country'][0], int(request_params['year'][0]))

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode())
        elif path == '/api/data/edit':
            request_params = parse_qs(parsed_url.query)

            response_body = DatabaseCCI.get_data_from_id(int(request_params['id'][0]))

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode())
        elif path == "/api/countries":
            country_names = DatabaseCCI.get_country_names()
            response_body = json.dumps(country_names)
            #print(f'response_body={response_body}')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Send the JSON response
            self.wfile.write(response_body.encode())
        elif path == "/api/table":
            request_params = parse_qs(parsed_url.query)
            start_date = None
            end_date = None
            countries_param = None
            if 'startDate' in request_params and request_params['startDate'] != '':
                start_date = request_params['startDate'][0]
            if 'endDate' in request_params and request_params['endDate'] != '':
                end_date = request_params['endDate'][0]
            if 'countries' in request_params.keys() and request_params['countries'] != '':
                countries_param = request_params['countries'][0]

            if countries_param:
                countries_selected = countries_param.split(',')
                print(countries_selected)
                db_cci = DatabaseCCI.get_countries(countries=countries_selected, start_date=start_date, end_date=end_date)
            else:
                db_cci = DatabaseCCI.get_all_countries(start_date=start_date, end_date=end_date)
            countries = {}
            for item in db_cci:
                for country in item.keys():
                    if country != "date":
                        if country not in countries.keys():
                            countries[country] = {item["date"]: item[country]}
                        else:
                            countries[country][item["date"]] = item[country]
            
            response_body = json.dumps(countries)
            #print(f'response_body={response_body}')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Send the JSON response
            self.wfile.write(response_body.encode())
        elif path == '/api/map':
            request_params = parse_qs(parsed_url.query)
            start_date = None
            end_date = None
            if 'startDate' in request_params and request_params['startDate'] != '':
                start_date = request_params['startDate'][0]
            if 'endDate' in request_params and request_params['endDate'] != '':
                end_date = request_params['endDate'][0]
            
            db_cci = DatabaseCCI.get_all_countries(start_date=start_date, end_date=end_date)

            mean_values = {}
            for entry in db_cci:
                for country, value in entry.items():
                    if country != 'date':
                        mean_values.setdefault(country, []).append(value)
            mean_values = {country: sum(values) / len(values) for country, values in mean_values.items()}
            
            response_body = json.dumps(mean_values)
            #print(f'response_body={response_body}')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Send the JSON response
            self.wfile.write(response_body.encode())
        elif path == '/api/download':
            request_params = parse_qs(parsed_url.query)
            print(f'request params = {request_params}')
            country_list, start_date, end_date = format_data_params(request_params)
            chart_type = request_params['chartType'][0]
            file = []
            if chart_type == "line" or chart_type == "table":
                file = DatabaseCCI.get_download_file_as_csv(countries=country_list, start_date=start_date, end_date=end_date)
            elif chart_type == "map":
                db_cci = DatabaseCCI.get_all_countries(start_date=start_date, end_date=end_date)
                mean_values = {}
                for entry in db_cci:
                    for country, value in entry.items():
                        if country != 'date':
                            mean_values.setdefault(country, []).append(value)
                mean_values = {country: sum(values) / len(values) for country, values in mean_values.items()}
                file.append(['Country', 'Mean Value'])
                for key in mean_values.keys():
                    file.append([key, mean_values[key]])
            
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.end_headers()

            # Send the CSV file as the response
            self.wfile.write(json.dumps(file).encode())
        elif path == '/api/users':

            #verify if user is logged in
            if self.is_user_logged_in():
                file = DatabaseUser.get_all_user_info()
            else:
                file = []

            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.end_headers()
            self.wfile.write(json.dumps(file).encode())
        elif path == '/api/user':
            request_params = parse_qs(parsed_url.query)

            #verify if user is logged in
            if self.is_user_logged_in():
                file = DatabaseUser.get_user_info(id=int(request_params['id'][0]))
            else:
                file = {}

            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.end_headers()
            self.wfile.write(json.dumps(file).encode())
        else:
            super().do_GET()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == 'api/data':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            for entry in data:
                DatabaseCCI.create_country_index(entry['country_name'], entry['date'], entry['index_value'])
            else:
                self.send_response(400)
        elif path == "/api/login":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "username" in data.keys():
                username = data['username']
            else:
                checker = False
            if "password" in data.keys():
                password = data['password']
            else:
                checker = False

            if checker:
                data = DatabaseUser.is_user_present(username, password)
                if data:
                    DatabaseSession.create_new_session(data['id'])
                    session = DatabaseSession.get_session_info(id=data['id'])
                    response = {
                        'message': True,
                        'data': data,
                        'token': session['token']
                    }
                else:
                    response = {'message': False}
            else:
                response = {'message': False}

            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif path == "/api/addUser":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "firstname" in data.keys():
                firstname = data['firstname']
            else:
                checker = False
            if "lastname" in data.keys():
                lastname = data['lastname']
            else:
                checker = False
            if "username" in data.keys():
                username = data['username']
            else:
                checker = False
            if "email" in data.keys():
                email = data['email']
            else:
                checker = False
            if "password" in data.keys():
                password = data['password']
            else:
                checker = False
            if "role" in data.keys():
                role = data['role']
            else:
                checker = False

            if checker:
                response = DatabaseUser.create_new_user(firstname, lastname, username, email, password)
                if response["message"] and role:
                    DatabaseUser.update_user_admin(username=response["data"]["username"])
            else:
                response = {
                    'message': False,
                    'error': 'invalidData'
                }

            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif path == "/api/register":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "firstname" in data.keys():
                firstname = data['firstname']
            else:
                checker = False
            if "lastname" in data.keys():
                lastname = data['lastname']
            else:
                checker = False
            if "username" in data.keys():
                username = data['username']
            else:
                checker = False
            if "email" in data.keys():
                email = data['email']
            else:
                checker = False
            if "password" in data.keys():
                password = data['password']
            else:
                checker = False

            if checker:
                response = DatabaseUser.create_new_user(firstname, lastname, username, email, password)
            else:
                response = {
                    'message': False,
                    'error': 'invalidData'
                }

            # Send the response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif path == "/api/exist/email":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "email" in data.keys():
                email = data['email']
            else:
                checker = False

            if checker:
                data = DatabaseUser.get_user_info(email=email)
                if data:
                    response = {
                        'message': True
                    }
                else:
                    response = {
                        'message': False
                    }
            else:
                response = {
                    'message': False
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif path == "/api/session":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "token" in data.keys():
                token = data['token']
            else:
                checker = False

            if checker:
                data = DatabaseSession.get_session_info(token=token)
                if data:
                    response = {
                        'message': True
                    }
                else:
                    response = {
                        'message': False
                    }
            else:
                response = {
                    'message': False
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif path == "/api/data/edit":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "country" in data.keys():
                country = data['country']
            else:
                checker = False
            if "date" in data.keys():
                date = data['date']
            else:
                checker = False
            if "index" in data.keys():
                index = data['index']
            else:
                checker = False

            if checker:
                data = DatabaseCCI.check_country_date(country, date, index)
                if data:

                    response = {
                        'message': True
                    }
                else:
                    response = {
                        'message': False,
                        "error": "exist"
                    }
            else:
                response = {
                    'message': False,
                    "error": "invalid"
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_PUT(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == 'api/data':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            for entry in data:
                DatabaseCCI.create_country_index(entry['country_name'], entry['date'], entry['index_value'])
            else:
                self.send_response(400)
        if path =='/api/user/password':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "email" in data.keys():
                email = data['email']
            else:
                checker = False
            if "password" in data.keys():
                password = data['password']
            else:
                checker = False

            if checker:
                data = DatabaseUser.update_user_info(id=DatabaseUser.get_user_info(email=email)['id'], new_password=password)
                if data:
                    response = {
                        'message': True
                    }
                else:
                    response = {
                        'message': False
                    }
            else:
                response = {
                    'message': False
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        if path =='/api/user':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "id" in data.keys():
                user_id = int(data['id'])
            else:
                checker = False
            if "firstname" in data.keys():
                firstname = data['firstname']
            else:
                checker = False
            if "lastname" in data.keys():
                lastname = data['lastname']
            else:
                checker = False
            if "username" in data.keys():
                username = data['username']
            else:
                checker = False
            if "email" in data.keys():
                email = data['email']
            else:
                checker = False
            if "role" in data.keys():
                role = data['role']
            else:
                checker = False

            if checker:
                data = DatabaseUser.update_user_info(id=user_id, new_firstname=firstname, new_lastname=lastname, new_username=username, new_email=email)
                if data:
                    DatabaseUser.update_user_admin(id=user_id, role=role)
                    response = {
                        'message': True
                    }
                else:
                    response = {
                        'message': False
                    }
            else:
                response = {
                    'message': False
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        if path =='/api/data/edit':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)

            checker = True
            if "id" in data.keys():
                user_id = int(data['id'])
            else:
                checker = False
            if "index" in data.keys():
                index = data['index']
            else:
                checker = False

            if checker:
                data = DatabaseCCI.update_country_index_by_id(user_id, index)
                if data:
                    response = {
                        'message': True
                    }
                else:
                    response = {
                        'message': False
                    }
            else:
                response = {
                    'message': False
                }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))


    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == 'api/data':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            for entry in data:
                DatabaseCCI.create_country_index(entry['country_name'], entry['date'])
            else:
                self.send_response(400)

# Create an SSL context and load the certificate and private key files
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile=CERTIFICATE_FILE, keyfile=PRIVATE_KEY_FILE)


Handler = MyRequestHandler

httpd = socketserver.TCPServer(('localhost', PORT), Handler)
httpd.socket = ssl_context.wrap_socket(httpd.socket)
print(f'Server running on https://localhost:{PORT}')

httpd.serve_forever()
