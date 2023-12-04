# Alpha Submission Containers

This directory contains example [Apptainer](https://apptainer.org/docs/user/latest/)
definition files that show how to containerize a router for submission.
Contestants not building on top of RWRoute are required to provide a new file named `<router_name>_container.def`
builds the environment for running their router.

For further details on the alpha submission please refer to
[this webpage](https://xilinx.github.io/fpga24_routing_contest/alpha_submission.html).

The contents of this directory are as follows:

* `rwroute_container.def` -- an example Apptainer definition file for `rwroute`
* `nxroute-poc_container.def` -- an example Apptainer definition file for `nxroute-poc` (this is actually a link to `rwroute_container.def` since both routers require an identical environment)
* `opencl_example/opencl_example_container.def` -- an example Apptainer definition file for a C++/OpenCL "Hello World" application
