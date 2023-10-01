# Ansible

With [Ansible](https://github.com/ansible/ansible) you can get the same results
as with the manual setup but fully automatic and reproducible.
However it is missing some features, for example it is not able to install with
`nginx` or `uWSGI`.

## Installation
Since Ansible runs on your local machine, the available installation methods
differ depending on your operating system, so please have a look on the official
[installation instructions](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible-on-specific-operating-systems).
If you are on Windows, we recommend you to use [WSL](https://docs.microsoft.com/de-de/windows/wsl/).

!!! attention
    Ansible is an advanced topic which can get quite complex.
    If you have never used it before, we recommend you to take a look at a
    [tutorial](https://docs.ansible.com/ansible/latest/user_guide/intro_getting_started.html) first.

Then get the Ansible role for Peering Manager by running `ansible-galaxy install gmazoyer.peering_manager`.
Later updates can be installed with `ansible-galaxy install gmazoyer.peering_manager --force`.
The role will install and configure Python, PostgreSQL, Redis, Apache and
Peering Manager on Debian or Ubuntu.

!!! attention
    When the Ansible remote user is not root, the package `acl` is required
    and has to be installed before running this role.
    
    Please also make sure that the choosen database locale is already
    installed or this role will fail.
    This could be done with [community.general.locale_gen](https://docs.ansible.com/ansible/latest/collections/community/general/locale_gen_module.html).

## Configuration
These are the most important configuration options you shold know.
For more detailed information, please see the [Ansible role repository](https://github.com/peering-manager/ansible-role-peering-manager).

|              Variable                |                              Default                             |                                                        Notes                                                |
|--------------------------------------|------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| `peering_manager_database`           | `peering-manager`                                                |                          											|
| `peering_manager_database_user`      | `peering-manager`                                                | 														|
| `peering_manager_database_password`  | `peering-manager`                                                | 														|
| `peering_manager_database_host`      | `localhost`                                                      | PostgreSQL will only be set up if this is set to `localhost`. Otherwise, an existing database will be used. |
| `peering_manager_database_lc`        | `en_US.UTF-8`                                                    | 														|
| `peering_manager_install_directory`  | `/opt/peering-manager`                                           | 														|
| `peering_manager_superuser_username` | `admin`                                                          | 														|
| `peering_manager_superuser_password` | `admin`                                                          | 														|
| `peering_manager_superuser_email`    | `admin@example.com`                                              | 														|
| `peering_manager_setup_systemd`      | `false`                                                          | Set to `true` to set up gunicorn and the Peering Manager worker units. 					|
| `peering_manager_setup_web_frontend` | `false`                                                          | Set to `true` to configure Apache web server. 								|
| `peering_manager_config`             | `ALLOWED_HOSTS:`<br>&ensp; `- localhost`<br>&ensp; `- 127.0.0.1` | Allowed hosts are used for hostnames in Apache config 							|
| `peering_manager_setup_cron_jobs`    | `true`                                                           | Set up cron for regular Peering Manager tasks 								|

