# Ansible

With Ansible you can get the same results as with the manual setup but in an
automated and reproducible way. It will however use gunicorn and Apache 2 to
expose Peering Manager services, you will need to handle things by yourself if
you want to use something else, e.g uWSGI and nginx.

## Installation

In order to use Ansible to install Peering Manager, you will need to install
it a machine of your choice. Please refer to [Ansible's
documentation](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html)
for guildelines

!!! attention
    Ansible is an advanced topic which can get quite complex. If you have
    never used it before, it is recommended to take a look at a
    [tutorial](https://docs.ansible.com/ansible/latest/user_guide/intro_getting_started.html)
    first.

With Ansible setup on a machine, you can fetch the role dedicated to Peering
Manager via Ansible Galaxy:

```no-highlight
ansible-galaxy install gmazoyer.peering_manager
```

Later updates can be installed with:

```no-highlight
ansible-galaxy install gmazoyer.peering_manager --force
```

The role will install and configure Python, PostgreSQL, Redis, Apache and
Peering Manager on Debian or Ubuntu based machine.

!!! attention
    When the Ansible remote user is not root, the package `acl` is required
    and has to be installed before running this role.
    
    Please also make sure that the choosen database locale is already
    installed or this role will fail. This can be achieved with
    [community.general.locale_gen](https://docs.ansible.com/ansible/latest/collections/community/general/locale_gen_module.html).

## Configuration

Please refer to the the [Ansible role's
`README.md`](https://github.com/peering-manager/ansible-role-peering-manager/blob/main/README.md).
