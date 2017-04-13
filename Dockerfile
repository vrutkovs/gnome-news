FROM fedora:rawhide
MAINTAINER Vadim Rutkovsky <vrutkovs@redhat.com>

# Install dependencies
RUN dnf install -y \
    meson \
    gcc \
    libappstream-glib-devel \
    intltool \
    itstool \
    glib2-devel

ADD . /opt/gnome-news/
WORKDIR /opt/gnome-news/

# Build
RUN meson build

# Install required check tools
RUN dnf install -y python3-pep8 python3-pyflakes
