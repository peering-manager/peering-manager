# Container Installation

## Installing a container engine
You can use any Container engine you want, for example [Podman](https://podman.io/) or
[Docker](https://www.docker.com/) as long as it understands the Docker file
format. The following explanations will focus on Docker.

=== "Debian 10"
	```no-highlight
	# apt update
	# apt install apt-transport-https ca-certificates curl gnupg lsb-release
	# curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
	# echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
	# apt update
	# apt install docker-ce docker-ce-cli containerd.io docker-compose
	# systemctl enable docker --now
	```

=== "CentOS 7 & 8"
	```no-highlight
	# yum install yum-utils
	# yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
	# yum install docker-ce docker-ce-cli containerd.io
	# systemctl enable docker --now
	```

You also need Git since we will clone a repository from GitHub. Install it with
`apt install git` or `yum install git` depending on your distribution.

## Getting the Compose file
We manage our files in a Git repository, clone it with `git clone https://github.com/peering-manager/docker.git`
to a location you want.
Then enter the directory with `cd`.

## Starting the containers
If you just want to check out Peering Manager it is sufficient to run
`docker-compose up -d`.
This will spin up the required Redis, PostgreSQL and nginx services for you.
After a moment you then can access the application at <http://localhost:8080>.

## Further configuration
When running in a production environment it is highly recommended to change
some settings. The settings files can be found in the `env` folder.
It is especially important to change passwords for Redis and PostgreSQL aswell
as the encryption key of Peering Manager.

`env/redis.env`:

| Variable	   | Usage			        |
|------------------|------------------------------------|
| `REDIS_PASSWORD` | Password for Redis key-value store |

`env/postgres.env`:

| Variable	      | Usage		      |
|---------------------|-----------------------|
| `POSTGRES_USER`     | Username for database |
| `POSTGRES_PASSWORD` | Password for database |
| `POSTGRES_DB`	      | Database name	      |

`env/peering-manager.env`:

| Variable	   | Usage					     |
|------------------|-------------------------------------------------|
| `SECRET_KEY`	   | Used for cryptopgraphic features		     |
| `BASE_PATH`	   | Set to path when Peering Manager is not at root |
| `TIME_ZONE`	   | Time Zone					     |
| `DB_NAME`	   | Database name				     |
| `DB_USER`	   | Username for database 			     |
| `DB_PASSWORD`	   | Password for database                           |
| `REDIS_PASSWORD` | Password for Redis key-value store              |
