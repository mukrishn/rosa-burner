#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid
import sys
import os
import yaml
import json
import time
import datetime
import argparse
import configparser


class Platform:
    def __init__(self, arguments, logging, utils, es):
        self.utils = utils
        self.logging = logging
        self.es = es
        self.environment = {}

        self.environment["commands"] = []
        self.environment["commands"].append("ocm")
        self.environment["commands"].append("oc")

        self.environment["platform"] = arguments["platform"]

        self.environment["ocm_url"] = arguments["ocm_url"]
        self.environment["ocm_token"] = arguments["ocm_token"]

        self.environment["uuid"] = (
            arguments["uuid"] if arguments["uuid"] else str(uuid.uuid4())
        )
        self.logging.info("Test running with UUID: %s" % self.environment["uuid"])

        self.environment["path"] = (
            arguments["path"]
            if arguments["path"]
            else "/tmp/" + self.environment["uuid"]
        )
        utils.create_path(self.environment["path"])
        self.logging.info("Using %s as working directory" % self.environment["path"])

        self.environment["clusters"] = {}
        self.environment["cluster_count"] = arguments["cluster_count"]
        self.environment["batch_size"] = arguments["batch_size"]
        self.environment["delay_between_batch"] = arguments["delay_between_batch"]

        self.environment["watcher_delay"] = arguments["watcher_delay"]

        self.environment["workers"] = arguments["workers"]

        self.environment["wait_for_workers"] = (
            arguments["wait_for_workers"] if arguments["wait_for_workers"] else None
        )
        self.environment["workers_wait_time"] = (
            arguments["workers_wait_time"] if arguments["wait_for_workers"] else None
        )

        if arguments['enable_workload']:
            self.environment['load'] = {}
            self.environment['load']["workload"] = arguments["workload"]
            self.environment['load']["repo"] = arguments["workload_repo"]
            self.environment['load']["script"] = arguments["workload_script"]
            self.environment['load']["executor"] = arguments["workload_executor"]
            self.environment['load']['duration'] = arguments['workload_duration']
            self.environment['load']['jobs'] = arguments['workload_jobs']

        self.environment["cluster_name_seed"] = utils.generate_cluster_name_seed(arguments["cluster_name_seed"])

        self.environment["wildcard_options"] = arguments["wildcard_options"]

        if arguments["cleanup_clusters"]:
            self.environment["cleanup_clusters"] = True
            self.environment["wait_before_cleanup"] = arguments["wait_before_cleanup"]
            self.environment["delay_between_cleanup"] = arguments[
                "delay_between_cleanup"
            ]

        try:
            self.logging.debug("Saving test UUID to the working directory")
            uuid_file = open(self.environment["path"] + "/uuid", "x")
            uuid_file.write(self.environment["uuid"])
            uuid_file.close()
            self.logging.debug("Saving cluster_name_seed to the working directory")
            seed_file = open(self.environment["path"] + "/cluster_name_seed", "x")
            seed_file.write(self.environment["cluster_name_seed"])
            seed_file.close()
        except Exception as err:
            self.logging.error(f"Cannot write folder {self.environment['path']}")
            self.logging.error(err)
            sys.exit("Exiting...")

    def initialize(self):
        self.logging.info(f"Initializing platform {self.environment['platform']}")

        # OCM Login
        self.logging.info("Attempting to log in OCM using `ocm login`")
        ocm_login_command = (
            "ocm login --url="
            + self.environment["ocm_url"]
            + " --token="
            + self.environment["ocm_token"]
        )
        ocm_code, ocm_out, ocm_err = self.utils.subprocess_exec(ocm_login_command)
        sys.exit("Exiting...") if ocm_code != 0 else self.logging.info(
            "`ocm login` execution OK"
        )

    def download_kubeconfig(self, cluster_name, path):
        self.logging.debug(
            f"Downloading kubeconfig file for Cluster {cluster_name} on {path}/kubeconfig_{cluster_name}"
        )
        kubeconfig_code, kubeconfig_out, kubeconfig_err = self.utils.subprocess_exec(
            "ocm get /api/clusters_mgmt/v1/clusters/"
            + self.get_cluster_id(cluster_name)
            + "/credentials",
            extra_params={"cwd": path, "universal_newlines": True},
        )
        if kubeconfig_code == 0:
            kubeconfig_as_dict = yaml.load(
                json.loads(kubeconfig_out)["kubeconfig"], Loader=yaml.Loader
            )
            del kubeconfig_as_dict["clusters"][0]["cluster"][
                "certificate-authority-data"
            ]
            kubeconfig_path = path + "/kubeconfig_" + cluster_name
            with open(kubeconfig_path, "w") as kubeconfig_file:
                yaml.dump(kubeconfig_as_dict, kubeconfig_file)
            self.logging.debug(
                f"Downloaded kubeconfig file for Cluster {cluster_name} and stored at {path}/kubeconfig_{cluster_name}"
            )
            return kubeconfig_path

    def get_cluster_id(self, cluster_name):
        self.logging.debug(f"Obtaining Cluster ID for cluster name {cluster_name}")
        describe_code, describe_out, describe_err = self.utils.subprocess_exec(
            "ocm describe cluster --json " + cluster_name,
            extra_params={"universal_newlines": True},
        )
        return json.loads(describe_out).get("id", None) if describe_code == 0 else None

    def get_ocm_cluster_info(self, cluster_name):
        self.logging.info(f"Get Cluster metadata of {cluster_name}")
        resp_code, resp_out, resp_err = self.utils.subprocess_exec(
                "ocm get cluster " + self.get_cluster_id(cluster_name),
                extra_params={"universal_newlines": True},
        )
        try:
            cluster = json.loads(resp_out)
        except Exception as err:
            self.logging.error(f"Cannot load metadata for cluster {cluster_name}")
            self.logging.error(err)        
        metadata = {}           
        metadata['cluster_name'] = cluster.get("name", None)
        metadata['infra_id'] = cluster.get("infra_id", None)
        metadata['cluster_id'] = cluster.get("id", None)
        metadata['version'] = cluster.get("openshift_version", None)
        metadata['base_domain'] = cluster.get("dns", {}).get("base_domain", None)
        metadata['aws_region'] = cluster.get("region", {}).get("id", None)
        if 'compute' in cluster.get("nodes", {}):
            metadata['workers'] = cluster.get("nodes", {}).get("compute", None)
        else:  # when autoscaling enabled
            metadata['workers'] = cluster.get("nodes", {}).get("autoscale_compute", {}).get("min_replicas", None)
            metadata['workers_min'] = cluster.get("nodes", {}).get("autoscale_compute", {}).get("min_replicas", None)
            metadata['workers_max'] = cluster.get("nodes", {}).get("autoscale_compute", {}).get("max_replicas", None)
        metadata['workers_type'] = cluster.get("nodes", {}).get("compute_machine_type", {}).get("id", None)
        metadata['network_type'] = cluster.get("network", {}).get("type", None)
        return metadata

    def _wait_for_workers(
        self, kubeconfig, worker_nodes, wait_time, cluster_name, machinepool_name
    ):
        self.logging.info(
            f"Waiting {wait_time} minutes for {worker_nodes} workers to be ready on {machinepool_name} machinepool on {cluster_name}"
        )
        myenv = os.environ.copy()
        myenv["KUBECONFIG"] = kubeconfig
        result = [machinepool_name]
        starting_time = datetime.datetime.utcnow().timestamp()
        self.logging.debug(
            f"Waiting {wait_time} minutes for nodes to be Ready on cluster {cluster_name} until {datetime.datetime.fromtimestamp(starting_time + wait_time * 60)}"
        )
        while datetime.datetime.utcnow().timestamp() < starting_time + wait_time * 60:
            # if force_terminate:
            #     logging.error("Exiting workers waiting on the cluster %s after capturing Ctrl-C" % cluster_name)
            #     return []
            self.logging.info("Getting node information for cluster %s" % cluster_name)
            nodes_code, nodes_out, nodes_err = self.utils.subprocess_exec(
                "oc get nodes -o json",
                extra_params={"env": myenv, "universal_newlines": True},
            )
            try:
                nodes_json = json.loads(nodes_out)
            except Exception as err:
                self.logging.error(
                    f"Cannot load command result for cluster {cluster_name}. Waiting 15 seconds for next check..."
                )
                self.logging.error(err)
                time.sleep(15)
                continue
            nodes = nodes_json["items"] if "items" in nodes_json else []

            # First we find nodes which label nodePool match the machinepool name and then we check if type:Ready is on the conditions
            ready_nodes = (
                sum(
                    len(
                        list(
                            filter(
                                lambda x: x.get("type") == "Ready"
                                and x.get("status") == "True",
                                node["status"]["conditions"],
                            )
                        )
                    )
                    for node in nodes
                    if node.get("metadata", {})
                    .get("labels", {})
                    .get("hypershift.openshift.io/nodePool")
                    and machinepool_name
                    in node["metadata"]["labels"]["hypershift.openshift.io/nodePool"]
                )
                if nodes
                else 0
            )

            if ready_nodes == worker_nodes:
                self.logging.info(
                    f"Found {ready_nodes}/{worker_nodes} ready nodes on machinepool {machinepool_name} for cluster {cluster_name}. Stopping wait."
                )
                result.append(ready_nodes)
                result.append(int(datetime.datetime.utcnow().timestamp()))
                return result
            else:
                self.logging.info(
                    f"Found {ready_nodes}/{worker_nodes} ready nodes on machinepool {machinepool_name} for cluster {cluster_name}. Waiting 15 seconds for next check..."
                )
                time.sleep(15)
        self.logging.error(
            f"Waiting time expired. After {wait_time} minutes there are {ready_nodes}/{worker_nodes} ready nodes on {machinepool_name} machinepool for cluster {cluster_name}"
        )
        result.append(ready_nodes)
        result.append("")
        return result

    def create_cluster(self, platform, cluster_name):
        pass

    def delete_cluster(self, platform, cluster_name):
        pass

    def platform_cleanup(self):
        pass

    def watcher(self):
        pass


class PlatformArguments:
    def __init__(self, parser, config_file, environment):
        EnvDefault = self.EnvDefault

        parser.add_argument("--ocm-token", action=EnvDefault, env=environment, envvar="ROSA_BURNER_OCM_TOKEN", help="Token to access OCM API")
        parser.add_argument("--ocm-url", action=EnvDefault, env=environment, envvar="ROSA_BURNER_OCM_URL", help="OCM URL", default="https://api.stage.openshift.com")

        if config_file:
            config = configparser.ConfigParser()
            config.read(config_file)
            defaults = {}
            defaults.update(dict(config.items("Platform")))
            parser.set_defaults(**defaults)

        temp_args, temp_unknown_args = parser.parse_known_args()
        if not temp_args.ocm_token:
            parser.error("rosa-burner.py: error: the following arguments (or equivalent definition) are required: --ocm-token")

    # def __getitem__(self, item):
    #     return self.parameters[item] if item in self.parameters else None

    class EnvDefault(argparse.Action):
        def __init__(self, env, envvar, default=None, **kwargs):
            default = env[envvar] if envvar in env else default
            super(PlatformArguments.EnvDefault, self).__init__(
                default=default, **kwargs
            )

        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values)
