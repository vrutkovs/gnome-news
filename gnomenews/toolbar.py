# Copyright (C) 2015 Vadim Rutkovsky <vrutkovs@redhat.com>
# Copyright (C) 2015 Igor Gnatenko <ignatenko@src.gnome.org>
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

from gi.repository import Gtk, GObject, GLib

from gettext import gettext as _

from gnomenews import log
import logging
logger = logging.getLogger(__name__)


class ToolbarState:
    MAIN = 0
    CHILD_VIEW = 1
    SEARCH_VIEW = 2


class Toolbar(GObject.GObject):

    __gsignals__ = {
        'state-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'toggle-starred': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
    }

    @log
    def __init__(self, window):
        GObject.GObject.__init__(self)
        self.window = window
        self._stack_switcher = Gtk.StackSwitcher(
            margin_top=2, margin_bottom=2, can_focus=False, halign="center")

        self._ui = Gtk.Builder()
        self._ui.add_from_resource('/org/gnome/News/ui/headerbar.ui')
        self.header_bar = self._ui.get_object('header-bar')
        self.header_bar.set_custom_title(self._stack_switcher)

        self.add_toggle_button = self._ui.get_object('add-toggle-button')
        self.add_popover = self._ui.get_object('add-popover')
        self.add_popover.hide()
        self.add_toggle_button.set_popover(self.add_popover)

        self.button_stack = self._ui.get_object('add-button-stack')

        self.new_url = self._ui.get_object('new-url')
        self.new_url.connect('changed', self.on_new_url_changed)
        self.add_button = self._ui.get_object('add-button')
        self.add_button.connect('clicked', self._add_new_feed)

        self._back_button = self._ui.get_object('back-button')
        self._back_button.connect('clicked', self.window.on_back_button_clicked)

        self._search_button = self._ui.get_object('search-button')
        self._search_button.bind_property('active',
                                          self.window.search_bar, 'search-mode-enabled',
                                          GObject.BindingFlags.BIDIRECTIONAL)

        self.window.search_entry.connect('search-changed', self._search_changed)

        # Starred button
        self._starred_button = self._ui.get_object('starred-button')
        self._starred_image = self._ui.get_object('starred-button-image')

        self._starred_button.connect('clicked', self._toggle_starred)
        self.starred = False

        self.set_state(ToolbarState.MAIN)

        self._stack_switcher.show()

    @log
    def reset_header_title(self):
        self.header_bar.set_custom_title(self._stack_switcher)

    @log
    def _toggle_starred(self, button):
        self.set_starred(not self.starred)
        self.emit('toggle-starred', self.starred)

    @log
    def _search_changed(self, entry, data=None):
        if entry.get_text_length() > 0:
            self.set_state(ToolbarState.SEARCH_VIEW)
            self.header_bar.set_title(_('Searching for "%s"') % entry.get_text())
        else:
            self.set_state(ToolbarState.MAIN)
            self.header_bar.set_title(_("News"))

    @log
    def set_starred(self, starred):
        # Don't set the same value
        if starred is self.starred:
            return

        self.starred = starred

        if starred:
            self._starred_image.set_from_icon_name('starred-symbolic', Gtk.IconSize.BUTTON)
        else:
            self._starred_image.set_from_icon_name('non-starred-symbolic', Gtk.IconSize.BUTTON)

    @log
    def set_stack(self, stack):
        self._stack_switcher.set_stack(stack)

    @log
    def get_stack(self):
        return self._stack_switcher.get_stack()

    @log
    def hide_stack(self):
        self._stack_switcher.hide()

    @log
    def show_stack(self):
        self._stack_switcher.show()

    @log
    def set_state(self, state, btn=None):
        self._state = state
        self._update()
        self.emit('state-changed')

    @log
    def _update(self):
        if self._state != ToolbarState.MAIN:
            self.header_bar.set_custom_title(None)
        else:
            self.reset_header_title()

        self._back_button.set_visible(self._state == ToolbarState.CHILD_VIEW)
        self._search_button.set_visible(self._state != ToolbarState.CHILD_VIEW)
        self._starred_button.set_visible(self._state == ToolbarState.CHILD_VIEW)
        self.add_toggle_button.set_visible(self._state != ToolbarState.CHILD_VIEW)

    @log
    def _add_new_feed(self, button):
        new_url = self.new_url.get_text()
        self.window.tracker.add_channel(new_url, 30, None, self._channel_added)
        self.button_stack.set_visible_child_name('spinner')
        self.new_url.set_sensitive(False)

    @log
    def _channel_added(self, user_data=None):
        self.button_stack.set_visible_child_name('button')
        self.new_url.set_sensitive(True)
        self.new_url.set_text('')
        self.add_popover.hide()

    @log
    def _update_title(self, post):
        self.set_state(ToolbarState.CHILD_VIEW)
        self.header_bar.set_title(post.title)
        self.header_bar.set_subtitle(post.author)

    def on_new_url_changed(self, entry):
        text = self.new_url.get_text()
        already_subscribed_label = self._ui.get_object("add-box-already-subscribed-label")
        if len(text) == 0:
            self.add_button.set_sensitive(False)
            already_subscribed_label.set_visible(False)
        else:
            if not GLib.uri_parse_scheme(text):
                self.add_button.set_sensitive(False)
                already_subscribed_label.set_visible(False)
                return
            if len(self.window.tracker.get_channels(text)) == 0:
                already_subscribed_label.set_visible(False)
                self.add_button.set_sensitive(True)
            else:
                self.add_button.set_sensitive(False)
                already_subscribed_label.set_visible(True)
