gnome = import('gnome')

custom_target('org.gnome.News.desktop',
    input: 'org.gnome.News.desktop.in',
    output: 'org.gnome.News.desktop',
    command: [intltool_merge, '--desktop-style', podir, '@INPUT@', '@OUTPUT@'],
    install: true,
    install_dir: appdatadir,)

i18n.merge_file('desktop',
    input: 'org.gnome.News.appdata.xml.in',
    output: 'org.gnome.News.appdata.xml',
    po_dir: podir,
    install: true,
    install_dir: appdatadir,)

run_command('cp', join_paths(meson.build_root(), 'VERSION'), meson.source_root())

gnome.compile_resources('gnome-news',
    'gnome-news.gresource.xml',
    gresource_bundle: true,
    install: true,
    install_dir: installdir,
    dependencies: [version],)

install_data('org.gnome.News.gschema.xml',
    install_dir: join_paths(get_option('datadir'), 'glib-2.0', 'schemas'))

install_subdir('icons',
    install_dir: icondir)
