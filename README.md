# Getting started with Zuul on Fedora

## Upstream documentation

The upstream documentation is available at: https://zuul-ci.org/docs/zuul/index.html

## Installation

This section describes the installation process of the minimal set of Zuul components to
get a working Zuul deployment. Please refer to the upstream documentation for advanced
setup.

Zuul requires a Web, a Zookeeper and SQL server running. This documentation covers all the step
to bootstrap Zuul.

### Install and setup Zookeeper

This process describes the minimal steps to get a Zookeeper service running. You
should refer to the Zookeeper documentation to get a production setup if needed.

```
$ mkdir /tmp/zookeeper && cd /tmp/zookeeper
$ curl -OL https://downloads.apache.org/zookeeper/zookeeper-3.6.1/apache-zookeeper-3.6.1-bin.tar.gz
$ tar -xvzf apache-zookeeper-3.6.1-bin.tar.gz
$ cp apache-zookeeper-3.6.1-bin/conf/zoo_sample.cfg apache-zookeeper-3.6.1-bin/conf/zoo.cfg
$ sudo apache-zookeeper-3.6.1-bin/bin/zkServer.sh start
```

### Install and setup postgresql

This process describes the minimal steps to get a postgres service running. You
should refer to the postgrres documentation to get a production setup if needed.

```
$ sudo dnf install -y posgresql python3-psycopg2
$ su - postgres
$ psql
  ALTER USER postgres WITH PASSWORD 'mypassword';
$ createdb --owner=postgres zuul
$ exit
```

Update the local access setting:

```
$ sudo sed -i /var/lib/pgsql/data/pg_hba.conf 's/127.0.0.1/32            ident/127.0.0.1/32            md5/'
$ sudo systemctl restart posgreql
```

Validate server connection by running:

```
$ psql -h 127.0.0.1 -U postgres -W zuul
```

### Install Zuul components

To install the packages run:

```
$ sudo dnf install zuul-scheduler zuul-executor zuul-web zuul-webui
```

### Update the zuul configuration to define the sql connection

In /etc/zuul/zuul.conf add the following:

```
[connection sqlreporter]
driver=sql
dburi=postgresql://postgres:mypassword@127.0.0.1:5432/zuul
```

### Setup Ansible virtual environment for the Zuul executor

The Zuul executor is the component in charge of running Zuul Jobs. A Zuul job is
a set of Ansible playbook. The Zuul executor supports multiple version of Ansible.
Zuul provides a tool to manage the Ansible virtual environments. To initialize them
run:

```
$ sudo -u zuul bash -c "cd && zuul-manage-ansible -u -r /var/lib/zuul/ansible-bin" 
```

### Build the Zuul web UI

The Zuul web UI is a React application. The Zuul packaging provides the source code of
the application. The following process describe how to compile the source to get a
production build:

```
$ curl --silent --location https://dl.yarnpkg.com/rpm/yarn.repo | sudo tee /etc/yum.repos.d/yarn.repo
$ sudo dnf install yarn
$ cd /usr/share/zuul-ui/
$ yarn install
$ REACT_APP_ZUUL_API='<api_url>' yarn build
```

Replace <api_url> by the URL where the zuul-web API is listening.

### Start the scheduler and executor

To do so run:

```
$ sudo -u zuul bash -c "ssh-keygen -t rsa -N '' -f /var/lib/zuul/.ssh/id_rsa"
$ sudo systemctl start zuul-scheduler
$ sudo systemctl start zuul-executor
```

The services logs are available into /var/log/zuul/zuul.log.

### Setup the web API

Install Apache:

```
$ sudo dnf install httpd
$ setsebool -P httpd_can_network_connect on
```

Then setup the reverve proxy by adding to /etc/httpd/conf.d/zuul.conf the
following content:

```
RewriteEngine on
RewriteRule ^/api/tenant/(.*)/console-stream ws://localhost:9000/api/tenant/$1/console-stream [P]
RewriteRule ^/(.*)$ http://localhost:9000/$1 [P]
```

Reload Apache:

```
$ sudo systemctl relead httpd
```

Finally start the zuul-web process

```
$ sudo systemctl start zuul-web
```

Validate the direct access to the API by running:

```
$ curl http://localhost:9000/api/tenants
```

Validate the access to the API via the reverse proxy:

```
$ curl http://<site_url>/api/tenants
```

## Run a first Zuul job

In this section, you'll find the steps to get a first periodic job running.

Please note that, this is a really basic configuration to ensure the services are working
as expected. To go further, please refer to the Zuul documentation to learn how to connect
Zuul to Code Review systems such as Github, Gerrit, Pagure. This demo uses the local system
to run jobs but this has serious limitation and should not be used in production.
Thus Nodepool must be used as the nodes and containers provider for Zuul.
Nodepool supports various cloud providers. Nodepool is packaged into Fedora and here is
its documentaion: https://zuul-ci.org/docs/nodepool/

### Prepare a Git repository to host the CI configuration

We need to prepare a local Git repository to host the pipelines and jobs configuration.

Follow the process below:

```
$ git init /home/fedora/zuul-config
```

In /home/fedora/zuul-config/.zuul.yaml add the following content:

```
- pipeline:
    name: periodic
    post-review: true
    description: Jobs in this queue are triggered every minute.
    manager: independent
    precedence: low
    trigger:
      timer:
        - time: '* * * * *'
    success:
      sqlreporter:
    failure:
      sqlreporter:

- job:
    name: my-noop
    description: Minimal working job
    parent: null
    run: my-noop.yaml

- project:
    periodic:
      jobs:
        - my-noop
```

Create the /home/fedora/zuul-config/my-noop.yaml and add the following content:

```
---
- hosts: localhost
  tasks:
    - name: List working directory
      command: ls -al {{ ansible_user_dir }}
    - name: Sleep 30 seconds
      wait_for:
        timeout: 30
```

Then commit the configuration by running:

```
$ cd /home/fedora/zuul-config/
$ git config user.name "John Doe"
$ git config user.email "john@localhost"
$ git add -A .
$ git commit -m"Init demo config"
```

### Run a Git deamon to serve the config repository

```
$ dulwich web-daemon -l 0.0.0.0 /
```

### Add the new connection in the Zuul configuration

In /etc/zuul/zuul.conf add the following:

```
[connection local_git]
driver=git
baseurl=http://localhost:8000/home/fedora
poll_delay=300
```

### Setup the Zuul tenant configuration file

In /etc/zuul/main.yaml add the following:

```
- tenant:
    name: default
    source:
      local_git:
        config-projects:
          - zuul-config
```

### Restart the Zuul services

```
$ sudo systemctl restart zuul-*
```

### Verify the job executed periodically

Run the following command to access the builds API endpoint and ensure the
my-noop job run as expected every minutes w/o errors.

```
$ curl http://<host>/api/tenant/default/builds | python -m json.tool
```

Access the build page, where you should see the periodic job my-noop runs

```
http://<host>/t/default/builds
```
