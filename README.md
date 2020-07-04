# Label_system
> Label system for ultrasound image of the thyroid nodule

## Start the web server and login administrator account

### Downloading the code
```bash
git clone https://github.com/guobbin/label_system.git
```

### Downloading dependencies

```bash
pip3 install -r requirements.txt  
```

### Start and connect to the mysql server

```bash
mysql.server start
mysql -uroot -p
# input your mysql account password
```

### Create label_system database

```bash
create database if not exists label_system
default character set utf8;
show databases;
```

### Data migration
> come to `label_system/` and run the script:
```bash
python manage.py db init
python manage.py db migrate
python manage.py db upgrade
```
> now come back to the mysql, and we can see the database schema created by SqlAlchemy.
```bash
use label_sysetem;
show tables;
```
> add an administrator account
```bash
insert into user values(1, true,'gbb','123')
```
### Start the server 
> you can start the server and login the system
```bash
python2 label.py
```
> open the browser and enter `http://127.0.0.1:5000`

> the administrator's username and password: 'gbb' and '123'


## The administrator has permission to import data
> download the data sample [here](https://pan.baidu.com/s/1Wy6tUiHaBPqtbfOUb0s17g ), password:dv6o. 
> unzip and upload the folder 
> the current version only supports Chrome browser