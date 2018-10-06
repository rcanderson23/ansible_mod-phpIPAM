#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.phpipam as phpipam


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type=str, required=True),
            password=dict(type=str, required=True, no_log=True),
            url=dict(type=str, required=True),
            vlan=dict(type=str, required=True),
            name=dict(type=str, required=True),
            description=dict(type=str, required=False),
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
    vlan = module.params['vlan']
    name = module.params['name']
    description = module.params['description']
    state = module.params['state']

    session = phpipam.PhpIpamWrapper(username, password, url)
    try:
        session.create_session()
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)

    vlan_url = url + 'vlan/'
    found_vlan = session.get_vlan(vlan)

    optional_args = {'name': name,
                     'description': description}
    if state == 'present' and found_vlan is None:
        # Create vlan if not present

        creation = session.create(session,
                                  vlan_url,
                                  number=vlan,
                                  **optional_args)
        if creation['code'] == 201:
            result['changed'] = True
            result['msg'] = creation
            module.exit_json(**result)
        else:
            module.fail_json(msg='vlan unable to be created', **result)
    elif state == 'present':
        # Update vlan information if necessary

        value_changed = False
        payload = {'name': name}
        vlan_id = session.get_vlan_id(vlan)

        for k in optional_args:
            if optional_args[k] != found_vlan[k]:
                value_changed = True
                payload[k] = optional_args[k]
        if value_changed:
            patch_response = session.modify(session,
                                            vlan_url,
                                            id=vlan_id,
                                            **payload)
            result['changed'] = True
            result['msg'] = patch_response
            module.exit_json(**result)
        else:
            result['msg'] = patch_response
            module.exit_json(**result)
    else:
        # Delete vlan if it exist

        vlan_id = session.get_vlan_id(vlan)
        if vlan_id is None:
            result['msg'] = 'Vlan doesn\'t exist'
            module.exit_json(**result)
        else:
            deletion = session.remove(session,
                                      vlan_url,
                                      vlan_id)
            if deletion['code'] == 200:
                result['changed'] = True
                result['msg'] = deletion
                module.exit_json(**result)
            else:
                result['msg'] = deletion
                module.fail_json(**result)


if __name__ == '__main__':
    main()
