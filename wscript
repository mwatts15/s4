# encoding: utf-8
#
# WAF build scripts for XMMS2
# Copyright (C) 2006-2009 XMMS2 Team
#

import sys
if sys.version_info < (2,4):
    raise RuntimeError("Python 2.4 or newer is required")

import os
from waflib import Options

BASEVERSION = "0.01"
APPNAME = 's4'

top = '.'
out = '_build_'

lib_dir = 'src/lib'
test_dir = 'tests'
tool_dirs = ['src/tools/bench', 'src/tools/s4']

####
## Initialization
####
def init(ctx):
    import gc
    gc.disable()


####
## Build
####
def build(bld):
    subdirs = bld.env.S4_SUBDIRS
    newest = max([os.stat(os.path.join(sd, "wscript")).st_mtime for sd in subdirs])
    if bld.env.NEWEST_WSCRIPT_SUBDIR and newest > bld.env.NEWEST_WSCRIPT_SUBDIR:
        bld.fatal("You need to run waf configure")
        raise SystemExit(1)

    bld.add_subdirs(subdirs)


####
## Configuration
####
def configure(conf):
    prefix = os.environ.get('PKG_CONFIG_PREFIX', None)
    if prefix:
        if not os.path.isabs(prefix):
            prefix = os.path.abspath(prefix)
        cond.env.PKG_CONFIG_DEFINES = dict(prefix=prefix)

    conf.env.S4_SUBDIRS = [lib_dir]

    if conf.options.build_tests:
        conf.env.append_value("S4_SUBDIRS", test_dir)
    if conf.options.build_tools:
        conf.env.append_value("S4_SUBDIRS", tool_dirs)

    conf.check_tool('misc gnu_dirs')
    conf.check_tool('gcc')
    conf.env.append_value('CFLAGS', ['-Wall', '-g'])

    if conf.options.target_platform:
        Options.platform = conf.options.target_platform

    conf.env.VERSION = BASEVERSION

    conf.env.PKGCONFIGDIR = conf.options.pkgconfigdir or \
            os.path.join(conf.env.PREFIX, 'lib', 'pkgconfig')

    if conf.options.enable_gcov:
        conf.env.append_value('CFLAGS', '-fprofile-arcs')
        conf.env.append_value('CFLAGS', '-ftest-coverage')
        conf.env.append_value('LINKFLAGS', '-fprofile-arcs')

    if conf.options.config_prefix:
        for d in conf.options.config_prefix:
            if not os.path.isabs(d):
                d = os.path.abspath(d)
            conf.env.prepend_value("LIBPATH", os.path.join(d, "lib"))
            conf.env.prepend_value("CPPPATH", os.path.join(d, "include"))

    # Our static libraries may link to dynamic libraries
    if Options.platform != 'win32':
        conf.env.CFLAGS_cstlib += ['-fPIC', '-DPIC']
    else:
        # As we have to change target platform after the tools
        # have been loaded there are a few variables that needs
        # to be initiated if building for win32.

        # Make sure we don't have -fPIC and/or -DPIC in our CCFLAGS
        conf.env.CFLAGS_cshlib = []

        # Setup various prefixes
        conf.env.cshlib_PATTERN = 'lib%s.dll'
        conf.env.cprogram_PATTERN = '%s.exe'

    # Add some specific OSX things
    if Options.platform == 'darwin':
        conf.env["LINKFLAGS"] += ['-multiply_defined suppress']
        conf.env["explicit_install_name"] = True
    else:
        conf.env["explicit_install_name"] = False

    # Check for support for the generic platform
    has_platform_support = os.name in ('nt', 'posix')
    conf.msg('Platform code for %s' % os.name, has_platform_support)
    if not has_platform_support:
        conf.fatal("s4 only has platform support for Windows "
              "and POSIX operating systems.")
        raise SystemExit(1)

    # Check sunOS socket support
    if Options.platform == 'sunos':
        conf.env.append_unique('CFLAGS', '-D_POSIX_PTHREAD_SEMANTICS')
        conf.env.append_unique('CFLAGS', '-D_REENTRANT')
        conf.env.append_unique('CFLAGS', '-std=gnu99')

    # Glib is required by everyone, so check for it here and let them
    # assume its presence.
    conf.check_cfg(package='glib-2.0', atleast_version='2.8.0',
            uselib_store='glib2', args='--cflags --libs')
    conf.check_cfg(package='gthread-2.0', atleast_version='2.6.0',
            uselib_store='gthread2', args='--cflags --libs')

    subdirs = conf.env.S4_SUBDIRS

    for sd in subdirs:
        conf.sub_config(sd)

    newest = max([os.stat(os.path.join(sd, "wscript")).st_mtime for sd in subdirs])
    conf.env.NEWEST_WSCRIPT_SUBDIR = newest

    return True


####
## Options
####
def _list_cb(option, opt, value, parser):
    """Callback that lets you specify lists of targets."""
    vals = value.split(',')
    if vals == ['']:
        vals = []
    if getattr(parser.values, option.dest):
        vals += getattr(parser.values, option.dest)
    setattr(parser.values, option.dest, vals)

def options(opt):
    opt.tool_options('gnu_dirs')
    opt.tool_options('gcc')

    opt.add_option('--with-custom-version', type='string',
                   dest='customversion', help="Override git commit hash version")
    opt.add_option('--conf-prefix', action="callback", callback=_list_cb,
                   type='string', dest='config_prefix',
                   help="Specify a directory to prepend to configuration prefix")
    opt.add_option('--with-pkgconfigdir', type='string', dest='pkgconfigdir',
                   help="Specify directory where to install pkg-config files")
    opt.add_option('--with-target-platform', type='string',
                   dest='target_platform',
                   help="Force a target platform (cross-compilation)")
    opt.add_option('--with-windows-version', type='string', dest='winver',
                   help="Force a specific Windows version (cross-compilation)")
    opt.add_option('--build-tests', action='store_true', default=False,
                   dest='build_tests', help="Build test suite")
    opt.add_option('--run-tests', action='store_true', default=False,
                   dest='run_tests', help="Run test suite")
    opt.add_option('--enable-gcov', action='store_true', default=False,
                   dest='enable_gcov', help="Enable code coverage analysis")
    opt.add_option('--lcov-report', action="store_true", default=False,
                   dest='build_lcov', help="Builds an lcov report")
    opt.add_option("--build-tools", action="store_true", default=False,
                    dest="build_tools",
                    help="Build S4 tools to verify and recover databases.")
    opt.add_option('--without-ldconfig', action='store_false', default=True,
                   dest='ldconfig', help="Don't run ldconfig after install")

    opt.sub_options(tool_dirs)

def shutdown(ctx):
    if 'install' in Options.commands and (
            ctx.options.ldconfig or
            (ctx.options.ldconfig is None and os.geteuid() == 0)):
        ldconfig = '/sbin/ldconfig'
        if os.path.isfile(ldconfig):
            libprefix = Utils.subst_vars('${PREFIX]/lib', ctx.env)
            try:
                import subprocess
                subprocess.check_output(['ldconfig', 'libprefix'])
            except:
                pass

    if ctx.options.run_tests:
        os.system(os.path.join(out, "tests/test_s4"))

    if ctx.options.build_lcov:
        cd = os.getcwd()
        os.chdir(out)
        os.system("lcov -c -b . -d . -o s4.info")
        os.system("genhtml -o ../coverage s4.info")
        os.chdir(cd)
