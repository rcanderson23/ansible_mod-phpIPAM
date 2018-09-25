#!/usr/bin/python
from __future__ import print_function
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.phpipam as phpipam

def main():
    module = AnsibleModule(
        argument_spec=dict(
        username=dict(type=str, required=True),
        password=dict(type=str, required=True, no_log=True),
        url=dict(type=str, required=True),
        subnet=dict(type=str, required=True),
        section=dict(type=str, required=True),
        hostname=dict(type=str, required=False),
        description=dict(type=str, required=False)
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False
    )
    username = module.params['username']
    password = module.params['password']
    url = module.params['url']
    subnet = module.params['subnet']
    section = module.params['section']
    hostname = module.params['hostname']
    description = module.params['description']

    session = phpipam.PhpIpamWrapper(username, password, url)
    try:
        session.create_session()
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)
    subnet_url = url + 'subnets/'
    subnet_response = session.get_subnet(subnet, section)
    if subnet_response:
        url += 'addresses/first_free/'
        subnet_id = session.get_subnet_id(subnet, section)
        payload = {'subnetId': subnet_id,
                   'hostname': hostname,
                   'description': description}
        free_ip = session.post(url, payload)
        if free_ip.json()['success']:
            ip = free_ip.json().get('data')
            result['ip'] = ip
            module.exit_json(**result)
        else:
            module.fail_json(msg='Subnet is full', **result)
    else:
        module.fail_json(msg='Subnet or section doesn\'t exist', **result)

if __name__ == '__main__':
    main()
