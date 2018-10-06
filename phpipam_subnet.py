#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.phpipam as phpipam


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type=str, required=True),
            password=dict(type=str, required=True, no_log=True),
            url=dict(type=str, required=True),
            section=dict(type=str, required=True),
            subnet=dict(type=str, required=True),
            description=dict(type=str, required=False),
            vlan=dict(type=str, required=False),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False
    )
    username = module.params['username']
    password = module.params['password']
    url = module.params['url']
    section = module.params['section']
    subnet = module.params['subnet']
    description = module.params['description']
    vlan = module.params['vlan']
    state = module.params['state']

    session = phpipam.PhpIpamWrapper(username, password, url)
    try:
        session.create_session()
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)

    subnet_url = url + 'subnets/'
    try:
        section_id = session.get_section_id(section)
    except:
        module.fail_json(msg='section doesn\'t exist', **result)
    found_subnet = session.get_subnet(subnet, section)

    if vlan:
        # If vlan is defined, make sure it exists and then set

        vlan_id = session.get_vlan_id(vlan)
        if vlan_id is None:
            module.fail_json(msg='vlan not found', **result)
        else:
            optional_args = {'description': description,
                             'vlanId': vlan_id}
    else:
        optional_args = {'description': description}

    if state == 'present' and found_subnet is None:
        # Create subnet if it doesn't exist

        subnet_split = subnet.rsplit('/',1)
        creation = session.create(session,
                                  subnet_url,
                                  subnet=subnet_split[0],
                                  mask=subnet_split[1],
                                  sectionId=section_id,
                                  **optional_args)
        if creation['code'] == 201:
            result['changed'] = True
            result['msg'] = creation
            module.exit_json(**result)
        else:
            result['msg'] = creation
            module.fail_json(**result)
    elif state == 'present':
        # Update subnet if necessary

        value_changed = False
        payload = {}
        for k in optional_args:
            if optional_args[k] != found_subnet[k]:
                value_changed = True
                payload[k] = optional_args[k]
        if value_changed:
            patch_response = session.modify(session,
                                            subnet_url,
                                            id=found_subnet['id'],
                                            sectionId=found_subnet['sectionId'],
                                            **payload)
            result['changed'] = True
            result['msg'] = patch_response
            module.exit_json(**result)
        else:
            result['msg'] = 'Subnet required no change'
            module.exit_json(**result)
    else:
        # Delete subnet if present
        try:
            deletion = session.remove(session, subnet_url, found_subnet['id'])
            if deletion['code'] == 200:
                result['changed'] = True
                result['msg'] = deletion
                module.exit_json(**result)
        except TypeError:
            result['msg'] = 'Subnet did not exist'
            module.exit_json(**result)


if __name__ == '__main__':
    main()
