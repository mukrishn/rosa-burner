# Rosa Platforms

Classes related to ROSA platform

To use this platform, select rosa as platform parameter:
`hcp-burner --platform rosa`

## Platforms Arguments

To use the config file, define parameters related to platform under the `[Platform:Rosa]` section

| Argument                 | Default Value     | Config file variable | Environment Variable           |
|--------------------------|-------------------|----------------------|--------------------------------|
| --rosa-env                      | staging           |                              | HCP_BURNER_ROSA_ENV             |
| --aws-account-file              |                   |                              | HCP_BURNER_AWS_ACCOUNT_FILE     |
| --aws-profile                   |                   |                              | HCP_BURNER_AWS_PROFILE          |
| --aws-region                    | us-east-2         |                              | HCP_BURNER_AWS_REGION           |
| --oidc-config-id                |                   |                              | HCP_BURNER_OIDC_CONFIG_ID       |
| --common-operator-roles         |                   |                              |                                  |
| --autoscale                     | false             |                              | HCP_BURNER_AUTOSCALE             |
| --min-replicas                  | 3                 |                              | HCP_BURNER_MIN_REPLICAS          |
| --max-replicas                  | 10                |                              | HCP_BURNER_MAX_REPLICAS          |
| --add-hcp-infra                 | false             |                              | HCP_BURNER_ADD_HCP_INFRA        |
| --infra-size                    | m5.xlarge         |                              | HCP_BURNER_INFRA_SIZE           |
| --extra-machinepool-name        |                   |                              | HCP_BURNER_MACHINE_POOL_NAME    |
| --extra-machinepool-machine-type| m5.xlarge         |                              | HCP_BURNER_MACHINE_POOL_MACHINE_TYPE |
| --extra-machinepool-replicas    | 3                 |                              | HCP_BURNER_MACHINE_POOL_REPLICAS |
| --extra-machinepool-count       | 1                 |                              | HCP_BURNER_MACHINE_POOL_COUNT  |
| --extra-machinepool-labels      |                   |                              | HCP_BURNER_MACHINEPOOL_LABELS   |
| --extra-machinepool-taints      |                   |                              | HCP_BURNER_MACHINEPOOL_TAINTS   |
| --extra-machinepool-autoscale   | false             |                              | HCP_BURNER_MACHINE_POOL_AUTOSCALE |
| --extra-machinepool-min-replicas| 3                 |                              | HCP_BURNER_MACHINE_POOL_MIN_REPLICAS |
| --extra-machinepool-max-replicas| 20                |                              | HCP_BURNER_MACHINE_POOL_MAX_REPLICAS |
| --extra-machinepool-use-spot-instances | false       |                              | HCP_BURNER_MACHINE_POOL_USE_SPOT_INSTANCES |
| --extra-machinepool-spot-max-price |                   |                              | HCP_BURNER_MACHINE_POOL_SPOT_MAX_PRICE |

`--extra-machinepool-count` is the total number of physical pools. With
multi-AZ clusters, ROSA distributes those pools across the availability zones
and distributes the total replica count across all of them. For example, a
count of `9` across three AZs creates three pools per AZ.
