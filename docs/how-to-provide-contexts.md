
# How to provide Contexts

Each model in models.json specifies a `dockerfile` that represents a collection of Dockerfiles, that start with the string. All Dockerfiles have individual context, given by `# CONTEXT` comment in the header of file. madengine automatically detects the hardware context within which it runs. Examples of hardware contexts include Host Operating System or GPU vendor. 

The Dockerfile collection is filtered through the detected hardware contexts. For each Dockerfile context that exists in the detected contexts, the value is compared. All common values have to match for the Dockerfile to be selected. The model is run for all filtered Dockerfiles. 

Additional contexts may be specified through `--additional-context` argument. 
For example, for models supporting both `'guest_os'` as UBUNTU and CENTOS, one may choose to run only the CENTOS image using `--additional-context "{'guest_os': 'CENTOS'}"'. Without this additional context, both UBUNTU and CENTOS images are used to run the model. 

Additional contexts may also be specified through a json file, given by `--additional-context-file` argument. 
For example, for models supporting both `'guest_os'` as UBUNTU and CENTOS, one may choose to run only the CENTOS image using `--additional-context-file addln_ctx.json, where the contents of addln_ctx.json might be

```json
{
  "guest_os": "CENTOS"
}
```

## Changing image from commandline or file

The `--additional-context` and `--additional-context-file` can be used to pass in a user-provided image. 

```shell
madengine run --tags {model} --additional-context "{'MAD_CONTAINER_IMAGE': 'rocm/pytorch:my_local_tag'}" 
```

or using file for `--additional-context-file` as 

```json
{
  "MAD_CONTAINER_IMAGE": "rocm/pytorch:my_local_tag"
}
```

## Changing base docker from commandline or file

The `--additional-context` and `--additional-context-file` can be used to override `BASE_DOCKER` used in the `FROM` line of Dockerfiles. 

```shell
madengine run --tags {model} --additional-context "{'docker_build_arg':{'BASE_DOCKER':'compute-artifactory.amd.com:5000/...' }}" 
```

or using file for `--additional-context-file` as 

```json
{
  "docker_build_arg": {"BASE_DOCKER": "compute-artifactory.amd.com:5000/..."}
}
```

## Providing environment variables to docker container 

The `--additional-context` and `--additional-context-file` can be used to provide environment variables to docker containers.

 ```shell
madengine run --tags {model} --additional-context "{'docker_env_vars':{'HSA_ENABLE_SDMA':'0'} }" 
```

or using file for --additional-context-file as

```json
{
  "docker_env_vars": {"HSA_ENABLE_SDMA": "0"}
}
```

There are also model-environment variables that one can change at madengine runtime.

```json
{
  "docker_env_vars": {"MAD_MODEL_NUM_EPOCHS": "5"}
}
```
This example will set the number of epochs to `5` for a particular model. Please see [How to add a Model](how-to-add-a-model.md) for the list of model-environment variables available.

## Mounting host folders inside docker container 
The `--additional-context` and `--additional-context-file` can be used to provide mount paths into docker containers.

 ```shell
madengine run --tags {model} --additional-context "{'docker_mounts':{'/data-path-inside-container':'/data-path-on-host'} }" 
```

or using file for --additional-context-file as

```json
{
  "docker_mounts": {"/data-path-inside-container": "/data-path-on-host"}
}
```

## Running pre/post model run scripts

The `--additional-context` and `--additional-context-file` can be used to provide scripts to be run before and after the model run. Commands that encapsulate the model run script can also be provided. 

```shell
--additional-context "{'pre_scripts':[{'path':'your/path/to/pre_script.sh', 'args':'-r'}], 'encapsulate_script':'your/path/to/encapsulate_script.sh', 'post_scripts':[{'path':'your/path/to/post_script.sh', 'args':'-p'}]}"
```

or using file for --additional-context-file as

```json
{
  "pre_scripts":[
      {
          "path":"your/path/to/pre_script.sh", 
          "args":"-r"
      }
  ],
  "encapsulate_script":"your/path/to/encapsulate_script.sh",
  "post_scripts":[
      {
          "path":"your/path/to/post_script.sh", 
          "args":"-p"
      }
  ]
}
```

These scripts have their respective directories `/scripts/common/pre_scripts/` and `/scripts/common/post_scripts/`, but it is not necessary to place them there. If you do decide

to place them in these directories you will need to append their respective paths to your script name for the path variable(s) in the additional-context and additional-context-file.
Also note that you can run multiple post and pre scripts.

## Selecting gpus and cpus within docker container
The `--additional-context` and `--additional-context-file` can be used to provide a sub-list of cpus or gpus, available within a container.

The gpus/cpus are comma-separated, and ranges may be denoted with hyphen.

```shell
--additional-context "{'docker_gpus':'0,2-4,5-5,7', 'docker_cpus':'14-18,32,44-44,62'}"
``` 

or using file for --additional-context-file as

```json
{
  "docker_gpus":"0,2-4,5-5,7", 
  "docker_cpus":"14-18,32,44-44,62"
}
```

## Providing model script with arguments 

Given additional context can modify existing model arguments to dlm run script by adding "model_args" value
Note: the values given through "model_args" are dependant on arguments the selected run script is expecting 

```shell
--additional-context "{'model_args':'--model_name_or_path bigscience/bloom'}" 
```

or using the file for --additional-context-file as 

```shell
{
    "model_args": "--model_name_or_path bigscience/bloom"
}
```
