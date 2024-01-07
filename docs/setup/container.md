# Container

## Container Engine

To run Peering Manager as a container, an engine such as
[Docker](https://www.docker.com/) or [Podman](https://podman.io/) needs to be
installed on the machine. It should work as long as it understands the Docker
file format. The following explanations will focus on Docker. Please refer to
the [documentation](https://docs.docker.com/engine/install/) for installation
guidelines.

You will need git as well as the Compose plugin for Docker to make use of what
is provided in the git repository.

## Getting The Compose File

A Dockerfile and Compose files are provided in an official repository. Clone
it locally on your machine using git, in a directory of your choice:


```no-highlight
git clone https://github.com/peering-manager/docker.git
```

## Starting Containers

If you just want to check out Peering Manager it is sufficient to run
`docker compose up -d`. This will spin up the required Redis, PostgreSQL and
all the Peering Manager processes. Keep in mind to use a
`docker-compose.override.yml` file to expose a port and also setup a proxy of
your choice.

## Further configuration

When running in a production environment it is highly recommended to change
some settings. The settings files can be found in the `env` folder. It is
especially important to change passwords for Redis and PostgreSQL as well as
the encryption key of Peering Manager.

`env/redis.env`:

| Variable         | Usage                              |
|------------------|------------------------------------|
| `REDIS_PASSWORD` | Password for Redis key-value store |

`env/postgres.env`:

| Variable            | Usage                 |
|---------------------|-----------------------|
| `POSTGRES_USER`     | Username for database |
| `POSTGRES_PASSWORD` | Password for database |
| `POSTGRES_DB`       | Database name         |

`env/peering-manager.env`:

| Variable         | Usage                                           |
|------------------|-------------------------------------------------|
| `SECRET_KEY`     | Used for cryptopgraphic features                |
| `BASE_PATH`      | Set to path when Peering Manager is not at root |
| `TIME_ZONE`      | Time Zone                                       |
| `DB_NAME`        | Database name                                   |
| `DB_USER`        | Username for database                           |
| `DB_PASSWORD`    | Password for database                           |
| `REDIS_PASSWORD` | Password for Redis key-value store              |
