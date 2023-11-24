# Getting started

For getting started with Kerko, we recommend that you use [KerkoApp]. However,
if KerkoApp is not suited to your use case, we also have instructions for
[creating a custom application](#creating-a-custom-application).


## Getting started with KerkoApp

To install KerkoApp, you may choose between a "standard" installation and a
Docker installation. Just go with the option you feel most comfortable with. If
you don't know Docker, you should be fine with the standard installation. But if
you prefer to keep your distance from Python-related stuff, perhaps the Docker
installation will suit you best.


### Standard installation

This procedure requires that you have [Python], [pip], and [Git] installed on
your computer.

1. The first step is to install the desired version of KerkoApp. You may check
   the list of [available versions][KerkoApp versions], but make sure to choose
   one that matches the documentation version you are currently reading! For
   version 1.0.0, for example, replace `VERSION` with `1.0.0` in the commands
   below:

    === "POSIX"
        ```bash
        git clone --branch VERSION https://github.com/whiskyechobravo/kerkoapp.git
        cd kerkoapp
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements/run.txt
        ```

    === "Windows"
        ```
        git clone --branch VERSION https://github.com/whiskyechobravo/kerkoapp.git
        cd kerkoapp
        python -m venv venv
        venv\Scripts\activate.bat
        pip install -r requirements\run.txt
        ```

    This will install all packages required by Kerko and KerkoApp within a
    [virtual environment][venv].

2. Copy the `sample.secrets.toml` file to `.secrets.toml` in the same directory.
   Open `.secrets.toml` in a text editor to assign proper values to the
   parameters outlined below:

    - `SECRET_KEY`: This parameter is required for generating secure tokens in
      web forms. It should have a hard to guess value, and should really remain
      secret. For this reason, never add your `.secrets.toml` file to a code
      repository.
    - `ZOTERO_API_KEY`: Your Zotero API key. [See API key creation
      instructions](config-params.md#zotero_api_key).

3. Copy the `sample.config.toml` file to `config.toml` in the same directory.
   Open `config.toml` in a text editor to assign proper values to the parameters
   outlined below:

    - `ZOTERO_LIBRARY_ID`: The identifier of the Zotero library to get
      data from. For a personal library the value is your _userID_, as found on
      https://www.zotero.org/settings/keys (you must be logged-in). For a group
      library this value is the _groupID_ of the library, as found in the URL of
      the library (e.g., the _groupID_ of the library at
      https://www.zotero.org/groups/2348869/kerko_demo is `"2348869"`).
    - `ZOTERO_LIBRARY_TYPE`: The type of library to get data from,
      either `"user"` for a personal library, or `"group"` for a group library.

    You do not need to edit other parameters at this point, but later on
    `config.toml` is where your configuration changes will take place.

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

6. Open <http://localhost:5000/> in your browser and explore the bibliography!

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

!!! warning "Not suitable for production"

    The above procedure relies on Flask's built-in server, which is not
    suitable for production. For production use, you should consider better
    options such as the [WSGI servers suggested in the Flask
    documentation][Flask production].


### Docker installation

This procedure requires that [Docker] is installed on your computer.

1. Copy the `Makefile`, `sample.secrets.toml`, and `sample.config.toml` files
   from the most recent stable branch of the [KerkoApp] repository (e.g.
   <https://github.com/whiskyechobravo/kerkoapp/tree/stable/1.0.x>) to an empty
   directory on your computer.

2. Under the same directory, create a subdirectory named `instance`. This is
   where you will put your configuration files, and where Kerko will save its
   data.

3. Copy `sample.secrets.toml` as `.secrets.toml` into the `instance`
   subdirectory. Open `instance/.secrets.toml` in a text editor to assign proper
   values to the configuration parameters outlined below:

    - `SECRET_KEY`: This parameter is required for generating secure tokens in
      web forms. It should have a hard to guess value, and should really remain
      secret. For this reason, never add your `.secrets.toml` file to a code
      repository.
    - `ZOTERO_API_KEY`: Your Zotero API key. [See API key creation
      instructions](config-params.md#zotero_api_key).

4. Copy `sample.config.toml` as `config.toml` into the `instance` subdirectory.
   Open `instance/config.toml` in a text editor to assign proper values to the
   configuration parameters outlined below:

    - `ZOTERO_LIBRARY_ID`: The identifier of the Zotero library to get
      data from. For a personal library the value is your _userID_, as found on
      https://www.zotero.org/settings/keys (you must be logged-in). For a group
      library this value is the _groupID_ of the library, as found in the URL of
      the library (e.g., the _groupID_ of the library at
      https://www.zotero.org/groups/2348869/kerko_demo is `"2348869"`).
    - `ZOTERO_LIBRARY_TYPE`: The type of library to get data from,
      either `"user"` for a personal library, or `"group"` for a group library.

    It should not be necessary to change other settings at this point. You can
    always come back later to this file in order to configure KerkoApp to your
    liking. For now, we suggest that you proceed to the next step and get it
    running.

5. From the same directory as `Makefile`, run KerkoApp:

    ```bash
    make run
    ```

    This command should do many things:

    - Download and install the latest KerkoApp Docker image from DockerHub.
    - Run the Docker container to have KerkoApp retrieve your data from
      zotero.org.
    - Run the Docker container to launch the KerkoApp server.

    If your configuration files have errors, the process may be interrupted; if
    that happens, retry `make run` after correcting the problem. Otherwise, if
    all goes well, you will only have to wait a bit for the data synchronization
    process to complete. This may take a long time if you have a large Zotero
    library.

    Kerko's data will be stored in the `instance` subdirectory.

    KerkoApp should launch once the synchronization process has completed. When
    you see the following message in the terminal, proceed to the next step:

    ```
    [INFO] Listening at: http://0.0.0.0:80
    ```

6. Open <http://localhost:8080/> in your browser and explore the bibliography!

To stop the KerkoApp server, press ++ctrl+c++ in the terminal where the
container is running.

The next time you execute `make run`, it will find that the image has been
already been downloaded and the data synchronized, and thus it will just launch
the server.

!!! tip "Using the Kerko command line interface (CLI) with Docker"

    To use Kerko's command line interface, enter this command from the same
    directory as `Makefile`:

    ```bash
    make shell
    ```

    This will start an interactive shell within the Docker container. From
    there, you may run Kerko commands to clean Kerko's data, to synchronize
    from zotero.org, or to check Kerko's configuration. The command below lists
    all the commands provided by Kerko:

    ```bash
    flask kerko --help
    ```

    To exit the interactive shell, enter `exit` or press ++ctrl+d++ at the
    command prompt.

!!! tip "Building a Docker image for production"

    The `Makefile` is just an example that shows how to build and interact with
    a dockerized KerkoApp. For production use, you might want to clone the full
    [KerkoApp repository][KerkoApp], make some changes to its `Dockerfile`, and
    build your own image.

    For full documentation on how to run Docker containers, including port mapping
    and volume binding, see the [Docker documentation].


## Creating a custom application

This section should help you understand the minimal steps required for setting
up Kerko within a custom Flask application.

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

3. In the `myapp` directory, create a file named `.env`, where parameters
   required by Kerko will be configured, with content such as the example below:

    ```sh
    MYAPP_SECRET_KEY="your-random-secret-key"
    MYAPP_ZOTERO_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxx"
    MYAPP_ZOTERO_LIBRARY_ID="9999999"
    MYAPP_ZOTERO_LIBRARY_TYPE="group"
    ```

    Replace each value with a proper one. The meaning of each parameter is
    outlined below:

    - `MYAPP_SECRET_KEY`: This parameter is required for generating secure
      tokens in web forms. It should have a hard to guess value, and should
      really remain secret. For this reason, never add your `.env` file to a
      code repository.
    - `MYAPP_ZOTERO_API_KEY`: Your Zotero API key. [See API key creation
      instructions](config-params.md#zotero_api_key).
    - `MYAPP_ZOTERO_LIBRARY_ID`: The identifier of the Zotero library to get
      data from. For a personal library the value is your _userID_, as found on
      https://www.zotero.org/settings/keys (you must be logged-in). For a group
      library this value is the _groupID_ of the library, as found in the URL of
      the library (e.g., the _groupID_ of the library at
      https://www.zotero.org/groups/2348869/kerko_demo is `"2348869"`).
    - `MYAPP_ZOTERO_LIBRARY_TYPE`: The type of library to get data from,
      either `"user"` for a personal library, or `"group"` for a group library.

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

    The above imports required modules and creates the Flask application object
    (`app`). Then, load the default Kerko configuration, and update it from
    values set in `.env`:

    ```python title="wsgi.py" linenums="9"
    # Initialize app configuration with Kerko's defaults.
    config_update(app.config, kerko.DEFAULTS)

    # Update app configuration from environment variables.
    app.config.from_prefixed_env(prefix="MYAPP")
    ```

    Next, adjust general application parameters to your liking. For example, we
    can use the `config_set` function to set the main title of the web
    application to `"My App"`. This function can be called each time you wish to
    set a [configuration option](config-basics.md).

    ```python title="wsgi.py" linenums="14"
    # Make changes to the Kerko configuration here, if desired.
    config_set(app.config, "kerko.meta.title", "My App")
    ```

    Next, have Kerko parse and validate the configuration. Then create the
    `kerko_composer` object, which provides key elements needed by Kerko such as
    the fields to display and search, and the facets made available for
    filtering:

    ```python title="wsgi.py" linenums="16"
    # Validate configuration and save its parsed version.
    parse_config(app.config)

    # Initialize the Composer object.
    app.config["kerko_composer"] = Composer(app.config)

    # Make changes to the Kerko composer object here, if desired.
    ```

    Using methods of the `Composer` class, your application could alter the
    `kerko_composer` object if needed, to add, remove or alter fields, facets,
    sort options, search scopes, record download formats, or badges.

    Finally, initialize extensions required by Kerko (see the respective
    documentations of [Flask-Babel][Flask-Babel documentation] and
    [Bootstrap-Flask][Bootstrap-Flask documentation] for more details), and
    register the Kerko blueprint with the application object:

    ```python title="wsgi.py" linenums="23"
    babel = Babel(app)
    bootstrap = Bootstrap4(app)

    app.register_blueprint(kerko.make_blueprint(), url_prefix="/bibliography")
    ```

    The `url_prefix` argument given above defines the base path for every URL
    provided by Kerko.

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

7. Open <http://127.0.0.1:5000/bibliography/> in your browser and explore the
   bibliography!

You have just built a really minimal application for Kerko. However, if you are
looking at developing a custom Kerko application, we recommend that you still
look at [KerkoApp] for a more advanced starting point. While still small,
KerkoApp adds some structure as well as features such as TOML configuration
files, translations loading, a syslog logging handler, and error pages.


[Bootstrap-Flask documentation]: https://bootstrap-flask.readthedocs.io/en/latest/basic.html
[Docker documentation]: https://docs.docker.com/
[Docker]: https://www.docker.com/
[Flask production]: https://flask.palletsprojects.com/en/latest/deploying/
[Flask-Babel documentation]: https://python-babel.github.io/flask-babel/
[Flask]: https://pypi.org/project/Flask/
[Git]: https://git-scm.com/
[Kerko]: https://github.com/whiskyechobravo/kerko
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[KerkoApp versions]: https://github.com/whiskyechobravo/kerkoapp/tags
[KerkoStart]: https://github.com/whiskyechobravo/kerkostart
[pip]: https://pip.pypa.io/
[Python]: https://www.python.org/
[venv]: https://docs.python.org/3.11/tutorial/venv.html
