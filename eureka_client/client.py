# -*- coding: utf-8 -*-
"""
Copyright 2017 Martin Picard
MIT License
"""
import json
import logging
import requests
from random import shuffle
from urllib.parse import urljoin
from eureka_client.exceptions import ConfigurationException
from eureka_client.statuses import STATUS_STARTING

log = logging.getLogger('eureka_client')


class Client:
    """
    Eureka Client
    """
    def __init__(self,
                 app_name,
                 context="eureka/v2",
                 eureka_domain_name=None,
                 eureka_port=None,
                 eureka_url=None,
                 health_check_url=None,
                 homepage_url=None,
                 hostname=None,
                 ip_addr=None,
                 port=None,
                 prefer_same_zone=True,
                 region=None,
                 secure_port=None,
                 secure_vip_address=None,
                 use_dns=True,
                 vip_address=None):
        """
        Initialize client with parameters
        """
        if not (eureka_url or use_dns):
            raise ConfigurationException(
                "eureka_url must be set or use_dns must be True")

        self.app_name = app_name
        self.context = context
        self.health_check_url = health_check_url
        self.hostname = hostname
        self.port = port
        self.prefer_same_zone = prefer_same_zone
        self.region = region
        self.secure_vip_address = secure_vip_address
        self.server_domain_name = eureka_domain_name
        self.server_port = eureka_port
        self.server_url = eureka_url
        self.server_urls = self.get_urls()
        self.use_dns = use_dns
        self.vip_address = vip_address

    @property
    def headers(self):
        return {'Content-Type': 'application/json'}

    def get_urls(self):
        """
        Build List of urls
        """
        if self.server_url:
            return [self.server_url]

        # Use DNS
        zone_dns = self.get_zones()
        zones = list(zone_dns.keys())

        if not len(zones):
            raise RuntimeError("No availability zones found")

        if self.prefer_same_zone:
            if self.get_instance_zone() in zones:
                zones.insert(0, self.get_instance_zone())
            else:
                log.warn(f"""Instance zone ${self.get_instance_zone()}
                         not in available zones ${zones}""")

        service_urls = []
        for zone in zones:
            instances = zone_dns[zone]
            shuffle(instances)
            for instance in instances:
                uri = f"http://${instance}"
                if self.port:
                    uri += f":${self.port}"
                instance_url = urljoin(uri, self.context, "/")
                # Add missing trailing slash
                instance_url.replace(r'^(.*?)(\/?)$', '$1/')
                service_urls.append(instance_url)

        primary = service_urls.pop(0)
        shuffle(service_urls)
        service_urls.insert(0, primary)

        log.info(f"Client serviceUrls ordering: ${service_urls}")

        return service_urls

    def get_instance_zone(self):
        """
        Retrieve instance zone from metadata.
        """
        if self.datacenter in ("AWS", "Amazon"):
            return ec2metadata.get('availability-zone')
        raise NotImplementedError(f"""eureka_client can't use DNS
                                  for ${self.datacenter}""")

    def get_instance_id(self):
        """
        Retrieve instance id from metadata or client configurations.
        """
        if self.datacenter in ("AWS", "Amazon"):
            return ec2metadata.get('instance-id')
        return (f'${self.hostname}:${self.app_name}:${self.port}')

    def register(self, initial_status=STATUS_STARTING):
        """
        """
        dc_info = {
            '@class': 'com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo',
            'name': self.datacenter
        }
        if self.datacenter in ("AWS", "Amazon"):
            dc_info['metadata'] = {
                'ami-launch-index': ec2metadata.get('ami-launch-index'),
                'local-hostname': ec2metadata.get('local-hostname'),
                'availability-zone': ec2metadata.get('availability-zone'),
                'instance-id': ec2metadata.get('instance-id'),
                'public-ipv4': ec2metadata.get('public-ipv4'),
                'public-hostname': ec2metadata.get('public-hostname'),
                'ami-manifest-path': ec2metadata.get('ami-manifest-path'),
                'local-ipv4': ec2metadata.get('local-ipv4'),
                'ami-id': ec2metadata.get('ami-id'),
                'instance-type': ec2metadata.get('instance-type'),
            }
            instance = {
                'hostName': self.hostname,
                'app': self.app_name,
                'ipAddr': self.ip_addr,
                'vipAddr': self.vip_address or '',
                'secureVipAddr': self.secure_vip_address or '',
                'status': initial_status,
                'port': {'$': self.port, '@enabled': 'true'},
                'securePort': {'$': self.secure_port, '@enabled': 'false'},
                'dataCenterInfo': dc_info,
                'healthCheckUrl': self.health_check_url or '',
                'instanceId': self.get_instance_id(),
                'homePageUrl': self.homepage_url,
                'vipAddress': self.hostname,
                'secureVipAddress': self.hostname
            }

            success, err = False, None

            for base_url in self.server_urls:
                try:
                    r = requests.put(self._get_register_url(base_url),
                                     data=json.dumps({'instance': instance}),
                                     headers=HEADERS)
                except Exception as e:
                    raise e

    def _get_register_url(self, base_url):
        """
        Returns registration endpoint url
        """
        return urljoin(base_url, f"apps/{self.app_name}")
