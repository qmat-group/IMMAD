ARG BASE
FROM ${BASE}

LABEL maintainer="IMMAD Project <hung.dangthe@phenikaa-uni.edu.vn>"

USER root

RUN apt-get update --yes && \
    apt-get install --yes --no-install-recommends \
    # for apps which need to install pymatgen:
    # https://pymatgen.org/installation.html#installation-tips-for-optional-libraries
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/

ARG AIIDA_VERSION
ARG PYMATGEN_VERSION
ARG PIP_VERSION

ENV AIIDA_PROFILE_NAME default

# Pin shared requirements in the base environemnt.
# The lower bound of aiida-core is set to the version of aiida-core to prevent
# lower aiida-core DB version installed and trigger database downgrade.
RUN echo "pip==${PIP_VERSION}" > /opt/requirements.txt && \
    echo "aiida-core>=${AIIDA_VERSION},<3" >> /opt/requirements.txt && \
    echo "pymatgen==${PYMATGEN_VERSION}" >> /opt/requirements.txt

# Install the shared requirements.
RUN mamba install --yes \
     aiida-core=${AIIDA_VERSION} \
     mamba-bash-completion \
     --file /opt/requirements.txt \
     && mamba clean --all -f -y && \
     fix-permissions "${CONDA_DIR}" && \
     fix-permissions "/home/${NB_USER}"

# Pin shared requirements in the base environemnt.
RUN cat /opt/requirements.txt | xargs -I{} conda config --system --add pinned_packages {}

# Configure pip to use requirements file as constraints file.
ENV PIP_CONSTRAINT=/opt/requirements.txt

# Enable verdi autocompletion.
RUN mkdir -p "${CONDA_DIR}/etc/conda/activate.d" && \
     echo 'eval "$(_VERDI_COMPLETE=bash_source verdi)"' >> "${CONDA_DIR}/etc/conda/activate.d/activate_aiida_autocompletion.sh" && \
     chmod +x "${CONDA_DIR}/etc/conda/activate.d/activate_aiida_autocompletion.sh" && \
     fix-permissions "${CONDA_DIR}"

# Install the load-singlesshagent.sh script as described here:
# https://aiida.readthedocs.io/projects/aiida-core/en/v2.0.0/howto/ssh.html#starting-the-ssh-agent
# The startup of this script is configured in the before-notebook.d/20_setup-ssh.sh file.
COPY load-singlesshagent.sh /opt/bin/

# Add ~/.local/bin to PATH where the dependencies get installed via pip
ENV PATH=${PATH}:/home/${NB_USER}/.local/bin

# Add conda envs_dirs in home directory,
# which will persist between container invocation
# NOTE: The order here is important!
# We want conda to create environments in ~/.conda/ by default
RUN conda config --system --add envs_dirs /opt/conda
RUN conda config --system --add envs_dirs "~/.conda/envs"

# Install AiiDAlab

# Install additional system packages
RUN apt-get update --yes && \
     apt-get install --yes --no-install-recommends \
     curl \
     povray \
     vim \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/*

# Install aiidalab package
ARG AIIDALAB_VERSION
RUN mamba install --yes \
     aiidalab=${AIIDALAB_VERSION} \
     && mamba clean --all -f -y && \
     fix-permissions "${CONDA_DIR}" && \
     fix-permissions "/home/${NB_USER}"

# Pin aiidalab version.
RUN echo "aiidalab==${AIIDALAB_VERSION}" >> /opt/requirements.txt
RUN conda config --system --add pinned_packages "aiidalab=${AIIDALAB_VERSION}"

# Enable aiidalab autocompletion
RUN echo 'eval "$(_AIIDALAB_COMPLETE=bash_source aiidalab)"' >> "${CONDA_DIR}/etc/conda/activate.d/activate_aiida_autocompletion.sh"

# Install the aiidalab-home app.
ARG AIIDALAB_HOME_VERSION
RUN git clone https://github.com/aiidalab/aiidalab-home && \
     cd aiidalab-home && \
     git checkout v"${AIIDALAB_HOME_VERSION}" && \
     pip install --quiet --no-cache-dir "./" && \
     fix-permissions "./" && \
     fix-permissions "${CONDA_DIR}" && \
     fix-permissions "/home/${NB_USER}"

# Install and enable appmode.
RUN git clone https://github.com/oschuett/appmode.git && \
     cd appmode && \
     git checkout v0.8.0
COPY gears.svg ./appmode/appmode/static/gears.svg
RUN pip install ./appmode --no-cache-dir && \
     jupyter nbextension enable --py --sys-prefix appmode && \
     jupyter serverextension enable --py --sys-prefix appmode

# Install other default apps: aiidalab-widgets-base and quantum-espresso
ARG AIIDALAB_WIDGETS_BASE_VERSION
RUN git clone https://github.com/aiidalab/aiidalab-widgets-base && \
     cd aiidalab-widgets-base && \
     git checkout v"${AIIDALAB_WIDGETS_BASE_VERSION}" && \
     pip install --quiet --no-cache-dir "./" && \
     fix-permissions "./"

ARG AIIDALAB_QUANTUM_ESPRESSO_VERSION
RUN git clone https://github.com/aiidalab/aiidalab-qe && \
     cd aiidalab-qe && \
     git checkout v"${AIIDALAB_QUANTUM_ESPRESSO_VERSION}" && \
     pip install --quiet --no-cache-dir "./" && \
     fix-permissions "./"

# pseudopotentials
RUN mamba install --yes aiida-pseudo

# Copy start-up scripts for AiiDA and AiiDAlab.
COPY before-notebook.d/* /usr/local/bin/before-notebook.d/

# Configure AiiDAlab environment.
ENV AIIDALAB_HOME /home/${NB_USER}
ENV AIIDALAB_APPS ${AIIDALAB_HOME}/apps
ENV AIIDALAB_DEFAULT_GIT_BRANCH master


# Specify which apps to install in addition to the home app. The
# AIIDALAB_DEFAULT_APPS variable should be a whitespace-delimited variable
# where each entry must follow the specifier format used by `aiidalab install`.
#
# Example for setting the AIIDALAB_DEFAULT_APPS variable:
#
#   AIIDALAB_DEFAULT_APPS="aiidalab-widgets-base quantum-espresso==20.12.0"
#
# Please note that multiple entries must be whitespace delimited.
# Please see `aiidalab install --help` for more information.
#ENV AIIDALAB_DEFAULT_APPS "aiidalab-widgets-base quantum-espresso"

# Specify default factory reset (not set):
ENV AIIDALAB_FACTORY_RESET ""

USER ${NB_USER}

WORKDIR "/home/${NB_USER}"

RUN mkdir -p ${AIIDALAB_APPS}

# When a Jupyter notebook server looses a connection to the frontend,
# it keeps the messages in a buffer. If there is a background thread running
# and trying to update the frontend, the buffer grows indefinitely,
# eventually consuming all available RAM.
# See https://github.com/aiidalab/issues/issues/13 for detailed analysis.
# Moreover, it will leave the python kernel running indefinitely which needlessly consumes resources.
# We could turn this behaviour off by setting "buffer_offline_messages=False",
# but that may come with other problems for people with flaky internet connections.
# Instead, here we configure Jupyter to kill all kernels that have been alive for
# more than 12 hours. We also close all inactive terminals after 10 minutes.
ENV NOTEBOOK_ARGS \
     "--NotebookApp.default_url='/apps/apps/home/start.ipynb'" \
     "--ContentsManager.allow_hidden=True" \
     "--MappingKernelManager.buffer_offline_messages=True" \
     "--MappingKernelManager.cull_busy=True" \
     "--MappingKernelManager.cull_connected=True" \
     "--MappingKernelManager.cull_idle_timeout=64800" \
     "--MappingKernelManager.cull_interval=300" \
     "--TerminalManager.cull_inactive_timeout=600" \
     "--TerminalManager.cull_interval=60"
