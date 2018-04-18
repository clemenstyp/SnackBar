# SnackBar

This is a web app for a digital coffee list hosted on an IPad.

It is based on CoffeeList from "duscheln": https://github.com/duscheln/CoffeeList


# Installation

* Install the pip requirements as denoted in requirements.txt:

```
pip install --user -r requirements.txt
```

* You can change the userList.csv as shown in the template. These users will be imported, when a database is created. You can add or remove useres at a later time
* Standard items will be created at start. You can change the price and names in the admin panel later.

* To start the SnackBar with the folowing command:

```
python SnackBar.py --port 8000
```

* you can add --port and -- host to change port and host.

```
python SnackBar.py --host 127.0.1.1 --port 8000
```

* The initial username and password for the admin interface are:

```
username: admin
password: admin
```

* you can change the password in the "Admins" section.

# Screenshots

![alt tag](https://github.com/clemenstyp/SnackBar/raw/master/screenshots/overview.png)
![alt tag](https://github.com/clemenstyp/SnackBar/raw/master/screenshots/buy.png)
![alt tag](https://github.com/clemenstyp/SnackBar/raw/master/screenshots/user.png)
![alt tag](https://github.com/clemenstyp/SnackBar/raw/master/screenshots/bill.png)