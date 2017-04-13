project('gnome-news', 'c', version : '0.98', meson_version : '>= 0.36.0')

python = find_program('python3')
intltool_merge = find_program('intltool-merge')
itstool = find_program('itstool')
msgfmt = find_program('msgfmt')

appdatadir = join_paths(get_option('datadir'), 'applications')
icondir = join_paths(get_option('datadir'), 'icons', 'hicolor')
podir = join_paths(meson.current_source_dir(), 'po')
installdir = join_paths(get_option('datadir'), meson.project_name())
pythondir = join_paths(get_option('prefix'), installdir)

conf = configuration_data()
conf.set('pkgdatadir', join_paths(
    get_option('prefix'), get_option('datadir'), meson.project_name()))
conf.set('localedir', join_paths(
    get_option('prefix'), get_option('localedir'), meson.project_name()))
conf.set('pythondir', pythondir)

conf.set('PACKAGE_VERSION', '0.0.1')
conf.set('PACKAGE_URL', 'https://wiki.gnome.org/Design/Apps/Potential/News')

version = configure_file(
    input: 'VERSION.in',
    output: 'VERSION',
    configuration: conf,
)

subdir('po')
subdir('data')

configure_file(
    input: 'gnome-news.in',
    output: 'gnome-news',
    configuration: conf,
    install: true,
    install_dir: get_option('bindir')
)

install_subdir('gnomenews', install_dir: installdir)
install_subdir('gnomenews', install_dir: installdir)

meson.add_install_script('meson_install.py')
