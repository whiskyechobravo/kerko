# Getting started

For getting started with Kerko, we recommend that you use KerkoApp, either with
a "standard" installation, or with a Docker installation. However, if KerkoApp
does not work for your use case, we also have instructions for [creating a
custom application](#creating-a-custom-application).


## Getting started with KerkoApp

To install KerkoApp, you may choose between a "standard" installation and a
Docker installation. Just go with the option you feel most comfortable with. If
you don't know Docker, you should be fine with the standard installation. But if
you prefer not to touch any Python-related thing, perhaps the Docker
installation will suit you best.


### Standard installation

This procedure requires that you have [Python], [pip], and [Git] installed on
your computer.

1. The first step is to install the software. Use the following commands:

    === "POSIX"
        ```bash
        git clone https://github.com/whiskyechobravo/kerkoapp.git
        cd kerkoapp
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements/run.txt
        ```

    === "Windows"
        ```
        git clone https://github.com/whiskyechobravo/kerkoapp.git
        cd kerkoapp
        python -m venv venv
        venv\Scripts\activate.bat
        pip install -r requirements\run.txt
        ```

    This will install all packages required by Kerko and KerkoApp within a
    [virtual environment][venv].

2. Copy the `sample.env` file to `.env` in the same directory. Open `.env` in a
   text editor to assign proper values to the variables outlined below.

    - `KERKOAPP_SECRET_KEY`: This variable is required for generating secure
      tokens in web forms. It should have a hard to guess, and should really
      remain secret. For this reason, never add your `.env` file to a code
      repository.
    - `KERKOAPP_ZOTERO_API_KEY`: Your Zotero API key, as [created on
      zotero.org](https://www.zotero.org/settings/keys/new). We recommend that
      you create a read-only API key, as Kerko does not need to write to your
      library.
    - `KERKOAPP_ZOTERO_LIBRARY_ID`: The identifier of the Zotero library to get
      data from. For a personal library this value is your _userID_, as found on
      https://www.zotero.org/settings/keys (you must be logged-in). For a group
      library this value is the _groupID_ of the library, as found in the URL of
      the library (e.g., the _groupID_ of the library at
      https://www.zotero.org/groups/2348869/kerko_demo is `2348869`).
    - `KERKOAPP_ZOTERO_LIBRARY_TYPE`: The type of library to get data from,
      either `'user'` for a personal library, or `'group'` for a group library.

3. Copy the `sample.config.toml` file to `config.toml` in the same directory.
   You do not need to edit the latter at this point, but later on this is where
   you will change configuration options.

4. Have KerkoApp synchronize your data from zotero.org:

    ```bash
    flask --debug kerko sync
    ```

    If you have a large Zotero library and/or large file attachments, that
    command may take a while to complete. Wait until the command finishes. In
    production use, this command is usually added to the crontab file for regular
    execution.

    The `--debug` switch is optional. If you use it, some messages will give you
    an idea of the sync process' progress. If you omit it, the command will run
    silently unless there are warnings or errors.

    To list all commands provided by Kerko:

    ```bash
    flask kerko --help
    ```

5. Run KerkoApp:

    ```bash
    flask --debug run
    ```

6. Open http://localhost:5000/ in your browser and explore the bibliography!

!!! warning "Not suitable for production"

    The above procedure relies on Flask's built-in server, which is not
    suitable for production. For production use, you should consider better
    options, such as the [WSGI servers suggested in Flask's
    documentation][Flask_production].

!!! info "Running your installed application"

    To launch the application again in a future session, make sure to reactivate the
    virtual environment first. The command sequence should look like:

    === "POSIX"
        ```bash
        cd kerkoapp
        source venv/bin/activate
        flask --debug run
        ```

    === "Windows"
        ```
        cd kerkoapp
        venv\Scripts\activate.bat
        flask --debug run
        ```


### Docker installation

This procedure requires that [Docker] is installed on your computer.

1. Copy the `Makefile`, `sample.env`, `sample.config.toml` files from
   [KerkoApp's repository][KerkoApp] to an empty directory on your computer.

2. Rename your `sample.env` copy to `.env`. Open `.env` in a text editor to
   assign proper values to the variables outlined below.

    - `KERKOAPP_SECRET_KEY`: This variable is required for generating secure
      tokens in web forms. It should have a hard to guess, and should really
      remain secret. For this reason, never add your `.env` file to a code
      repository.
    - `KERKOAPP_ZOTERO_API_KEY`: Your Zotero API key, as [created on
      zotero.org](https://www.zotero.org/settings/keys/new). We recommend that
      you create a read-only API key, as Kerko does not need to write to your
      library.
    - `KERKOAPP_ZOTERO_LIBRARY_ID`: The identifier of the Zotero library to get
      data from. For a personal library this value is your _userID_, as found on
      https://www.zotero.org/settings/keys (you must be logged-in). For a group
      library this value is the _groupID_ of the library, as found in the URL of
      the library (e.g., the _groupID_ of the library at
      https://www.zotero.org/groups/2348869/kerko_demo is `2348869`).
    - `KERKOAPP_ZOTERO_LIBRARY_TYPE`: The type of library to get data from,
      either `'user'` for a personal library, or `'group'` for a group library.
    - `MODULE_NAME`: This variable is required for running the application with
      the provided Docker image. It specifies the Python module to be imported
      by Gunicorn. You should not need to change the value that is provided in
      `sample.env`.

    !!! warning

        Do not assign a value to the `KERKOAPP_DATA_DIR` variable. If you do, the
        volume bindings defined within the `Makefile` will not be of any use to the
        application running within the container.

3. Rename your `sample.config.toml` copy to `config.toml`. You do not need to
   edit the latter at this point, but later on this is where you will change
   configuration options.

4. Pull the latest KerkoApp Docker image. In the same directory as the
   `Makefile`, run the following command:

    ```bash
    docker pull whiskyechobravo/kerkoapp
    ```

5. Have KerkoApp retrieve your bibliographic data from zotero.org:

    ```bash
    make kerkosync
    ```

    If you have a large Zotero library and/or large file attachments, that
    command may take a while to complete. Wait until the command finishes.

    Kerko's index will be stored in the `data` subdirectory.

6. Run KerkoApp:

    ```
    make run
    ```

7. Open http://localhost:8080/ in your browser and explore the bibliography!

The provided `Makefile` is only an example on how to run a dockerized KerkoApp.
For production use, you might want to build your own image.

For full documentation on how to run Docker containers, including port mapping
and volume binding, see the [Docker documentation][Docker_docs].


## Creating a custom application

This section should help you understand the minimal steps required for getting
Kerko to work within a custom Flask application.

!!! tip

    For a ready-to-use standalone application, you will be better off using
    [KerkoApp](#getting-started-with-kerkoapp) instead.

Some familiarity with [Flask] should help you make more sense of the
instructions, but should not be absolutely necessary for getting them to work.
Let's now build a minimal app:

1. Create an empty directory `myapp` where your application reside.

2. Install Kerko in a new [virtual environment][venv]:

    === "POSIX"
        ```bash
        cd myapp
        python -m venv venv
        source venv/bin/activate
        pip install kerko
        ```

    === "Windows"
        ```
        cd myapp
        python -m venv venv
        venv\Scripts\activate.bat
        pip install kerko
        ```

3. In the `myapp` directory, create a file named `.env`, where variables
   required by Kerko will be configured, with content such as the example below:

    ```sh
    MYAPP_SECRET_KEY="your-random-secret-key"
    MYAPP_ZOTERO_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxx"
    MYAPP_ZOTERO_LIBRARY_ID="9999999"
    MYAPP_ZOTERO_LIBRARY_TYPE="group"
    ```

    Replace each value with a proper one. The meaning of each variable is
    outlined below:

    - `MYAPP_SECRET_KEY`: This variable is required for generating secure tokens
      in web forms. It should have a hard to guess, and should really remain
      secret. For this reason, never add your `.env` file to a code repository.
    - `MYAPP_ZOTERO_API_KEY`: Your Zotero API key, as [created on
      zotero.org](https://www.zotero.org/settings/keys/new). We recommend that
      you create a read-only API key, as Kerko does not need to write to your
      library.
    - `MYAPP_ZOTERO_LIBRARY_ID`: The identifier of the Zotero library to get
      data from. For a personal library this value is your _userID_, as found on
      https://www.zotero.org/settings/keys (you must be logged-in). For a group
      library this value is the _groupID_ of the library, as found in the URL of
      the library (e.g., the _groupID_ of the library at
      https://www.zotero.org/groups/2348869/kerko_demo is `2348869`).
    - `MYAPP_ZOTERO_LIBRARY_TYPE`: The type of library to get data from, either
      `'user'` for a personal library, or `'group'` for a group library.

    A `.env` file is a good place to store an application's secrets. It is good
    practice to keep this file only on the machine where the application is
    hosted, and to never push it to a code repository.

4. Create a file named `wsgi.py` with the following content:

    ```python title="wsgi.py" linenums="1"
    import kerko
    from flask import Flask
    from flask_babel import Babel
    from flask_bootstrap import Bootstrap4
    from kerko.composer import Composer
    from kerko.config_helpers import config_set, config_update, validate_config

    app = Flask(__name__)
    ```

    This imports required modules and creates the Flask application object
    (`app`).

    ```python title="wsgi.py" linenums="9"
    app.config.from_prefixed_env(prefix='MYAPP')
    config_update(app.config, kerko.DEFAULTS)
    ```

    This loads configuration settings from the `.env` file, and loads Kerko's
    default configuration.

    ```python title="wsgi.py" linenums="11"
    # Make changes to the Kerko configuration here, if desired.
    config_set(app.config, 'kerko.meta.title', 'My App')
    ```

    This uses Kerko's `config_set` function to assign the title that users of
    the web application will see. The same function could be used again right
    there to set any of Kerko's [configuration options](config.md).

    ```python title="wsgi.py" linenums="13"
    validate_config(app.config)
    app.config['kerko_composer'] = Composer(app.config)
    ```

    The ensures that the configuration has been set in a valid format, and then
    creates the `kerko_composer` object. This object provides key elements
    needed by Kerko, e.g., fields for display and search, facets for filtering.
    Using methods of the `Composer` class, your application may alter this
    object if needed (but only at configuration time, thus right here after its
    creation), to add, remove or alter fields, facets, sort options, search
    scopes, record download formats, or badges.

    ```python title="wsgi.py" linenums="15"
    babel = Babel(app)
    bootstrap = Bootstrap4(app)
    ```

    This initializes the Flask-Babel and Bootstrap-Flask extensions (see the
    respective docs of [Flask-Babel][Flask-Babel_documentation] and
    [Bootstrap-Flask][Bootstrap-Flask_documentation] for more details).

    ```python title="wsgi.py" linenums="17"
    app.register_blueprint(kerko.blueprint, url_prefix='/bibliography')
    ```

    Finally, the Kerko blueprint is registered with the application object. The
    `url_prefix` argument defines the base path for every URL provided by Kerko.

    !!! note

        The full code example is available [on GitHub][KerkoStart].

5. In the same directory as `wsgi.py` with your virtual environment active, run
   the following shell commands:

    ```bash
    flask --debug kerko sync
    ```

    If you have a large Zotero library and/or large file attachments, that
    command may take a while to complete. Wait until the command finishes. In
    production use, this command is usually added to the crontab file for regular
    execution.

    The `--debug` switch is optional. If you use it, some messages will give you
    an idea of the sync process' progress. If you omit it, the command will run
    silently unless there are warnings or errors.

    To list all commands provided by Kerko:

    ```bash
    flask kerko --help
    ```

6.  Run your application:

    ```bash
    flask --debug run
    ```

7. Open http://127.0.0.1:5000/bibliography/ in your browser and explore the
   bibliography!

You have just built a really minimal application for Kerko. However, if you are
looking at developing a custom Kerko application, we recommend that you still
look at [KerkoApp] for a more advanced starting point. While still small,
KerkoApp adds some structure as well as features such as TOML configuration
files, translations loading, a syslog logging handler, and error pages.


[Bootstrap-Flask_documentation]: https://bootstrap-flask.readthedocs.io/en/latest/basic.html
[Docker_docs]: https://docs.docker.com/
[Docker]: https://www.docker.com/
[Flask_production]: https://flask.palletsprojects.com/en/latest/deploying/
[Flask-Babel_documentation]: https://python-babel.github.io/flask-babel/
[Flask]: https://pypi.org/project/Flask/
[Git]: https://git-scm.com/
[Kerko]: https://github.com/whiskyechobravo/kerko
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoStart]: https://github.com/whiskyechobravo/kerkostart
[pip]: https://pip.pypa.io/
[Python]: https://www.python.org/
[venv]: https://docs.python.org/3.11/tutorial/venv.html
