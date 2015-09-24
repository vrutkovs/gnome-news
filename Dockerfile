FROM fedora:rawhide
MAINTAINER Vadim Rutkovsky <vrutkovs@redhat.com>

# Install dependencies
RUN dnf install -q -y libappstream-glib-devel autoconf autoconf-archive automake \
    intltool gcc glib2-devel make findutils tar xz

ADD . /opt/gnome-news/
WORKDIR /opt/gnome-news/

# Build
RUN ./autogen.sh && make