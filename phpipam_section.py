#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.phpipam as phpipam


def set_master_section(session, master_section):
    if master_section in ('', 'root'):
        return '0'
    else:
        return session.get_section_id(master_section)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type=str, required=True),
            password=dict(type=str, required=True, no_log=True),
            url=dict(type=str, required=True),
            section=dict(type=str, required=True),
            master_section=dict(type=str, required=False, default='root'),
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
    section = module.params['section']
    master_section = module.params['master_section']
    description = module.params['description']
    state = module.params['state']

    session = phpipam.PhpIpamWrapper(username, password, url)
    try:
        session.create_session()
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)

    section_url = url + 'sections/'
    found_section = session.get_section(section)
    master_section_id = set_master_section(session, master_section)
    if master_section_id is None:
        module.fail_json(msg='master_section does not exist', **result)
    else:
        optional_args = {'masterSection': set_master_section(session, master_section),
                         'description': description}
    if state == 'present' and found_section is None:
        # Create the section since it does not exist

        if optional_args['masterSection'] == '0':
            del optional_args['masterSection']
        creation = session.create(session,
                                  section_url,
                                  name=section,
                                  **optional_args)
        if creation['code'] == 201:
            result['changed'] = True
            result['msg'] = creation
            module.exit_json(**result)
        elif creation['code'] == 500:
            result['msg'] = creation
            module.exit_json(**result)
        else:
            result['msg'] = creation
            module.fail_json(msg='Something went wrong', **result)
    elif state == 'present':
        # Potentially modify the section if it doesn't match

        value_changed = False
        payload = {}
        section_id = session.get_section_id(section)

        for k in optional_args:
            if optional_args[k] != found_section[k]:
                value_changed = True
                payload[k] = optional_args[k]
        if value_changed:
            patch_response = session.modify(session,
                                            section_url,
                                            id=section_id,
                                            **payload)
            result['changed'] = True
            result['msg'] = patch_response
            module.exit_json(**result)
        else:
            result['msg'] = 'No changes made to section'
            module.exit_json(**result)
    else:
        # Ensure the section does not exist, delete if necessary

        section_info = session.get_section(section)
        try:
            deletion = session.remove(session,
                                      section_url,
                                      section_info['id'])
            if deletion['code'] == 200:
                result['changed'] = True
                result['msg'] = deletion
                module.exit_json(**result)
        except KeyError:
            result['msg'] = 'Section did not exist'
            module.exit_json(**result)
        except TypeError:
            result['msg'] = 'Section did not exist'
            module.exit_json(**result)


if __name__ == '__main__':
    main()
