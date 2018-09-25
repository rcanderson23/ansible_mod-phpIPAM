from requests import Session


class PhpIpamWrapper(Session):
    def __init__(self, username, password, url):
        Session.__init__(self)
        self.username = username
        self.password = password
        self.url = url
        self.auth = (self.username, self.password)

    # Create and authenticates a session against phpipam server
    def create_session(self):
        url = self.url + 'user/'
        auth = self.post(url)
        token = auth.json().get('data').get('token')
        self.headers.update({'token': '%s' % token})

    # Retrieves subnet information in json
    def get_subnet(self, subnet, section):
        url = self.url + 'subnets/cidr/%s/' % subnet
        subnet_response = self.get(url)
        section_id = self.get_section_id(section)
        try:
            for subnets in subnet_response.json()['data']:
                if subnets['sectionId'] == section_id:
                    return subnets
        except KeyError:
            return None

    def get_section(self, section):
        url = self.url + 'sections/%s/' % section
        section_response = self.get(url)
        try:
            return section_response.json()['data']
        except KeyError, e:
            return None

    def get_vlan(self, vlan):
        url = self.url + 'vlan/'
        vlan_response = self.get(url)
        for vlans in vlan_response.json()['data']:
            if vlans['number'] == vlan:
                return vlans
        return None

    def get_subnet_id(self, subnet, section):
        subnet_response = self.get_subnet(subnet, section)
        try:
            section_id = self.get_section_id(section)
        except KeyError:
            return None
        if subnet_response['sectionId'] == section_id:
            return subnet_response['id']
        else:
            return None

    def get_section_id(self, section):
        section_response = self.get_section(section)
        try:
            return section_response['id']
        except KeyError:
            return None
        except TypeError:
            return None
    
    def get_vlan_id(self, vlan):
        vlans = self.get_vlan(vlan)
        try:
            if vlans['number'] == vlan:
                return vlans['vlanId']
        except TypeError:
            return None

