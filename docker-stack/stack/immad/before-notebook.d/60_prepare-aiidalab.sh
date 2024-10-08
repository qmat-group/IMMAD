#!/bin/bash

# Debugging.
set -x

# Environment.
export SHELL=/bin/bash

# Fix https://github.com/aiidalab/aiidalab-docker-stack/issues/225
if [ -L /home/${NB_USER}/${NB_USER} ]; then
  rm /home/${NB_USER}/${NB_USER}
fi

# Check whether this is likely the first time we run this script.
[[ -z $(ls -A "/home/${NB_USER}/apps/") ]] && INITIAL_SETUP=1 || INITIAL_SETUP=0

# Install apps.
SRC=("aiidalab-home" "aiidalab-widgets-base" "aiidalab-qe")
DEST=("home" "aiidalab-widgets-base" "quantum-espresso")

# Ensure that the ~/apps directory exists.
mkdir -p ${AIIDALAB_APPS}

for i in ${!SRC[@]}; do
  src=${SRC[$i]}
  dest=${DEST[$i]}
  src_dir=/opt/$src
  dest_dir=${AIIDALAB_APPS}/${dest}
  if [ ! -e $dest_dir ]; then
      echo "Install ${src} app as ${dest}."
  
      # The home app is installed in system space and linked to from user space.
      # That ensures that users are not inadvertently running the wrong version of
      # the home app for a given system environment, but still makes it possible to
      # manually install a specific version of the home app in between upgrades, e.g.,
      # for development work, by simply replacing the link with a clone of the repository.
      ln -s $src_dir $dest_dir
  elif [[ -d $dest_dir && ! -L $dest_dir ]]; then
    echo "Backup $dest and replace by a link to $src_dir"
    # Backup an existing repository of the home app and replace with link to /opt/aiidalab-home.
    # This mechanism preserves potential development work on a manually installed repository
    # of the home app and also constitutes a migration path for existing aiidalab accounts, where
    # the home app was installed directly into user space by default.
    mv $dest_dir ${AIIDALAB_APPS}/.${dest}~`date --iso-8601=seconds` \
      && ln -s $src_dir $dest_dir || echo "WARNING: Unable to install home app."
  fi
done

# Install default apps (see the Dockerfile for an explanation of the
# AIIDALAB_DEFAULT_APPS variable).
if [[ ${INITIAL_SETUP} == 1 ]]; then

  # Iterate over lines in AIIDALAB_DEFAULT_APPS variable.
  for app in ${AIIDALAB_DEFAULT_APPS:-}; do
      aiidalab install --yes "${app}"
  done
fi

# Clear user trash directory.
if [ -e /home/${NB_USER}/.trash ]; then
  rm -rf /home/${NB_USER}/.trash/*
fi

# Remove old apps_meta.sqlite requests cache files.
find -L /home/${NB_USER} -maxdepth 3 -name apps_meta.sqlite -writable -delete

# Remove old temporary notebook files.
find -L /home/${NB_USER}/apps -maxdepth 2 -type f -name .*.ipynb -writable -delete

# Uninstall aiidalab from user packages (if present).
# Would otherwise interfere with the system package.
USER_AIIDALAB_PACKAGE="$(python -c 'import site; print(site.USER_SITE)')/aiidalab"
if [ -e ${USER_AIIDALAB_PACKAGE} ]; then
  echo "Uninstall local installation of aiidalab package."
  pip uninstall --yes aiidalab
fi
