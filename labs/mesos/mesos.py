#!/usr/bin/env python
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from argparse import ArgumentParser

# Dealing with relative import
if __name__ == "__main__" and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from lab import Lab, enable_debug
else:
    from ..lab import Lab, enable_debug

class Mesos(Lab):
    def __init__(self, environment, deployment, region, zone, zone_name, instance_count, instance_type,
                 mesos_version, zk_version, node, aurora_url='', marathon_version='', marathon='',
                 aurora='', mesos_dns='', slave_on_master=''):
        super(Mesos, self).__init__(environment, deployment, region, zone, 
                                    template="-".join([node,'template.cfn']))
        vpc_id = self.get_vpc(environment).id
        private_subnet_id = self.get_subnet("private." + environment, vpc_id, zone).id
        topic_arn = self.get_sns_topic("autoscaling-notifications-" + environment)
        role_name = self.get_role_name("GenericDev")
        self.stack_name = "-".join([self.lab_dir, node, environment, deployment, region, zone])
        hosted_zone_id = self.get_hosted_zone_id(zone_name)
        # m1, c1, m2 instances need old paravirtualized ami. New instances need hvm enabled ami.
        if instance_type in ["m1.small", "m1.medium", "m1.large", "m1.xlarge", "c1.medium",
                             "c1.large", "m2.xlarge", "m2.2xlarge","m2.4xlarge"]:
            virtualization = "paravirt"
        else:
            virtualization = "hvm"
        self.parameters.append(("KeyName",          environment))
        self.parameters.append(("Environment",      environment))
        self.parameters.append(("Deployment",       deployment))
        self.parameters.append(("AvailabilityZone", zone))
        self.parameters.append(("NumberOfNodes",    instance_count))
        self.parameters.append(("InstanceType",     instance_type))
        self.parameters.append(("MesosVersion",     mesos_version))
        self.parameters.append(("ZookeeperVersion", zk_version))
        self.parameters.append(("VpcId",            vpc_id))
        self.parameters.append(("PrivateSubnetId",  private_subnet_id))
        self.parameters.append(("AsgTopicArn",      topic_arn))
        self.parameters.append(("RoleName",         role_name))
        self.parameters.append(("Virtualization",   virtualization))
        self.parameters.append(("HostedZoneId",     hosted_zone_id))
        if node == "master":
            public_subnet_id = self.get_subnet("public." + environment, vpc_id, zone).id
            self.parameters.append(("PublicSubnetId",  public_subnet_id))
            self.parameters.append(("AuroraUrl",       aurora_url))  # Needs to be optional in CFN template
            self.parameters.append(("MarathonVersion", marathon_version))
            self.parameters.append(("Marathon",        marathon))
            self.parameters.append(("Aurora",          aurora))
            self.parameters.append(("MesosDns",        mesos_dns))
            self.parameters.append(("SlaveOnMaster",   slave_on_master))


parser = ArgumentParser(description='Deploy Mesos Master(s) or Slave(s) to an AWS CloudFormation environment.')
subparsers_mesos = parser.add_subparsers(dest="mesos")
parser_master = subparsers_mesos.add_parser(name="master", add_help=True)
parser_master.add_argument('--debug', action='store_true', help='Enable debug mode')
parser_master.add_argument('-e', '--environment', required=True, help='CloudFormation environment to deploy to')
parser_master.add_argument('-d', '--deployment', required=True, help='Unique name for the deployment')
parser_master.add_argument('-r', '--region', required=True, help='Geographic area to deploy to')
parser_master.add_argument('-z', '--availability-zone', required=True, help='Isolated location to deploy to')
parser_master.add_argument('-o', '--hosted-zone', required=True, help='The name of dns route53 hosted zone')
parser_master.add_argument('-n', '--num-nodes', type=int, default=1, help='Number of instances to deploy')
parser_master.add_argument('-i', '--instance-type', default='m1.small', help='AWS EC2 instance type to deploy')
parser_master.add_argument('-m', '--mesos-version', default='0.21.0', help='The Mesos version to deploy')
parser_master.add_argument('-v', '--zk-version', default='3.4.6', help='The Zookeeper version to deploy')
parser_slave = subparsers_mesos.add_parser(name="slave", add_help=False, parents=[parser_master])
parser_master.add_argument('-a', '--aurora-url', default='', help='The Aurora scheduler URL')
parser_master.add_argument('-t', '--marathon-version', default='0.7.5', help='The Marathon version to deploy')
parser_master.add_argument('--marathon', default='false', action='store_const', const='true',
                           help='Use this flag to deploy Marathon framework')
parser_master.add_argument('--aurora', default='false', action='store_const', const='true',
                           help='Use this flag to deploy Aurora framework')
parser_master.add_argument('--mesos-dns', default='false', action='store_const', const='true',
                           help='Use this flag to deploy Mesos-DNS on Marathon')
parser_master.add_argument('--slave-on-master', default='false', action='store_const', const='true',
                           help='Use this flag to deploy Mesos slaves on master nodes')

def main(parser):
    args, unknown = parser.parse_known_args()
    enable_debug(args)
    if args.mesos == 'master':
        lab = Mesos(args.environment, args.deployment, args.region, args.availability_zone, args.hosted_zone,
                    str(args.num_nodes), args.instance_type, args.mesos_version, args.zk_version,
                    args.mesos, args.aurora_url, args.marathon_version, args.marathon,
                    args.aurora, args.mesos_dns, args.slave_on_master)
    elif args.mesos == 'slave':
        lab = Mesos(args.environment, args.deployment, args.region, args.availability_zone, args.hosted_zone,
                    str(args.num_nodes), args.instance_type, args.mesos_version, args.zk_version,
                    args.mesos)
    lab.deploy()

if __name__ == '__main__':
    main(parser)
