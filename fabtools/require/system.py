"""
Idempotent API for managing system settings
"""
from __future__ import with_statement

from fabric.api import sudo, warn
from fabric.contrib.files import append

from fabtools.files import watch
from fabtools.system import (
    get_hostname, set_hostname,
    get_sysctl, set_sysctl,
    supported_locales,
    )


def sysctl(key, value, persist=True):
    """
    Require a kernel parameter to have a specific value
    """
    if get_sysctl(key) != value:
        set_sysctl(key, value)

    if persist:
        from fabtools import require
        filename = '/etc/sysctl.d/60-%s.conf' % key
        def on_change():
            sudo('service procps start')
        with watch(filename, True, on_change):
            require.file(filename,
                contents='%(key)s = %(value)s\n' % locals(),
                use_sudo=True)


def hostname(name):
    """
    Require the hostname to have a specific value
    """
    if get_hostname() != name:
        set_hostname(name)


def locales(names):
    """
    Require the list of locales to be available
    """

    config_file = '/var/lib/locales/supported.d/local'

    def regenerate():
        sudo('dpkg-reconfigure locales')

    # Regenerate locales if config file changes
    with watch(config_file, True, regenerate):

        # Add valid locale names to the config file
        supported = dict(supported_locales())
        for name in names:
            if name in supported:
                charset = supported[name]
                locale = "%s %s" % (name, charset)
                append(config_file, locale, use_sudo=True)
            else:
                warn('Unsupported locale name "%s"' % name)


def locale(name):
    """
    Require the locale to be available
    """
    locales([name])


def default_locale(name):
    """
    Require the locale to be the default
    """
    from fabtools import require

    # Ensure the locale is available
    locale(name)

    # Make it the default
    contents = 'LANG="%s"\n' % name
    require.file('/etc/default/locale', contents, use_sudo=True)
