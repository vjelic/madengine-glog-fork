
# How to collect competitive library performance

## Profile the AI Model

The goal is to generate a list of library API config calls in a csv file (library_trace.csv). 
See [How to profile a Model](how-to-profile-a-model.md)

Examples:

```shell
madengine run --tags pyt_torchvision_alexnet --additional-context "{'guest_os': 'UBUNTU', 'tools': [{'name':'miopen_trace'}] }"
madengine run --tags pyt_torchvision_alexnet --additional-context "{'guest_os': 'UBUNTU', 'tools': [{'name':'rocblas_trace'}] }"
```
or alternatively, collect everything in one run

```shell
madengine run --tags pyt_torchvision_alexnet --additional-context "{'guest_os': 'UBUNTU', 'tools': [{'name':'miopen_trace'},{'name':'rocblas_trace'}] }"
```

## Measure competitive library configuration performance

Here, the library config trace collected in previous section is used to collect competitive performance. This section works the same on AMD and NVIDIA gpus. 

The code assumes library_trace.csv exists in root folder, and produces a library_perf.csv. 

Examples:

```shell
madengine run --tags pyt_library_config_perf
```
