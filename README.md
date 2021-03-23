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
  - `triage_guidelines` -- optional, defaults to empty; shown on review: triage stage. HTML assumed
  - `random_paper_order` -- optional, defaults to false. If true: triage returns 10 random papers
  - `submit_button_text` -- optional. If specified, displays a button on the index for submitting data with this text.
  - `index-content` -- optional, a filename for a file with content for the homepage; content appears for users regardless of if they are logged-in
  - `css` -- optional; style information included on every page
  - `pipeline_review_buttons` -- list of buttons and their properties for review queues;
    from our experience, we recommend including at least reject, accept, and discussion queues.
    (This list is also used for the "Review" menu.)

    Example:

        "pipeline_review_buttons": [
          {
              "name": "Relevant",
              "queue": "relevant",
              "color": "green"
          },
          {
              "name": "Low priority",
              "queue": "low-priority",
              "color": "yellow",
              "font_color": "black"
          },
          {
              "name": "Not relevant",
              "queue": "not-relevant",
              "color": "red"
          }
        ]
-  `pipeline_annotation` (optional, but required for annotation phase of the pipeline); should be in this general format, where the
   `pipeline_metadata_tags_autocomplete_file` is a JSON file representation of a dictionary whose keys are names and the values are
   tag ids. If not specified, the metadata tags during the annotate phase are unrestricted.

     "pipeline_annotation": {
        "title": "Annotate",
        "queue_in": "relevant",
        "next_button": {
            "queue": "prepare_submission",
            "name": "Next"
        },
        "fields": [
            {
                "name": "Your Excerpt",
                "short_name": "excerpt",
                "placeholder": "Put an excerpt describing your conclusions",
                "type": "text"
            },
            {
                "name": "Confidence",
                "short_name": "confidence",
                "placeholder": "How confident are you about your conclusions?",
                "type": "text"
            }
        ],
        "pipeline_metadata_tags_autocomplete_file": "/home/bitnami/metadata_autocomplete.json"
    }
    - `data` -- optional but required for enabling /data/ pages
      "data": {
        "enabled": true <-- required for allowing data pages (like entry, but not editable)
        "header": "..." <-- optional, can include html
      }
  - `solicit_message_template` -- optional, but required for email button on entry pages (note: express newlines as `\\n`)
  - `solicit_subject_template` -- optional, but required for email button on entry pages
  - `solicit_email_field` -- optional, but required for email button on entry page; corresponds to a GLOBAL field in `userentry`
  - `userentry` -- optional but required for enabling /entry/ pages
    "userentry": {
      "title": "...",
      "logfile": "...",
      "allow_multiple": true, <-- optional; defaults to false
      "multiple_button_name": "Add another", <-- optional; defaults as shown
      "header": "...", <-- optional, can include html
      "global_fields": [
        {
            "name": "visible name",
            "help_text": "text to appear when clicking the ?",
            "example": "...",
            "field": "database name",
            "readonly": true, <-- optional, defaults to false (readonly for public users; editable for logged-in users)
            "multiline": true <-- optional, defaults to false
        },
      ... <-- more optional and required fields
    }
- Apply the django migrations
  `python3 manage.py migrate`
- Run `python3 setup/permissions.py` script to declare the possible pipeline permissions.
- You will also want to use django admin to create a user with admin permissions from within the
  shell you get via `python3 manage.py shell`.
  Example extended from: https://docs.djangoproject.com/en/3.0/topics/auth/default/#creating-users
  ```
  from django.contrib.auth.models import User
  user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
  user.is_superuser = True
  user.is_staff = True
  user.save()
  ```
- You can run a development server via, e.g. `python3 manage.py runserver 8888`
  - This will make the website available on port 8888 (you can then access it from your host system via port-forwarding.
  - This is separate from apache, which is also running if you're using the bitnami stack and can later be connected to your django system.

## On users and permissions

Assuming you set the `is_superuser` and `is_staff` attributes of your initial user and saved them as above,
that user will have access to all pages and (because of the `is_staff` attribute) can access the /admin pages as well
to create new users and to assign specific permissions to groups and to users.

When setting permissions: you'll want to filter for "pipeline". Choices include "auth | user | Can browse pipeline",
"auth | user | Can do pipeline reviews", and "auth | user | Can see pipeline statistics". These permissions can be
added to individual users or groups.

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

## On combining with other tools
- Make sure that the other tools include javascript code to support CSRF in their main.html, as is done here.

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
