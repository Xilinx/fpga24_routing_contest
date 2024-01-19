# Alpha Submission

In order to ensure that the contest environment is able to support all router
entries ahead of the final submission deadline, a mandatory step for continued
participation in the contest is the submission of an early "alpha" release.
The performance of this alpha submission will have **zero** effect on the
final submission score; instead, the organizers will endeavour to work with
contestants to ensure that the runtime environment is as desired.
Contestants will receive private feedback from the organizers assessing the
performance of just their router on the released benchmark suite (plus a hidden
benchmark) when run on contest hardware.

## Key Details

* Alpha submission is mandatory for continued participation in the contest
* Performance of alpha submissions will be shared privately with contestants and will not impact the final score
* Alpha submissions will be evaluated on [AMD Heterogeneous Compute Cluster (HACC)](https://www.amd-haccs.io/) hardware
* Contestants are required to use [Apptainer](https://apptainer.org/docs/user/latest/) to containerize their submission (details below)

## Runtime Environment

Aside from running under Linux without network access, no restrictions are
placed on the languages, software dependencies, or runtime environment that
contestants may use to implement their router. In order to enable this platform
independence, contestants must containerize their router and runtime environment
with the [Apptainer](https://apptainer.org/docs/user/latest/) framework.

### Apptainer

From the [Apptainer documentation](https://apptainer.org/docs/user/latest/introduction.html):
> Apptainer is a container platform. It allows you to create and run containers that package up pieces of software in a way that is portable and reproducible. You can build a container using Apptainer on your laptop, and then run it on many of the largest HPC clusters in the world, local university or company clusters, a single server, in the cloud, or on a workstation down the hall. Your container is a single file, and you don’t have to worry about how to install all the software you need on each different operating system.

Apptainer containers may be described with a `*.def`
[definition file](https://apptainer.org/docs/user/latest/definition_files.html)
that specifies the base operating system image, and any further customisations
(such as library installations) required to support an application. A
definition file can then be compiled into an executable `*.sif` image which
allows the application to be run in an isolated environment.

The [contest repository](https://github.com/Xilinx/fpga24_routing_contest/)
has been updated with example `*.def` files in the `alpha_submission` directory
for both `rwroute` and `nxroute-poc`. To build and run the default container
(which on a fresh clone would be `rwroute`) one would just run:

```
make run-container
```

This is roughly equivalent to:
```
apptainer build rwroute_container.sif alpha_submission/rwroute_container.def
apptainer exec --pid --home `pwd` --rocm --bind /etc/OpenCL --mount src=/tools/,dst=/tools/,ro rwroute_container.sif make
```

The `apptainer build` command creates an image from the `rwroute_container.def`
definition, and the `apptainer exec` command runs the given command inside this image.
The Apptainer command line options do the following:

* `--pid` runs the container in a new process ID namespace to ensure processes
spawned by the container are not orphaned if the container is killed.
* ``--home `pwd` `` sets the container home directory to be the current directory
* `--rocm --bind /etc/OpenCL` configures [GPU Access](#gpu-access)
* `--mount ...` creates a read-only mount of the host system's `/tools`
directory to the container's `/tools` directory, which allows the container to
access the host Vivado installation.

The remainder of the Apptainer command line simply runs the default make target from inside the
container.

Finally, in order to aid in development the Makefile target:

```
make test-container
```

has also been provided. This target is identical to the `run-container` target,
except that results are only collected for the `boom_med_pb` benchmark, instead
of collecting results for every benchmark. This allows contestants to quickly
test their Apptainer flow and avoid overloading shared resources should they
be working on a shared cluster.

For further information about working with Apptainer containers please refer to
[the user documentation](https://apptainer.org/docs/user/latest/introduction.html).

### GPU Access

It is possible to access AMD GPU resources on the host from an Apptainer
container. The directory `alpha_submission/opencl_example` contains a sample
`*.def` file that builds a [C++/OpenCL "Hello World" example](https://github.com/cqcallaw/ocl-samples).
To run this example:

```
make run-opencl-example
```

This `make` target builds a `*.sif` image from the
`opencl_example_container.def` definition file and runs it with the command:

```
apptainer run --pid --home `pwd` --rocm --bind /etc/OpenCL opencl_example_container.sif
```

The `--rocm` switch enables AMD ROCm support in the container. The
`--bind /etc/OpenCL` switch mounts the host OpenCL directory in the container,
which is required to allow the containerized OpenCL stack to discover the host
resources.

Please note that contestants are free to use GPU interfaces other than OpenCL,
such as [AMD HIP](https://github.com/ROCm-Developer-Tools/HIP).

## Submission Format

Contestants are required to submit a clone of the contest
repository which has been modified to run their router in Apptainer.
Specifically, organizers must be able to run the submitted router by calling only
the `make run-container` target. By default, in a fresh checkout of the contest
repository, this target will run `rwroute` in an Apptainer container.
Thus in addition to their router contestants must supply a custom `*.def` file
in the `alpha_submission` directory, as well as a Makefile that has been
modified to run their router by default. To set the default router in the
Makefile contestants must change the value of the `ROUTER` variable from
`rwroute` to the name of their router.

Starting from a clone of the contest repository that has already had its
Makefile `ROUTER` variable modified such that `make` invokes the contestant
router, one would just execute:

```
make distclean-and-package-submission
```

Which generates a submission artifact named
`<router_name>_submission_<timestamp>.tar.gz` in the current directory.
Internally, this executes the following commands:

```
make distclean
tar -czf ../<router_name>_submission_<timestamp>.tar.gz .
mv ../<router_name>_submission_<timestamp>.tar.gz .
```

Note that `make distclean` will delete all unrouted design files, routed
results and logs, as well as the device description. The organizers will then
evaluate the artifact with a process similar to the following:

```
mkdir <router_name>_alpha_submission
cd <router_name>_alpha_submission
tar -xvf <router_name>_submission_<timestamp>.tar.gz
make run-container
```

### Closed-Source Submissions

While contestants are strongly encouraged to open-source their solutions at the
conclusion of the contest, there is no requirement to do so. In such cases,
it is still necessary to use the flow described above to produce a binary only
submission. That is, any precompiled router must still work inside Apptainer
and be invoke-able using `make run-container` on the contest hardware.
