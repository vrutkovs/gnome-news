FROM fedora:latest
MAINTAINER Vadim Rutkovsky <vrutkovs@redhat.com>

# Install build dependencies
RUN dnf update -y && \
    dnf install -y --refresh \
        autoconf autoconf-archive automake intltool gcc \
        glib2-devel make findutils tar xz \
        libappstream-glib-devel python3 \
        python3-gobject gtk3 tracker && \
    dnf clean all

ADD . /opt/gnome-news/
WORKDIR /opt/gnome-news/

# Build and exit if DISPLAY was not passed
RUN ./autogen.sh && make

RUN adduser user -c User -d /home/user -m -s /bin/bash -u 1000 -U
RUN mkdir -p /home/user/.config && chown 1000.1000 /home/user/.config
RUN echo "user ALL=(root) NOPASSWD: ALL" >> /etc/sudoers
USER 1000
WORKDIR /home/user
EXPOSE 8080
CMD ["/opt/gnome-news/broadway.sh"]
