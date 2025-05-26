# How to Run Mulit-Node

**NOTE: all of the commands/examples shown below are only showing the multi-node arguments - you will probably need to add the other arguments for your run on top of these.**

## Multi-Node Runners

There are two mulit-node `RUNNER`s in DLM/MAD, namely `torchrun` and `mpirun` (coming soon). Each of these `RUNNER`s are enabled in the model's bash script via the environment variable `MAD_MULTI_NODE_RUNNER`. For example in the `pyt_megatron_lm_train_llama2_7b` script, this feature is enabled with the following code

```bash
run_cmd="
        $MAD_MULTI_NODE_RUNNER \
        $TRAIN_SCRIPT \
        $GPT_ARGS \
        $DATA_ARGS \
        $OUTPUT_ARGS \
        $EXTRA_ARGS \
        --save $CHECKPOINT_PATH \
        --load $CHECKPOINT_PATH
"
```

Note the use of the `$MAD_MULTI_NODE_RUNNER` environment variable. This environment variable will be expanded into which ever `RUNNER` is chosen at DLM/MAD runtime.

### torchrun

Default `RUNNER` is `torchrun` , `MASTER_ADDR` is `localhost` , `NNODES` is 1 , `NODE_RANK` is 0, additional context `multi_node_args` is not necessary to run on single node 

```bash
madengine run --tags {model}
```

#### Two-Node Example

Using the `torchrun` `RUNNER` requires you to execute the DLM/MAD CLI command on each node manually. `NCCL_SOCKET_IFNAME` , `GLOO_SOCKET_IFNAME` needs to be set using `ifconfig` from `net-tools`

```bash
apt install net-tools
```

So let's assume the first node is our "master" node and has an IP=10.227.23.63

On first node, run the following:

```bash
madengine run --tags {model} --additional-context "{'multi_node_args': {'RUNNER': 'torchrun', 'MASTER_ADDR': '10.227.23.63', 'MASTER_PORT': '400', 'NNODES': '2', 'NODE_RANK': '0'}}"
```

On the second node, run the following:

```bash
madengine run --tags {model} --additional-context "{'multi_node_args':{'RUNNER': 'torchrun', 'MASTER_ADDR': '10.227.23.63', 'MASTER_PORT': '400', 'NNODES': '2', 'NODE_RANK': '1'}}"
```

### mpirun

Coming Soon!

## Sharing Data

DLM/MAD multi-node feature assumes the dataset is in a shared-file system for all participating nodes. For example, look at the following 2-node run of the Megatron-LM Llama2 workload.

On the first node (assumed to be master node), run the following:

```bash
madengine run --tags pyt_megatron_lm_train_llama2_7b --additional-context "{'multi_node_args': {'RUNNER': 'torchrun', 'MASTER_ADDR': '10.194.129.113', 'MASTER_PORT': '4000', 'NNODES': '2', 'NODE_RANK': '0', 'NCCL_SOCKET_IFNAME': 'ens14np0', 'GLOO_SOCKET_IFNAME': 'ens14np0'}}" --force-mirror-local /nfs/data
```

On the second node, run the following:

```bash
madengine run --tags pyt_megatron_lm_train_llama2_7b --additional-context "{'multi_node_args': {'RUNNER': 'torchrun', 'MASTER_ADDR': '10.194.129.113', 'MASTER_PORT': '4000', 'NNODES': '2', 'NODE_RANK': '1', 'NCCL_SOCKET_IFNAME': 'ens14np0', 'GLOO_SOCKET_IFNAME': 'ens14np0'}}" --force-mirror-local /nfs/data
```

You can see at the end of these commands, we are pointing DLM/MAD to the shared-file system where the data can be located.

**NOTE: The above commands assumes the shared-file system is mounted at `/nfs` in the commands above. If this is not the case and a user simply copies/pastes the above commands on two nodes, DLM/MAD will create a folder called `nfs` on each node and copy the data there, which is not desired behavior.**

## TODO

### RUNNER

- [ ] mpirun (requires ansible integration)

### Job Schedulare

- [ ] SLURM
- [ ] Kubernetes

### Design Consideration

- [ ] Having the python model script launched by individual bash scripts can be limiting for multi-node. Perhaps we can explore a full python workflow for multi-node and only the job scheduler uses a bash script like SLURM using sbatch script.
