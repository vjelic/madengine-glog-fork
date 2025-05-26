# rocEnvTool: System Environment collection tool

This tool is responsible for collecting some important details from the machine that we run on. 
Note: This tool needs sudo previlege access to collect some information.

## How to run this tool

This tool needs sudo access. 
* To gather full configuration details run the following command:

```
sudo python rocenv_tool.py
```

This dumps out a folder called : .sys_config_files inside the current working directory which contains multiple folders with logs available.

* To run the lite version run the below command. Make sure to update your selected tags via roc_env.json file. By default it dumps out os_information.

```
sudo python rocenv_tool.pyy --lite
```

## Details that are collected via this tool:

The below tags denote the details that are collected via this tool. 
These are the tags that are available for user if they wish to use lite version.

### Tags:
*  hardware_information
*  cpu_information
*  gpu_information
*  bios_settings
*  os_information
*  dmsg_gpu_drm_atom_logs
*  amdgpu_modinfo
*  memory_information
*  rocm_information
*  rocm_repo_setup
*  rocm_packages_installed
*  rocm_env_variables
*  rocm_smi
*  ifwi_version
*  rocm_smi_showhw
*  rocm_smi_pcie
*  rocm_smi_pids
*  rocm_smi_topology
*  rocm_smi_showserial
*  rocm_smi_showperflevel
*  rocm_smi_showrasinfo
*  rocm_smi_showxgmierr
*  rocm_smi_clocks
*  rocm_smi_showcompute_partition
*  rocm_smi_nodesbwi
*  rocm_info
*  pip_list
*  numa_balancing
