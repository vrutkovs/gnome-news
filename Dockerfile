FROM fedora:latest
MAINTAINER Vadim Rutkovsky <vrutkovs@redhat.com>

# Install build dependencies
RUN dnf update -y && \
    dnf install -y --refresh \
        autoconf autoconf-archive automake intltool gcc \
        glib2-devel make findutils tar xz \
        libappstream-glib-devel python3 && \
        dnf clean all

ADD . /opt/gnome-news/
WORKDIR /opt/gnome-news/

# Build
RUN ./autogen.sh && make