# How to profile a Model

madengine now supports several tools for profiling. This is provided via the `additional-context` option and the `additional-context-file`. (Given the complexity of these configuration snippets, we recommend to use the `additional-context-file`.)

For example to use the `rocprof` tool, one just needs to provide a `additional-context-file` with the following:

```json
{
  "tools": [{
      "name": "rocprof" 
  }]
}
```

This results in a file named `rocprof_output` which contains all the resulting profiling information.

NOTE: This feature only supports profiling a single workload so the tag provided should be the workload's name (e.g. `pyt_torchvison_alexnet`)

## Changing the default behavior

Providing an `additional-context-file` with the contents above will use `rocprof` default behavior. The default behavior for supported tools can be found in `./scripts/common/tools.json`. There are two keys we can change that will modify a tool's behavior, namely `cmd` and `env_vars`. The `cmd` key's value will be the full command to be placed before the python command that runs our model.

For example, we can change then default command of `rocprof` with the following:

```json
{
  "tools": [{
    "name": "rocprof",
    "cmd": "rocprof --timestamp on "
  }]
}
```

The above configuration changes the default behavior to use `timestamp` instead of `hip-trace`. (NOTE: `rocprof` is a binary itself and so is required in our `cmd` value.)

There is also support for setting tool specific environment variables.

```json
{
  "tools": [{
    "name": "rocprof",
    "env_vars": {
      "NCCL_DEBUG": "INFO"
    }
  }]
}

```

## Stackable design

The profiling/tracing tools follow a stackable design, where multiple tools can be stacked on top of each other. The order in which the tools are specified is the same order in which the tools are applied, with the initial tool forming the innermost envelope around the workload, and the final tool forming the outermost envelope around the workload. 

In the example below, rocprof is the innermost tool, and miopen_trace is the outermost. During runtime, the outermost tool setup is done first, followed by innermost tool setup. Then, the workload is run. The innermost scaffold is deconstucted first, followed by outermost scaffold. 

```json
{
  "tools": [{
    "name": "rocprof"
  },
  {
    "name": "miopen_trace"
  }]
}
```

## List of supported tools for profiling

### rocprof
ROCprofiler can be used to profile the application, with the rocprof tool. 

```json
{
  "tools": [{
    "name": "rocprof"
  }]
}
```

### rpd
This mode is used to profile using rpd.

```json
{
  "tools": [{
    "name": "rpd"
  }]
}
```

### rocblas_trace
This mode is used to trace rocBLAS calls within an application. The rocBLAS calls reside in the output log file. This tool also generates a library_trace csv file that contains the summary of library, configs.

```json
{
  "tools": [{
    "name": "rocblas_trace"
  }]
}
```

### miopen_trace
This mode is used to trace MIOpen calls within an application. The MIOpen calls reside in the output log file. This tool also generates a library_trace csv file that contains the summary of library, configs.

```json
{
  "tools": [{
    "name": "miopen_trace"
  }]
}
```

### tensile_trace
This mode is used to trace Tensile calls within an application. The Tensile calls reside in the output log file. This tool also generates a library_trace csv file that contains the summary of library, configs.

```json
{
  "tools": [{
    "name": "tensile_trace"
  }]
}
```

### rccl_trace
This mode is used to trace RCCL calls within an application. The RCCL calls reside in the output log file.  

```json
{
  "tools": [{
    "name": "rccl_trace"
  }]
}
```
### gpu_info_power_profiler & gpu_info_vram_profiler
For `gpu_info_power_profiler`:

```json
{"tools": [{"name": "gpu_info_power_profiler"}]}
```

For `gpu_info_vram_profiler`:

```json
{"tools": [{"name": "gpu_info_vram_profiler"}]}
```

Currently, `gpu_info_power_profiler` and `gpu_info_vram_profiler` supports ROCm and CUDA, and it profiles real-time power and vram consumption for the workloads. The ouput of the profile is a `gpu_info_power_profiler_output.csv`or `gpu_info_vram_profiler_output.csv`.

The default `env_vars` for the `gpu_info_power_profiler` `gpu_info_vram_profiler` can be found in `madengine/scripts/common/tools.json`:

```json
"env_vars": {"DEVICE":"0", "SAMPLING_RATE":"0.1", "MODE":"power", "DUAL-GCD":"false"}
```

These two profiling tools share the same backend and
- `DEVICE` can be `"all"` or a string of device index like `"0"` or `"0,1,2"`. When the `MODE` is `"power"`, the device must be a "master" GCD on an OAM (the profiler will issue an error if the device is a secondary die). The tool automatically filters out the "master" GCDs when the value of this field is `"all"`.
- `SAMPLING_RATE` is the sampling interval for the profiler in **seconds**.
- `MODE` supports `"power"` and `"vram"`.
- `DUAL-GCD` launches the same workload on two GCDs if value is "true" **and** the container got two GCDs; therefore, to enable `DUAL_GCD`, one needs to set `"n_gpus": "2"` for the model in `models.json`.


## For developers

This functionality is provided by pre- and post-scripts, which initially sets up the tool and then saves the wanted information while also cleaning up. These scripts are found in `./scripts/common/pre_scripts` and `./scripts/common/post_scripts`. The end result, in some cases, will be a directory called `tool_name_output` and will contain all of the results. The pre-scripts will deal with initial setup and installation, while the post-scripts deals with saving to output directory and cleanup.

The `./scripts/common/tools.json` file is where the tools default behavior is defined. See previous tools there for examples.


