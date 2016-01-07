# vim: ts=4:sw=4:expandtab
# -*- coding: UTF-8 -*-

# BleachBit
# Copyright (C) 2008-2016 Andrew Ziem
# http://bleachbit.sourceforge.net
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Actions that perform cleaning
"""


import glob
import os
import re
import types
import Command
import FileUtilities
import General
import Special

from Common import _

if 'posix' == os.name:
    import Unix


#
# Plugin framework
# http://martyalchin.com/2008/jan/10/simple-plugin-framework/
#
class PluginMount(type):

    """A simple plugin framework"""

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            cls.plugins = []
        else:
            cls.plugins.append(cls)


class ActionProvider:

    """Abstract base class for performing individual cleaning actions"""
    __metaclass__ = PluginMount

    def __init__(self, action_node):
        """Create ActionProvider from CleanerML <action>"""
        pass

    def get_deep_scan(self):
        """Return a dictionary used to construct a deep scan"""
        raise StopIteration

    def get_commands(self):
        """Yield each command (which can be previewed or executed)"""
        pass


#
# base class
#
class FileActionProvider(ActionProvider):

    """Base class for providers which work on individual files"""
    action_key = '_file'

    def __init__(self, action_element):
        """Initialize file search"""
        self.regex = action_element.getAttribute('regex')
        assert(isinstance(self.regex, (str, unicode, types.NoneType)))
        self.nregex = action_element.getAttribute('nregex')
        assert(isinstance(self.nregex, (str, unicode, types.NoneType)))
        self.search = action_element.getAttribute('search')
        self.path = os.path.expanduser(os.path.expandvars(
            action_element.getAttribute('path')))
        if 'nt' == os.name and self.path:
            # convert forward slash to backslash for compatibility with getsize()
            # and for display.  Do not convert an empty path, or it will become
            # the current directory (.).
            self.path = os.path.normpath(self.path)
        self.ds = {}
        if 'deep' == self.search:
            self.ds['regex'] = self.regex
            self.ds['nregex'] = self.nregex
            self.ds['cache'] = General.boolstr_to_bool(
                action_element.getAttribute('cache'))
            self.ds['command'] = action_element.getAttribute('command')
            self.ds['path'] = self.path

    def get_deep_scan(self):
        if 0 == len(self.ds):
            raise StopIteration
        yield self.ds

    def get_paths(self):
        """Return a filtered list of files"""

        def get_file(path):
            if os.path.lexists(path):
                yield path

        def get_walk_all(top):
            for expanded in glob.iglob(top):
                for path in FileUtilities.children_in_directory(expanded, True):
                    yield path

        def get_walk_files(top):
            for expanded in glob.iglob(top):
                for path in FileUtilities.children_in_directory(expanded, False):
                    yield path

        if 'deep' == self.search:
            raise StopIteration
        elif 'file' == self.search:
            func = get_file
        elif 'glob' == self.search:
            func = glob.iglob
        elif 'walk.all' == self.search:
            func = get_walk_all
        elif 'walk.files' == self.search:
            func = get_walk_files
        else:
            raise RuntimeError("invalid search='%s'" % self.search)

        if self.regex:
            regex_c = re.compile(self.regex)

        if self.nregex:
            nregex_c = re.compile(self.nregex)

        # Sometimes this loop repeats many times, so optimize it by
        # putting the conditional outside the loop.

        if not self.regex and not self.nregex:
            for path in func(self.path):
                yield path
        elif self.regex and not self.nregex:
            for path in func(self.path):
                if not regex_c.search(os.path.basename(path)):
                    continue
                yield path
        elif self.nregex:
            for path in func(self.path):
                if nregex_c.search(os.path.basename(path)):
                    continue
                yield path
        else:
            for path in func(self.path):
                if not regex_c.search(os.path.basename(path)):
                    continue
                if nregex_c.search(os.path.basename(path)):
                    continue
                yield path

    def get_commands(self):
        raise NotImplementedError('not implemented')


#
# Action providers
#


class AptAutoclean(ActionProvider):

    """Action to run 'apt-get autoclean'"""
    action_key = 'apt.autoclean'

    def __init__(self, action_element):
        pass

    def get_commands(self):
        # Checking executable allows auto-hide to work for non-APT systems
        if FileUtilities.exe_exists('apt-get'):
            yield Command.Function(None,
                                   Unix.apt_autoclean,
                                   'apt-get autoclean')


class AptAutoremove(ActionProvider):

    """Action to run 'apt-get autoremove'"""
    action_key = 'apt.autoremove'

    def __init__(self, action_element):
        pass

    def get_commands(self):
        # Checking executable allows auto-hide to work for non-APT systems
        if FileUtilities.exe_exists('apt-get'):
            yield Command.Function(None,
                                   Unix.apt_autoremove,
                                   'apt-get autoremove')


class ChromeAutofill(FileActionProvider):

    """Action to clean 'autofill' table in Google Chrome/Chromium"""
    action_key = 'chrome.autofill'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_autofill,
                _('Clean file'))


class ChromeDatabases(FileActionProvider):

    """Action to clean Databases.db in Google Chrome/Chromium"""
    action_key = 'chrome.databases_db'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_databases_db,
                _('Clean file'))


class ChromeFavicons(FileActionProvider):

    """Action to clean 'Favicons' file in Google Chrome/Chromium"""
    action_key = 'chrome.favicons'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_favicons,
                _('Clean file'))


class ChromeHistory(FileActionProvider):

    """Action to clean 'History' file in Google Chrome/Chromium"""
    action_key = 'chrome.history'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_history,
                _('Clean file'))


class ChromeKeywords(FileActionProvider):

    """Action to clean 'keywords' table in Google Chrome/Chromium"""
    action_key = 'chrome.keywords'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_chrome_keywords,
                _('Clean file'))


class Delete(FileActionProvider):

    """Action to delete files"""
    action_key = 'delete'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Delete(path)


class Ini(FileActionProvider):

    """Action to clean .ini configuration files"""
    action_key = 'ini'

    def __init__(self, action_element):
        FileActionProvider.__init__(self, action_element)
        self.section = action_element.getAttribute('section')
        self.parameter = action_element.getAttribute('parameter')
        if self.parameter == "":
            self.parameter = None

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Ini(path, self.section, self.parameter)


class Json(FileActionProvider):

    """Action to clean JSON configuration files"""
    action_key = 'json'

    def __init__(self, action_element):
        FileActionProvider.__init__(self, action_element)
        self.address = action_element.getAttribute('address')

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Json(path, self.address)


class MozillaUrlHistory(FileActionProvider):

    """Action to clean Mozilla (Firefox) URL history in places.sqlite"""
    action_key = 'mozilla_url_history'

    def get_commands(self):
        for path in self.get_paths():
            yield Special.delete_mozilla_url_history(path)


class OfficeRegistryModifications(FileActionProvider):

    """Action to delete LibreOffice history"""
    action_key = 'office_registrymodifications'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                Special.delete_office_registrymodifications,
                _('Clean'))


class Shred(FileActionProvider):

    """Action to shred files (override preference)"""
    action_key = 'shred'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Shred(path)


class SqliteVacuum(FileActionProvider):

    """Action to vacuum SQLite databases"""
    action_key = 'sqlite.vacuum'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Function(
                path,
                FileUtilities.vacuum_sqlite3,
                # TRANSLATORS: Vacuum is a verb.  The term is jargon
                # from the SQLite database.  Microsoft Access uses
                # the term 'Compact Database' (which you may translate
                # instead).  Another synonym is 'defragment.'
                _('Vacuum'))


class Truncate(FileActionProvider):

    """Action to truncate files"""
    action_key = 'truncate'

    def get_commands(self):
        for path in self.get_paths():
            yield Command.Truncate(path)


class WinShellChangeNotify(ActionProvider):

    """Action to clean the Windows Registry"""
    action_key = 'win.shell.change.notify'

    def get_commands(self):
        import Windows
        yield Command.Function(
            None,
            Windows.shell_change_notify,
            None)


class Winreg(ActionProvider):

    """Action to clean the Windows Registry"""
    action_key = 'winreg'

    def __init__(self, action_element):
        self.keyname = action_element.getAttribute('path')
        self.name = action_element.getAttribute('name')

    def get_commands(self):
        yield Command.Winreg(self.keyname, self.name)


class YumCleanAll(ActionProvider):

    """Action to run 'yum clean all'"""
    action_key = 'yum.clean_all'

    def __init__(self, action_element):
        pass

    def get_commands(self):
        # Checking allows auto-hide to work for non-APT systems
        if not FileUtilities.exe_exists('yum'):
            raise StopIteration

        yield Command.Function(
            None,
            Unix.yum_clean,
            'yum clean all')
