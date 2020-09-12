# pipeline

## Overview

This is a generic tool for triaging documents and assigning metadata.

This is developed and tested on a bitnami django stack.

## Getting started
- Download the [bitnami django stack OVA][1]
- Import it into a virtual machine such as [VirtualBox][2]
- Install the community edition of MongoDB following [these directions][3]
  - note: if you're using Amazon lightsail instead, you'll need to switch to the instructions for Ubuntu. At this writing it's using Ubuntu 16.04.
- Create a MongoDB account with readwrite access to a specific database (for simplicity, you may want to call it `pipeline`)
  - launch MongoDB by typing `mongo`
  - switch to the database you want to use e.g. `use pipeline`
  - create the user:
  
        db.createUser({
            user: "username",
            pwd: "password",
            roles: [{role: "userAdmin", db:"pipeline"}]})
            
- Install git so you can clone this repository, if it's not already installed `sudo apt install git`
- Clone this repository
- Install Python dependencies (`sudo pip3 install -r requirements.txt`)
- Create a settings file in the exact path `/home/bitnami/app-settings.json` (this path could be changed by modifying the `settings.py` file). It should have values for:
  - `secret_key` (I'm unclear on if there are any rules on this, but I guess a random 50 character string should work)
  - `mongodb_user`
  - `mongodb_pw`
  - `db_name` -- set this to `pipeline` or whatever you called the database you wish to use.
  - `collection_name` -- this is the collection where the pipeline data will go
  - `pipelinebase` -- optional, but set to e.g. `pipeline` if you want links to go to start with `/pipeline/`
  - `footerhtml` -- optional, but anything you put here will appear in the footer of every page
  - `toolname` -- optional, defaults to "Pipeline"
  - `browse_fields` -- optional, defaults to all
- Apply the django migrations
  `python3 manage.py migrate`
- You will also want to use django admin to create a user with admin permissions from within the
  shell you get via `python3 manage.py shell`.
  Example from: https://docs.djangoproject.com/en/3.0/topics/auth/default/#creating-users
  ```
  from django.contrib.auth.models import User
  user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')```
- You can run a development server via, e.g. `python3 manage.py runserver 8888`
  - This will make the website available on port 8888 (you can then access it from your host system via port-forwarding.
  - This is separate from apache, which is also running if you're using the bitnami stack and can later be connected to your django system.

## On data storage

Every document in the pipeline collection should have the following form:

    {
        "title": "Some title",
        "url": "https://some.url",
        "field_order": ['fieldname1', 'fieldname2'],
        "fieldname1": ["alert1", "alert2"],
        "fieldname2": "This is a snippet..."
        ]
    }

where e.g. fieldname1, fieldname2, ... are arbitrary. Use a list for values that should appear separately on the statistics report.

When the pipeline app starts, any document in the pipeline collection that does not have a `status` attribute will have its `status` attribute set to `"triage"`.
Likewise, any document that does not have a `notes` attribute will have its `notes` attribute set to the empty string.

For performance reasons, the `status` attribute of the documents should be indexed; e.g.

    db.collection.create_index([("status", 1)])

## Deployment hints
- If you're deploying on bitnami's django stack, see their instructions at: https://docs.bitnami.com/virtual-machine/infrastructure/django/get-started/deploy-django-project/
- be sure to turn off debugging in the settings file
- the sqlite3 database needs to be writeable and it needs to be in a folder that's writeable (so not in a path that hosts the website code)
  (e.g. you might put it in /home/bitnami/db/ and modify settings.py accordingly)
- if you make any changes on a bitnami machine with apache setup; run `sudo /opt/bitnami/ctlscript.sh restart apache` to restart
- wsgi.py needs the correct name of the settings module... it's currently setup to use `Project` as the folder name, but that
  may not be appropriate if this is one django app on a more complicated website.
 - the settings file may need the full path to `TEMPLATES["DIRS"]`



## Contributing
For stylistic consistency, all Python code is to be formatted using `black`.

Get `black` via `sudo pip3 install black` and run with `black .` (or whatever folder).


## Technologies

The pipeline is powered in part by a number of other technologies, including:

### Backend
- [python](https://python.org)
- [django](https://www.djangoproject.com/)
- [mongodb](https://mongodb.com)
- [pymongo](https://pypi.org/project/pymongo/)
- [bitnami django stack][1]

### Frontend
- [jQuery](https://jquery.com)
- [jQuery UI](https://jqueryui.com/)
- [Bootstrap](https://getbootstrap.com/)
- [Font Awesome](https://fontawesome.com)
- [select2](https://select2.org/)
- [popper](https://popper.js.org)
- [Bootstrap Table](https://bootstrap-table.com/)


Did we miss something? Submit a pull request!

[1]: https://bitnami.com/stack/django/virtual-machine "Bitnami django OVA"
[2]: https://www.virtualbox.org/ "VirtualBox"
[3]: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-debian/ "MongoDB installation guide"