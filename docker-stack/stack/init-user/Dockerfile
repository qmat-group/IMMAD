ARG BASE
FROM $BASE
RUN apk add --no-cache postgresql-client

LABEL maintainer="IMMAD Project <hung.dangthe@HOST>"

ARG UID=1000
ARG GID=1000
ARG USER=immad
ARG GROUP=immad
ARG HOME_DIR="/${USER}"
ARG IMMAD_DIR="/var/immad"

RUN \
  addgroup -g $GID $GROUP && \
  adduser -u $UID -G $GROUP -h $HOME_DIR -D $USER

WORKDIR $HOME_DIR

USER $USER

COPY init.sh $HOME_DIR
