# Getting started

**TODO: update this** This section presents ~~two~~ approaches to getting started with ~~KerkoApp~~: running
from a standard installation of KerkoApp, or running from a Docker container
pre-built with KerkoApp. You may choose the one you are most comfortable with.

KerkoApp is just a thin container around Kerko. As such, almost all of its
features are inherited from Kerko. See [Kerko's documentation][Kerko] for the
list of features.

The main features added by KerkoApp over Kerko's are:

**TODO:config: Update this description!**

- Read most configuration from environment variables or a `.env` file, adhering
  to the [Twelve-factor App](https://12factor.net/config) methodology.
- Provide extra environment variables for:
    - defining facets based on Zotero collections;
    - excluding or including tags or child items (notes and attachments) with
      regular expressions;
    - excluding fields, facets, sort options, search scopes, record download
      formats, or badges from Kerko's defaults.
- Provide templates for common HTTP errors.
- Load user interface translations based on the configured locale.

## Getting started with KerkoApp

### Standard installation

This procedure requires Python 3.7 or later.

1. The first step is to install the software. As with any Python package, it is
   highly recommended to install it within a [virtual environment][venv].

   ```bash
   git clone https://github.com/whiskyechobravo/kerkoapp.git
   cd kerkoapp
   pip install -r requirements/run.txt
   ```

   This will install many packages required by Kerko or KerkoApp.

2. Copy the `sample.env` file to `.env`. Open `.env` in a text editor to assign
   proper values to the variables outlined below.

   - `KERKOAPP_SECRET_KEY`: This variable is required for generating secure tokens in web
     forms. It should have a secure, random value and it really has to be
     secret. For this reason, never add your `.env` file to a code repository.
   - `KERKOAPP_ZOTERO_API_KEY`, `KERKOAPP_ZOTERO_LIBRARY_ID` and
     `KERKOAPP_ZOTERO_LIBRARY_TYPE`: These variables are required for Kerko to be
     able to access your Zotero library. See [Environment
     variables](#environment-variables) for details.

3. Have KerkoApp retrieve your data from zotero.org:

   ```bash
   flask --debug kerko sync
   ```

   If you have a large bibliography and/or large file attachments, that command
   may take a while to complete (and there is no progress indicator). In
   production use, that command is usually added to the crontab file for regular
   execution.

   The `--debug` switch is optional. If you use it, some messages will give you
   an idea of the sync process' progress. If you omit it, the command will run
   silently unless there are warnings or errors.

4. Run KerkoApp:

   ```bash
   flask --debug run
   ```

5. Open http://localhost:5000/ in your browser and explore the bibliography.

Note that Flask's built-in server is **not suitable for production** as it
doesn’t scale well. You'll want to consider better options, such as the [WSGI
servers suggested in Flask's documentation][Flask_production].


### Docker installation

This procedure requires that [Docker] is installed on your computer.

1. Copy the `Makefile` and `sample.env` files from [KerkoApp's
   repository][KerkoApp] to an empty directory on your computer.

2. Rename `sample.env` to `.env`. Open `.env` in a text editor to assign proper
   values to the variables outlined below.

   - `KERKOAPP_SECRET_KEY`: This variable is required for generating secure tokens in web
     forms. It should have a secure, random value and it really has to be
     secret. For this reason, never add your `.env` file to a code repository.
   - `KERKOAPP_ZOTERO_API_KEY`, `KERKOAPP_ZOTERO_LIBRARY_ID` and
     `KERKOAPP_ZOTERO_LIBRARY_TYPE`: These variables are required for Kerko to be
     able to access your Zotero library. See [Environment
     variables](#environment-variables) for details.
   - `MODULE_NAME`: This variable is required for running the application with
     the provided Docker image. See `sample.env` for the proper value.

   **Do not** assign a value to the `KERKOAPP_DATA_DIR` variable. If you do, the
   volume bindings defined within the `Makefile` will not be of any use to the
   application running within the container.

3. Pull the latest KerkoApp Docker image. In the same directory as the
   `Makefile`, run the following command:

   ```bash
   docker pull whiskyechobravo/kerkoapp
   ```

4. Have KerkoApp retrieve your bibliographic data from zotero.org:

   ```bash
   make kerkosync
   ```

   If you have a large bibliography, this may take a while (and there is no
   progress indicator).

   Kerko's index will be stored in the `data` subdirectory.

5. Run KerkoApp:

   ```
   make run
   ```

6. Open http://localhost:8080/ in your browser and explore the bibliography.

Keep in mind that the `sample.env` and `Makefile` provide only examples on how
to run the dockerized KerkoApp. Also, **we have not made any special effort to
harden the KerkoApp image for production use**; for such use, you will have to
build an image that is up to your standards. For full documentation on how to
run Docker containers, including the port mapping and volume binding required to
run containers, see the [Docker documentation][Docker_docs].


## Creating a custom application

This section should help you understand the minimal steps required for getting
Kerko to work within a Flask application. **For a ready-to-use standalone
application, please refer to [KerkoApp's installation instructions][KerkoApp]
instead.**

Some familiarity with [Flask] should help you make more sense of the
instructions, but should not be absolutely necessary for getting them to work.
Let's now build a minimal app:

1. The first step is to install Kerko. As with any Python library, it is highly
   recommended to install Kerko within a [virtual environment][venv].

   Once the virtual environment is set and active, use the following command:

   ```bash
   pip install kerko
   ```

2. In the directory where you want to install your application, create a file
   named `.env`, where variables required by Kerko will be configured, with
   content such as the example below:

   ```sh
   MYAPP_SECRET_KEY="your-random-secret-key"  # Replace this value.
   MYAPP_ZOTERO_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxx"  # Replace this value.
   MYAPP_ZOTERO_LIBRARY_ID="9999999"  # Replace this value.
   MYAPP_ZOTERO_LIBRARY_TYPE="group"  # Replace this value if necessary.
   ```

   Here's the meaning of each variable:

   - `MYAPP_SECRET_KEY`: This variable is required for generating secure tokens
     in web forms. It should have a hard to guess, random value, and should
     really remain secret.
   - `MYAPP_ZOTERO_API_KEY`, `MYAPP_ZOTERO_LIBRARY_ID`, and
     `MYAPP_ZOTERO_LIBRARY_TYPE`: These variables are required for Kerko to be
     able to access your Zotero library. See [Configuration
     variables](#configuration-variables) for details on how to properly set
     these variables.

   A `.env` file is a good place to store an application's secrets. It is good
   practice to keep this file only on the machine where the application is
   hosted, and to never push it to a code repository.

3. Create a file named `wsgi.py` with the following content:

   ```python
   import kerko
   from flask import Flask
   from kerko.config_helpers import config_set, config_update
   from kerko.composer import Composer

   app = Flask(__name__)
   app.config.from_prefixed_env(prefix='MYAPP')
   config_update(app.config, kerko.DEFAULTS)

   # Make changes to the Kerko configuration here, if desired.
   config_set(app.config, 'kerko.meta.title', 'My App')

   validate_config(app.config)
   app.config['kerko_composer'] = Composer(app.config)
   ```

   This code creates the Flask application object (`app`), loads configuration
   settings from the `.env` file, and sets two more configuration variables:

   - `kerko`: This variable contains Kerko's configuration settings, which are
     represented in a Python `dict`. Here we simply assign the default values
     from `DEFAULTS`.
   - `kerko_composer`: This variable specifies key elements needed by Kerko,
     e.g., fields for display and search, facets for filtering. These are
     defined by instantiating the `Composer` class. Your application may
     manipulate the resulting object at configuration time to add, remove or
     alter fields, facets, sort options, search scopes, record download formats,
     or badges. See [Kerko Recipes](#kerko-recipes) for some examples.

4. Also configure the Flask-Babel and Bootstrap-Flask extensions:

   ```python
   from flask_babel import Babel
   from flask_bootstrap import Bootstrap4

   babel = Babel(app)
   bootstrap = Bootstrap4(app)
   ```

   See the respective docs of [Flask-Babel][Flask-Babel_documentation] and
   [Bootstrap-Flask][Bootstrap-Flask_documentation] for more details.

5. Instantiate the Kerko blueprint and register it in your app:

   ```python
   import kerko

   app.register_blueprint(kerko.blueprint, url_prefix='/bibliography')
   ```

   The `url_prefix` argument defines the base path for every URL provided by
   Kerko.

6. In the same directory as `wsgi.py` with your virtual environment active, run
   the following shell commands:

   ```bash
   flask --debug kerko sync
   ```

   Kerko will retrieve your bibliographic data from zotero.org. If you have a
   large bibliography or large attachments, this may take a while (and there is
   no progress indicator). In production use, that command is usually added to
   the crontab file for regular execution (with enough time between executions
   for each to complete before the next one starts).

   The `--debug` switch is optional. If you use it, some messages will give you
   an idea of the sync process' progress. If you omit it, the command will run
   silently unless there are warnings or errors.

   To list all commands provided by Kerko:

   ```bash
   flask kerko --help
   ```

7. Run your application:

   ```bash
   flask --debug run
   ```

8. Open http://127.0.0.1:5000/bibliography/ in your browser and explore the
   bibliography.

You have just built a really minimal application for Kerko. The full code
example is available at [KerkoStart]. However, if you are looking at developing
a custom Kerko application, we recommend that you still look at [KerkoApp] for a
more advanced starting point. While still small, KerkoApp adds some structure as
well as features such as a configuration file, translations loading, and error
pages.


[Bootstrap-Flask_documentation]: https://bootstrap-flask.readthedocs.io/en/latest/basic.html
[Docker_docs]: https://docs.docker.com/
[Docker]: https://www.docker.com/
[Flask_production]: https://flask.palletsprojects.com/en/latest/deploying/
[Flask-Babel_documentation]: https://python-babel.github.io/flask-babel/
[Kerko]: https://github.com/whiskyechobravo/kerko
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoStart]: https://github.com/whiskyechobravo/kerkostart
[venv]: https://docs.python.org/3.11/tutorial/venv.html
