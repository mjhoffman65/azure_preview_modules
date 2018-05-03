#!/usr/bin/python
#
# Copyright (c) 2017 Sertac Ozercan, <seozerca@microsoft.com>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: azure_rm_virtualmachine_scaleset_facts

version_added: "2.4"

short_description: Get Virtual Machine Scale Set facts

description:
    - Get facts for a virtual machine scale set

options:
    name:
        description:
            - Limit results to a specific virtual machine scale set
        required: false
        default: null
    resource_group:
        description:
            - The resource group to search for the desired virtual machine scale set
        required: false

    format:
        description:
            - What data should be returned?
        default: 'default'
        choices:
            - 'default'
            - 'full'
            - 'raw'

extends_documentation_fragment:x
    - azure

author:
    - "Sertac Ozercan (@sozercan)"
'''

EXAMPLES = '''
    - name: Get facts for a virtual machine scale set
      azure_rm_virtualmachine_scaleset_facts:
        resource_group: Testing
        name: testvmss001

    - name: Get facts for all virtual networks
      azure_rm_virtualmachine_scaleset_facts:
        resource_group: Testing

    - name: Get facts by tags
      azure_rm_virtualmachine_scaleset_facts:
        resource_group: Testing
        tags:
          - testing
'''

RETURN = '''
azure_vmss:
    description: List of virtual machine scale sets
    returned: always
    type: list
    example: [{
        "location": "eastus",
        "properties": {
            "overprovision": true,
            "singlePlacementGroup": true,
            "upgradePolicy": {
                "mode": "Manual"
            },
            "virtualMachineProfile": {
                "networkProfile": {
                    "networkInterfaceConfigurations": [
                        {
                            "name": "testvmss",
                            "properties": {
                                "dnsSettings": {
                                    "dnsServers": []
                                },
                                "enableAcceleratedNetworking": false,
                                "ipConfigurations": [
                                    {
                                        "name": "default",
                                        "properties": {
                                            "privateIPAddressVersion": "IPv4",
                                            "subnet": {
                                                "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing/providers/Microsoft.Network/virtualNetworks/testvnet/subnets/testsubnet"
                                            }
                                        }
                                    }
                                ],
                                "primary": true
                            }
                        }
                    ]
                },
                "osProfile": {
                    "adminUsername": "testuser",
                    "computerNamePrefix": "testvmss",
                    "linuxConfiguration": {
                        "disablePasswordAuthentication": true,
                        "ssh": {
                            "publicKeys": [
                                {
                                    "keyData": "",
                                    "path": "/home/testuser/.ssh/authorized_keys"
                                }
                            ]
                        }
                    },
                    "secrets": []
                },
                "storageProfile": {
                    "imageReference": {
                        "offer": "CoreOS",
                        "publisher": "CoreOS",
                        "sku": "Stable",
                        "version": "899.17.0"
                    },
                    "osDisk": {
                        "caching": "ReadWrite",
                        "createOption": "fromImage",
                        "managedDisk": {
                            "storageAccountType": "Standard_LRS"
                        }
                    }
                }
            }
        },
        "sku": {
            "capacity": 1,
            "name": "Standard_DS1_v2",
            "tier": "Standard"
        }
    }]
'''  # NOQA

from ansible.module_utils.azure_rm_common import AzureRMModuleBase
import re

try:
    from msrestazure.azure_exceptions import CloudError
except:
    # handled in azure_rm_common
    pass

AZURE_OBJECT_CLASS = 'VirtualMachineScaleSet'

AZURE_ENUM_MODULES = ['azure.mgmt.compute.models']


class AzureRMVirtualMachineScaleSetFacts(AzureRMModuleBase):
    """Utility class to get virtual machine scale set facts"""

    def __init__(self):

        self.module_args = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            format=dict(
                type='str',
                choices=['default',
                         'full',
                         'raw']
            ),
        )

        self.results = dict(
            changed=False,
            ansible_facts=dict(
                azure_vmss=[]
            )
        )

        self.name = None
        self.resource_group = None
        self.format = 'default'
        self.tags = None

        super(AzureRMVirtualMachineScaleSetFacts, self).__init__(
            derived_arg_spec=self.module_args,
            supports_tags=False,
            facts_module=True
        )

    def exec_module(self, **kwargs):

        for key in self.module_args:
            setattr(self, key, kwargs[key])

        if self.name and not self.resource_group:
            self.fail("Parameter error: resource group required when filtering by name.")
        if self.name:
            self.results['ansible_facts']['azure_vmss'] = self.get_item()
        else:
            self.results['ansible_facts']['azure_vmss'] = self.list_items()

        return self.results

    def get_item(self):
        """Get a single virtual machine scale set"""

        self.log('Get properties for {}'.format(self.name))

        item = None
        results = []

        try:
            item = self.compute_client.virtual_machine_scale_sets.get(self.resource_group, self.name)
        except CloudError:
            pass

        if item and self.has_tags(item.tags, self.tags):
            results = [self.serialize_obj(item, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES)]

        if self.format == 'full':

            vmss = self.serialize_obj(item, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES)

            subnet_id = vmss['properties']['virtualMachineProfile']['networkProfile']['networkInterfaceConfigurations'][0]['properties']['ipConfigurations'][0]['properties']['subnet']['id']
            backend_address_pool_id = vmss['properties']['virtualMachineProfile']['networkProfile']['networkInterfaceConfigurations'][0]['properties']['ipConfigurations'][0]['properties']['loadBalancerBackendAddressPools'][0]['id']
            subnet_name = re.sub('.*subnets\\/', '', subnet_id)
            load_balancer_name =  re.sub('\\/backendAddressPools.*', '', re.sub('.*loadBalancers\\/', '', backend_address_pool_id))
            virtual_network_name = re.sub('.*virtualNetworks\\/', '', re.sub('\\/subnets.*', '', subnet_id))

            results[0] = {}
            results[0]['resource_group'] = self.resource_group
            results[0]['name'] = vmss['name']
            results[0]['state'] = 'present'
            results[0]['location'] = vmss['location']
            results[0]['vm_size'] = vmss['sku']['name'] 
            results[0]['capacity'] = vmss['sku']['capacity']
            results[0]['tier'] = vmss['sku']['tier']
            results[0]['upgrade_policy'] = vmss['properties']['upgradePolicy']['mode']
            #results[0]['admin_username']
            #results[0]['admin_password']
            #results[0]['ssh_password_enabled']
            #results[0]['ssh_public_keys']
            # image could be a dict, string, 
            results[0]['image'] = vmss['properties']['virtualMachineProfile']['storageProfile']['imageReference']

            results[0]['os_disk_caching'] = vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['caching']
            results[0]['os_type'] = vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['caching']
            results[0]['managed_disk_type'] = vmss['properties']['virtualMachineProfile']['storageProfile']['osDisk']['managedDisk']['storageAccountType']
            #results[0]['data_disks']
            results[0]['virtual_network_name'] = virtual_network_name
            results[0]['subnet_name'] = subnet_name
            results[0]['load_balancer'] = load_balancer_name
            #results[0]['remove_on_absent']

        return results

    def list_items(self):
        """Get all virtual machine scale sets"""

        self.log('List all virtual machine scale sets')

        try:
            response = self.compute_client.virtual_machine_scale_sets.list(self.resource_group)
        except CloudError as exc:
            self.fail('Failed to list all items - {}'.format(str(exc)))

        results = []
        for item in response:
            if self.has_tags(item.tags, self.tags):
                results.append(self.serialize_obj(item, AZURE_OBJECT_CLASS, enum_modules=AZURE_ENUM_MODULES))

        return results


def main():
    """Main module execution code path"""

    AzureRMVirtualMachineScaleSetFacts()

if __name__ == '__main__':
    main()
