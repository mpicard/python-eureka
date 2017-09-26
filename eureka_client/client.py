# -*- coding: utf-8 -*-
# Copyright 2017 Martin Picard
# MIT License
import json
import logging
import requests
from random import shuffle
from urllib.parse import urljoin
from dns.resolver import query
from ec2_metadata import ec2_metadata
from eureka_client import __version__
from eureka_client.exceptions import ClientConfigurationException, RegistrationFailed
from eureka_client.statuses import STATUS_STARTING


log = logging.getLogger('eureka_client')


class Client:
    """
    Application client for Netflix Eureka.
    """
    def __init__(self,
                 app_name,
                 context="eureka/v2",
                 datacenter="Amazon",
                 eureka_domain_name=None,
                 eureka_port=None,
                 eureka_url=None,
                 health_check_url=None,
                 homepage_url=None,
                 hostname=None,
                 ip_addr=None,
                 port=None,
                 prefer_same_zone=True,
                 region_name=None,
                 secure_port=None,
                 secure_vip_address=None,
                 vip_address=None):

        self.metadata = ec2_metadata
        self.app_name = app_name
        self.datacenter = datacenter
        self.context = context
        self.health_check_url = health_check_url
        self.port = port
        self.prefer_same_zone = prefer_same_zone
        self.secure_vip_address = secure_vip_address
        self.server_domain_name = eureka_domain_name
        self.server_port = eureka_port
        self.server_url = eureka_url
        self.vip_address = vip_address

        if region_name:
            self.region_name = region_name
        else:
            self.region_name = self.metadata.region

        if hostname:
            self.hostname = hostname
        else:
            self.hostname = self.metadata.public_hostname

    @property
    def headers(self):
        return {
            'Content-Type': 'application/json',
            'User-agent': 'python-eureka-client v{}'.format(__version__),
            'accept': 'application/json'
        }

    @property
    def instance_zone(self):
        return self.metadata.availability_zone

    @property
    def instance_id(self):
        return self.metadata.instance_id

    def get_zones(self):
        zone_urls = list(self._get_zone_urls(
            f"txt.{self.region_name}.{self.server_domain_name}"))
        urls = list(self._get_zone_urls(f"txt.{url}") for url in zone_urls)
        return {i.split('.')[0]: urls for i in zone_urls}

    def register(self, initial_status=STATUS_STARTING):
        datacenter_info = {
            '@class': 'com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo',
            'name': self.datacenter,
            'metadata': {
                'ami-launch-index':  self.metadata.ami_launch_index,
                'local-hostname':    self.metadata.private_hostname,
                'availability-zone': self.metadata.availability_zone,
                'instance-id':       self.metadata.instance_id,
                'public-ipv4':       self.metadata.public_ipv4,
                'public-hostname':   self.metadata.public_hostname,
                'ami-manifest-path': self.metadata.ami_manifest_path,
                'local-ipv4':        self.metadata.private_ipv4,
                'ami-id':            self.metadata.ami_id,
                'instance-type':     self.metadata.instance_type
            }
        }

        instance = {
            'hostName':         self.hostname,
            'app':              self.app_name,
            'ipAddr':           self.ip_addr,
            'vipAddr':          self.vip_address or '',
            'secureVipAddr':    self.secure_vip_address or '',
            'status':           initial_status,
            'dataCenterInfo':   datacenter_info,
            'healthCheckUrl':   self.health_check_url or '',
            'instanceId':       self.instance_id,
            'homePageUrl':      self.homepage_url,
            'vipAddress':       self.hostname,
            'secureVipAddress': self.hostname,
            'port': {
                '$': self.port,
                '@enabled': 'true'
            },
            'securePort': {
                '$': self.secure_port,
                '@enabled': 'false'
            },
        }

        err = None

        for base_url in self.server_urls:
            try:
                r = requests.put(self._get_app_url(base_url),
                                 data=json.dumps({'instance': instance}),
                                 headers=HEADERS)
                r.raise_for_status()
                return
            except requests.exceptions.RequestException as e:
                err = e

        raise RegistrationFailed(str(err))

    def update_status(self, status):
        err = None

        for base_url in self.server_urls:
            try:
                r = requests.put(self._get_status_url(base_url, status))
                r.raise_for_status()
                return
            except requests.exceptions.RequestException as e:
                err = e

        raise UpdateFailed(str(err))

    def heartbeat(self):
        for base_url in self.server_urls:
            try:
                r = requests.put(self._get_instance_url(base_url))
                r.raise_for_status()
                return
            except requests.exceptions.RequestException:
                raise HeartbeatFailed("No instances replied to heartbeat")

    def get_apps(self):
        return self._get_data('apps')

    def get_app(self, app_id):
        return self._get_data(f'apps/{app_id}')

    def get_vip(self, vip_address):
        return self._get_data(f'vips/{vip_address}')

    def get_svip(self, vip_address):
        return self._get_data(f'svips/{vip_address}')

    def get_instance(self, instance_id):
        return self._get_data(f'instances/{instance_id}')

    def get_app_instance(self, app_id, instance_id):
        return self._get_data(f'apps/{app_id}/{instance_id}')

    def _get_zone_urls(self, domain):
        records = query(domain, 'TXT')
        for r in records:
            for i in record.string:
                yield i

    def _get_data(self, resource):
        """
        Generic get requests for any instance data, returns dict of payload
        """
        # TODO: cache
        for base_url in self.server_urls:
            try:
                r = requests.get(urljoin(base_url, resource),
                                 headers={'accept': 'application/json',
                                          'accept-encoding': 'gzip'})
                r.raise_for_status()
                return r.json()
            except requests.exceptions.RequestException:
                pass
        raise FetchFailed(f"Failed to get {resource} from all instances")

    def _get_status_url(self, base_url, status):
        """
        Returns apps/{app_name}/{instane_id}/status?value={status}
        """
        return urljoin(self._get_instance_url(base_url),
                       f"status?value={status}")

    def _get_instance_url(self, base_url):
        """
        Returns apps/{app_name}/{instance_id}
        """
        return urljoin(self._get_app_url(base_url), f"{self.instance_id}")

    def _get_app_url(self, base_url):
        """
        Returns apps/{app_name}
        """
        return urljoin(base_url, f"apps/{self.app_name}")
