# Docker Stack for IMMAD

This repository contains the Dockerfiles and Bash scripts for the IMMAD docker image stack.
All images are based on the [jupyter/minimal-notebook](https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html#jupyter-minimal-notebook).

There are two images corresponding to two targets:
- `immad` – An IMMAD image.
- `init-user` – An init container for setting up new user, which is deployed whenever a new user is created.

## Development

### Development environment

The repository uses the [doit automation tool](https://pydoit.org/) to automate tasks related to this repository.

To use this system, setup a build end testing environment and install the dependencies with:

```console
pip install -r requirements-dev.txt
```

### Build images locally

To build the images, run `doit build` (tested with *docker buildx* version v0.8.2).

The build system will attempt to detect the local architecture and automatically build images for it (tested with amd64 and arm64).
All commands `build`, `tests`, and `up` will use the locally detected platform and use a version tag based on the state of the local git repository.
However, you can also specify a custom platform or version with the `--platform` and `--version` parameters, example: `doit build --arch=arm64 --version=my-version`.

You can specify target stacks to build with `--target`, example: `doit build --target immad --target init-user`.

Finally, you have to push the image using `docker push`.

### Creating a release

We distinguish between _regular_ releases and _special_ releases, where the former follow the standard versioning scheme (`v2022.1001`) and the latter would be specific to a certain use case, e.g., a workshop with dedicated requirements.
To create a regular release, set up a development environment, and then use `bumpver`:
```console
bumpver update
```
This will update the README.md file, make a commit, tag it, and then push both to the repository to kick off the build and release flow.

To create a _special_ release, simply tag it with a tag name of your choice with the exception that it cannot start with the character `v`.


