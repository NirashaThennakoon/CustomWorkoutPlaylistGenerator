
# PWP SPRING 2024
# Custom Workout Playlist Generator
```
  ____          _                   __        __         _               _        
 / ___|   _ ___| |_ ___  _ __ ___   \ \      / /__  _ __| | _____  _   _| |_      
| |  | | | / __| __/ _ \| '_ ` _ \   \ \ /\ / / _ \| '__| |/ / _ \| | | | __|     
| |__| |_| \__ \ || (_) | | | | | |   \ V  V / (_) | |  |   < (_) | |_| | |_      
 \____\__,_|___/\__\___/|_| |_| |_| ___\_/\_/ \___/|_|  |_|\_\___/ \__,_|\__|     
|  _ \| | __ _ _   _| (_)___| |_   / ___| ___ _ __   ___ _ __ __ _| |_ ___  _ __  
| |_) | |/ _` | | | | | / __| __| | |  _ / _ \ '_ \ / _ \ '__/ _` | __/ _ \| '__| 
|  __/| | (_| | |_| | | \__ \ |_  | |_| |  __/ | | |  __/ | | (_| | || (_) | |    
|_|   |_|\__,_|\__, |_|_|___/\__|  \____|\___|_| |_|\___|_|  \__,_|\__\___/|_|    
               |___/                                                                
```
# Group information
* Student 1. Iresh Jayasundara - Iresh.JayasundaraMudiyanselage@student.oulu.fi
* Student 2. Kavindu Wijesinghe - Kavindu.WijesingheArachchilage@student.oulu.fi
* Student 3. Sonali Prasadika - Sonali.LiyanaBadalge@student.oulu.fi
* Student 4. Nirasha Thennakoon - Nirasha.KaluarachchiThennakoonAppuhamilage@student.oulu.fi

# Database Implementation :Custom Workout Playlist Generator
The following chapter describes the the selection of databases, libraries and instructions to setup the requirements needed for the Custom Workout Playlist Generator. 

## 🔗 Dependencies and Setup

Following tools and libraries are required for setting up the database for the Custom Workout Playlist Generator. Note that the steps in this section listed below is designed as a guide for you to manually setup the database. If you wish to skip these steps and directly create the database, tables and dummy data, jump to the installing MySql step and follow the next section titled **Flask app setup.** 

[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](https://www.python.org)

- [x]  Install latest python version from [here.](https://www.python.org) 3.11.5 is recommended 
- [x]  Install pip from [here.](https://pip.pypa.io/en/stable/installation/) 23.2.1 is recommended.
Note: pip will be available as a part of your python installation. you can check the pip version for verifying.
```bash
pip --version
```
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/en/3.0.x/)

Flask is a web application framework written in Python. Read more abput flask from [here.](https://flask.palletsprojects.com/en/3.0.x/) Install flask 2.2.2 using the following command.
```bash
pip install flask
```


![Static Badge](https://img.shields.io/badge/SQLAlchemy--00353fe)

The Flask SQL Alchemy SQL Toolkit and Object Relational Mapper is a comprehensive set of tools for working with databases and Python. It has several distinct areas of functionality which can be used individually or combined together. Its major components are illustrated below, with component dependencies organized into layers: [Read more here](https://docs.sqlalchemy.org/en/20/intro.html)

- [x]  Install FlaskSQLAlchemy. Use pip to install or refer [here](https://docs.sqlalchemy.org/en/20/intro.html#installation) for other methods of installation.
```bash
pip install flask-sqlalchemy sqlalchemy
```
![Static Badge](https://img.shields.io/badge/mysqlclient-2299ff)

Mysqlclient is an interface to the MySQL database server that provides the Python database API.

```bash
pip install mysqlclient
```

![Swagger](https://img.shields.io/badge/-Swagger-%23Clojure?style=for-the-badge&logo=swagger&logoColor=white)

[Swagger](https://swagger.io/docs/specification/2-0/what-is-swagger/) allows to describe the structure of the APIs so that machines can read them.

```bash
pip install flasgger
```
[![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/downloads/)

MySQL was chosen as a database for the project because it's free to use, widely used, and performs well with large amounts of data. It's easy to scale up as projects grow and works with many programming languages. Plus, it's secure and stable, making it a reliable option for important tasks.

- [x]  install MySQL communuty edition from [here](https://www.mysql.com/products/community/)
- [x]  When prompted for the credentials duting the installation wizard, use the **username root  and password root.** if you wish to use a different credentials, make sure to update the modified credentials when runng the app.py in the next section. 
- [x]  Configre the MySQL server to run on your OS with your credentials.



## install the follwoing libs to run Custom Workout Playlist Generator
- ☑️ blinker==1.7.0
- ☑️ click==8.1.7
- ☑️ colorama==0.4.6
- ☑️ Flask==3.0.2
- ☑️ Flask-SQLAlchemy==3.1.1
- ☑️ greenlet==3.0.3
- ☑️ itsdangerous==2.1.2
- ☑️ Jinja2==3.1.3
- ☑️ MarkupSafe==2.1.5
- ☑️ mysqlclient==2.2.3
- ☑️ python-dateutil==2.8.2
- ☑️ pytz==2023.3.post1
- ☑️ six==1.16.0
- ☑️ SQLAlchemy==2.0.25
- ☑️ typing_extensions==4.9.0
- ☑️ tzdata==2023.4
- ☑️ Werkzeug==3.0.1
- ☑️ flask-jwt-extended==4.6.0
- ☑️ pytest=8.1.1
- ☑️ flasgger==0.9.5

#Flask App and Environment Setup

If you have skipped the manual setup to install the required libraries, you can use the ❎❎**requirements.txt**❎❎ file to install the nessacery libraries. 

- [x]  We recommend you use a Python Virtual Environment for setting-up the next steps.
- [x]  Create a folder of your choosing for the virtual Environment
- [x]  Clone our repo to the folder
- [x]  Use the folder path to create the Virtual Environment
```bash
python3 -m venv /path/to/the/virtualenv
```
- [x]  Activate the Virtual Environment

```bash
c:\path\to\the\virtualenv\Scripts\activate.bat
on OSX
source /path/to/the/virtualenv/bin/activate
```
```bash
pip install -r requirements.txt
```
- [x]  Run the flask App. this will create all the tables and relationships in your environment. make sure to change the password install to the database url if you have used a password of your own.
```python
app.config["SQLALCHEMY_DATABASE_BASE_URI"] = "mysql+mysqldb://root@localhost/"
```
```bash
python __init__.py
```
- [x] To add sample data to the tables, you can run the provided sql dump using the following command.

```bash
use workout_playlists
source /path/to/sql/your_sql_file.sql
```
## Running Tests

To run all test cases 

```bash
Run “pytest” cmd in project folder
```

To run specific test class 
```bash
– Run pytest <path to test folder>/<testclassname>.py
```
## link to the API documentation

```bash
http://localhost:5000/apidocs/
```
