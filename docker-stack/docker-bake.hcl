# docker-bake.hcl
variable "PYTHON_VERSION" {}
variable "AIIDA_VERSION" {}
variable "AIIDALAB_VERSION" {}
variable "AIIDALAB_HOME_VERSION" {}
variable "AIIDALAB_WIDGETS_BASE_VERSION" {}
variable "AIIDALAB_QUANTUM_ESPRESSO_VERSION" {}
variable "PIP_VERSION" {}
variable "PYMATGEN_VERSION" {}

variable "JUPYTER_BASE_IMAGE" {
  default = "jupyter/minimal-notebook:python-${PYTHON_VERSION}"
}

variable "TAG" {
  default = "newly-build"
}

variable "ORGANIZATION" {
  default = "htdang"
}

variable "REGISTRY" {
  default = "docker.io/"
}

variable "PLATFORMS" {
  default = ["linux/amd64"]
}

variable "TARGETS" {
  default = ["immad", "init-user"]
}

function "tags" {
  params = [image]
  result = [
    "${REGISTRY}${ORGANIZATION}/${image}:${TAG}",
  ]
}

group "default" {
  targets = "${TARGETS}"
}

target "immad-meta" {
  tags = tags("immad")
}

target "immad" {
  inherits = ["immad-meta"]
  context = "stack/immad"
  platforms = "${PLATFORMS}"
  args = {
    "BASE" = "${JUPYTER_BASE_IMAGE}"
    "AIIDA_VERSION" = "${AIIDA_VERSION}"
    "AIIDALAB_VERSION" = "${AIIDALAB_VERSION}"
    "AIIDALAB_HOME_VERSION" = "${AIIDALAB_HOME_VERSION}"
    "AIIDALAB_WIDGETS_BASE_VERSION" = "${AIIDALAB_WIDGETS_BASE_VERSION}"
    "AIIDALAB_QUANTUM_ESPRESSO_VERSION" = "${AIIDALAB_QUANTUM_ESPRESSO_VERSION}"
    "PIP_VERSION" = "${PIP_VERSION}"
    "PYMATGEN_VERSION" = "${PYMATGEN_VERSION}"
  }
}

target "init-user-meta" {
  tags = tags("init-user")
}

target "init-user" {
  inherits = ["init-user-meta"]
  context = "stack/init-user"
  platforms = "${PLATFORMS}"
  args = {
    "BASE" = "alpine:latest"
  }
}

