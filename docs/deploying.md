# How to deploy

As there is a great diversity of operating systems, hosting environments, and
[WSGI servers], it is hard to provide universal and useful instructions for
setting up [KerkoApp] for use in production.

You can expect a procedure similar to that of any [Flask] application, and there
are many guides on the web covering this topic for various environments.

That said, you may refer to the guide below for step-by-step instructions. Even
if your environment is different from the one this guide was designed for, it
might provide you with some useful hints.

## Deploying on Ubuntu 20.04 or 22.04 with nginx and gunicorn

These instructions will detail the steps and configurations required to get
[KerkoApp] running on an Ubuntu 20.04 or 22.04 web server, using [Gunicorn] as
the WSGI container and [nginx] as a HTTP proxy.

The procedure is similar that of any Flask application, but KerkoApp-specific
steps are also covered here.

Install some required packages, including Python 3:

```bash
sudo apt install git nginx python3 python3-pip python3-venv
```

Create the user who will run the app:

```bash
sudo groupadd --system kerkoapp
sudo useradd --gid kerkoapp --shell /bin/bash --create-home --home-dir /home/kerkoapp --groups www-data kerkoapp
```

Switch to that user and clone the desired version of KerkoApp. If you want to
use version 1.0.0, for example, replace `VERSION` in the command below with
`1.0.0`:

```bash
sudo su kerkoapp
git clone --branch VERSION https://github.com/whiskyechobravo/kerkoapp.git ~/kerkoapp
```

Still as user `kerkoapp`, create a Python virtual environment and install the
Python packages required by KerkoApp:

```bash
python3 -m venv ~/venv
source ~/venv/bin/activate
pip3 install -r ~/kerkoapp/requirements/run.txt
pip3 install gunicorn
```

Always as user `kerkoapp`, create the `~/.secrets.toml` file. This is where you
will put secret keys that should only be known to your server. Its content
should look like the following:

```toml title=".secrets.toml"
SECRET_KEY = "MY_SECRET_KEY"
ZOTERO_API_KEY = "MY_ZOTERO_API_KEY"
```

You **must** set `SECRET_KEY` with a random string, and `ZOTERO_API_KEY` with an
appropriate value (see [configuration
parameters](config-params.md#zotero_api_key)).

Then create the `~/instance.toml` file. This file will contain settings that are
specific to your server, but are not secret. Its content should look like the
following:

```toml title="instance.toml"
LOGGING_HANDLER = "syslog"

[kerkoapp.proxy_fix]
enabled = true
x_for = 1
x_proto = 1
x_host = 1
x_port = 0
x_prefix = 0
```

We are enabling the `kerkoapp.proxy_fix` parameters because we will configure
nginx as a reverse proxy.

Then create the `~/config.toml` file. This file will contain general settings
for Kerko. You might have already tested KerkoApp on your desktop computer and
created such file. If so, you could just copy that file to your server. At the
very least it should contain the following settings:

```toml title="config.toml"
ZOTERO_LIBRARY_ID = "MY_ZOTERO_LIBRARY_ID"
ZOTERO_LIBRARY_TYPE = "MY_ZOTERO_LIBRARY_TYPE"

[kerko.meta]
title = "My Bibliography"
```

You **must** set `ZOTERO_LIBRARY_ID` and `ZOTERO_LIBRARY_TYPE` with appropriate
values (see [configuration parameters](config-params.md#zotero_library_id)) so
that Kerko can connect to your Zotero library.

It is not absolutely necessary to use three separate configuration files for
KerkoApp as we just did. You could, for example, have just `~/instance.toml` and
put all of the settings there. However, it is a good practice to split the
configuration, and that allows you to copy `config.toml` from or to other
machines, or even share it with other people, without worrying about leaking
secret keys or messing up your server-specific settings.

Once the configuration files are ready, Kerko should be able to talk to Zotero.
Have Kerko retrieve your Zotero library's data by running the following command:

```bash
flask --debug kerko sync
```

The `--debug` switch is optional. If you use it, some messages will give you an
better idea of the progress of the sync process. If you omit it, the command
will run silently unless there are warnings or errors.

Depending on the size of your library, this process can complete within less
than a minute or take an hour or more. Zotero throttles API requests to prevent
its servers from getting overloaded, so sometimes the process might seem to
freeze, but be patient and Kerko will resume synchronization a few minutes
later.

Now that synchronization works, configure the cron task that will synchronize
data from your Zotero library on a regular basis. Run the following command
(always from the `kerkoapp` user):

```bash
crontab -e
```

That will launch the default `nano` editor. Add the following line at the very
bottom, then save the file and exit the editor:

``` title="crontab"
10 4 * * * cd /home/kerkoapp/kerkoapp && /home/kerkoapp/venv/bin/flask kerko sync
```

That will synchronize the data once a day, at 4:10am. You may specify a
different time, of course.

Now exit from the `kerkoapp` user's shell, and go back to your usual sudoer
account to finish the installation.

Configure a socket that will let Gunicorn to speak with nginx. As the superuser,
create the `/etc/systemd/system/kerkoapp.socket` file, with the following
content:

``` title="kerkoapp.socket"
[Unit]
Description=KerkoApp socket

[Socket]
ListenStream=/run/kerkoapp.socket

[Install]
WantedBy=kerkoapp.target
```

Configure a service that will run Gunicorn. As the superuser, create the
`/etc/systemd/system/kerkoapp.service` file, with the following content:

``` title="kerkoapp.service"
[Unit]
Description=KerkoApp daemon
Requires=kerkoapp.socket
After=network.target

[Service]
WorkingDirectory=/home/kerkoapp/kerkoapp
ExecStart=/home/kerkoapp/venv/bin/gunicorn wsgi:app --name kerkoapp --user kerkoapp --group www-data --workers 4 --log-level warning --error-logfile - --access-logfile - --bind unix:/run/kerkoapp.socket
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Reload the systemd configurations, then enable and start the new service by
running the following commands:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kerkoapp.socket
sudo systemctl enable kerkoapp.service
sudo systemctl start kerkoapp.socket
```

You can check whether the socket is active with this command:

```bash
sudo systemctl status kerkoapp.socket
```

If it shows up as 'active (listening)', you may now verify that it triggers the
service:

```bash
curl --unix-socket /run/kerkoapp.socket localhost
sudo systemctl status kerkoapp.service
```

The `curl` command should output some HTML, and the `systemctl` command should
now show the KerkoApp daemon as 'active (running)'.

If either the socket or the service doesn't work, you might want to check for
errors in the log:

```bash
sudo journalctl --unit=kerkoapp
```

Once all of the above works, configure nginx to pass requests to Gunicorn. As
the superuser, create the `/etc/nginx/sites-available/kerkoapp.conf` file with
the following content, replacing `example.com` with your actual domain name:

``` title="kerkoapp.conf"
server {
    listen 80;
    server_name example.com;

    location / {
        proxy_redirect off;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-Proto $scheme;

        if (!-f $request_filename) {
            proxy_pass http://unix:/run/kerkoapp.socket;
            break;
        }
    }
}
```

Enable the site by running the following command:

```bash
sudo ln -s /etc/nginx/sites-available/kerkoapp.conf /etc/nginx/sites-enabled/
```

Have nginx test the configuration:

```bash
sudo nginx -t
```

If the command reports the configuration test as successful, reload nginx to
make the configuration changes effective:

```bash
sudo service nginx reload
```

You should now be able to view your KerkoApp site at http://example.com!

The nginx configuration above will serve the application using the HTTP
protocol. As for any website, HTTPS is strongly recommended. That will require
that you install a SSL certificate and configure nginx to use it; that exercise
is left to the reader.

!!! warning "Changing the configuration can be disruptive"

    Making any change to a configuration file requires that you at least restart
    the application afterwards for the change to become effective.

    Moreover, some parameters have an effect on the structure of the cache or
    the search index that Kerko depends on. Changing this kind of parameter may
    require that you rebuild either. Refer to the [documentation of the
    parameter](config-params.md) to check if specific actions need to be taken
    after a change.

    The commands below, for example, will allow you to clean and rebuild the
    search index, and to restart KerkoApp:

    ```bash
    sudo -iu kerkoapp bash -c 'cd /home/kerkoapp/kerkoapp && /home/kerkoapp/venv/bin/flask kerko clean index'
    sudo -iu kerkoapp bash -c 'cd /home/kerkoapp/kerkoapp && /home/kerkoapp/venv/bin/flask kerko sync'
    sudo systemctl stop kerkoapp.socket
    sudo systemctl start kerkoapp.socket
    ```


## Submitting your sitemap to search engines

Kerko generates an [XML Sitemap] that can help search engines discover your
bibliographic records.

The path of the sitemap is `BASE_URL/sitemap.xml`, where `BASE_URL` should be
replaced with the protocol, domain, port, and Kerko URL path prefix that are
relevant to your installation, e.g.,
`https://example.com/bibliography/sitemap.xml`.

Different search engines may have different procedures for submitting sitemaps
([Google](https://developers.google.com/search/docs/advanced/sitemaps/build-sitemap#addsitemap),
[Bing](https://www.bing.com/webmasters/help/Sitemaps-3b5cf6ed),
[Yandex](https://yandex.com/support/webmaster/indexing-options/sitemap.html)).

However, a standard method consists in adding a `Sitemap` directive to a
`robots.txt` file served at the root of your site, to tell web crawlers where to
find your sitemap. For example, one might add the following line to
`robots.txt`:

```
Sitemap: https://example.com/bibliography/sitemap.xml
```

A `robots.txt` file can have multiple `Sitemap` directives, thus the Kerko
sitemap can be specified alongside any other sitemaps you might already have.



[Flask]: https://flask.palletsprojects.com/en/latest/deploying/
[GUnicorn]: https://gunicorn.org/
[KerkoApp]: https://github.com/whiskyechobravo/kerkoapp
[nginx]: https://nginx.org/en/docs/
[WSGI servers]: https://flask.palletsprojects.com/en/latest/deploying/
[XML Sitemap]: https://www.sitemaps.org/
