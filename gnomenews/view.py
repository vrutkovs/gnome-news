# Copyright (C) 2015 Vadim Rutkovsky <vrutkovs@redhat.com>
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

from gi.repository import Gtk, GObject, WebKit2, GLib, Gdk, Gio

from gettext import gettext as _

from gnomenews import log
from gnomenews.post import Post
import logging
logger = logging.getLogger(__name__)


class GenericFeedsView(Gtk.Stack):

    __gsignals__ = {
        'open-article': (GObject.SignalFlags.RUN_FIRST, None, (GObject.GObject,)),
        'toggle-progressbar': (GObject.SignalFlags.RUN_FIRST, None, (bool, )),
    }

    @log
    def __init__(self, tracker, name, title=None):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        self.name = name
        self.title = title

        self._ui = Gtk.Builder()
        self._ui.add_from_resource('/org/gnome/News/ui/empty-view.ui')

        self.flowbox = Gtk.FlowBox(
            min_children_per_line=2,
            activate_on_single_click=True,
            row_spacing=10, column_spacing=10,
            margin=15,
            valign=Gtk.Align.START,
            selection_mode=Gtk.SelectionMode.NONE)
        self.flowbox.get_style_context().add_class('feeds-list')
        self.flowbox.connect('child-activated', self._post_activated)

        # Setup the layout
        self.setup_layout()

        # Setup the Empty state view
        self._empty_view = self._ui.get_object('empty-view')
        self.add_named(self._empty_view, 'empty')

        self.tracker = tracker
        self.show_all()

    @log
    def show_empty_view(self, show):
        if show:
            self.set_visible_child_name('empty')
        else:
            self.set_visible_child_name('view')

    @log
    def _add_a_new_preview(self, cursor, child=None):
        p = Post(cursor)
        if child:
            p.flowbox = child
        else:
            p.flowbox = self.flowbox
        p.connect('info-updated', self._insert_post)

    @log
    def _insert_post(self, source, post):
        image = Gtk.Image.new_from_file(post.thumbnail)
        image.get_style_context().add_class('feed-box')
        image.show()

        if post.is_read:
            image.set_opacity(0.5)
            image.set_tooltip_text(_('This article was already read'))

        # Store the post object to refer to it later on
        image.post = post.cursor

        source.flowbox.insert(image, -1)

    @log
    def _post_activated(self, box, child, user_data=None):
        cursor = child.get_children()[0].post
        post = Post(cursor)

        child.set_opacity(0.5)
        child.set_tooltip_text(_('This article was already read'))

        self.emit('open-article', post)

    @log
    def get_next_post(self):
        post_urls = [Post(x).url for x in self.posts]
        try:
            current_post_index = post_urls.index(self.current_post_url)
        except ValueError:
            return self.posts[0]
        else:
            return self.posts[current_post_index + 1]

    @log
    def get_prev_post(self):
        post_urls = [Post(x).url for x in self.posts]
        try:
            current_post_index = post_urls.index(self.current_post_url)
        except ValueError:
            return self.posts[-1]
        else:
            return self.posts[current_post_index - 1]

    @log
    def setup_layout(self):
        scrolledWindow = Gtk.ScrolledWindow()

        self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._box.pack_end(self.flowbox, True, True, 0)
        scrolledWindow.add(self._box)

        self.add_named(scrolledWindow, 'view')

    @log
    def update(self):
        pass


class FeedView(Gtk.Stack):

    __gsignals__ = {
        'go-back': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'show-prev-post': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'show-next-post': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self, tracker, post):
        Gtk.Stack.__init__(self,
                           transition_type=Gtk.StackTransitionType.CROSSFADE)
        stylesheet = Gio.File.new_for_uri('resource:///org/gnome/News/theme/reader.css')
        webview = WebKit2.WebView()
        if post.content:
            html_content = stylesheet.load_contents(None)[1].decode()
            html = """
                <style>%s</style>
                <body>
                  <article>
                  <h1>%s</h1>
                  <span>%s</span>
                  <p>%s</p>
                  <div id="footer">""" % (html_content, post.title, post.author or '', post.content)

            if post.author_homepage:
                html += """<p><a href="%s">%s</a></p>""" % (
                    post.author_homepage, post.author_homepage)

            if post.author_email:
                html += """<p><a href="mailto:%s?Subject=%s">%s</a></p>""" % (
                    post.author_email, post.title, post.author_email)

            html += """
            <p><a href="%s">View post</a></p>
            </div>
            </article>
            </body>
            """ % post.url

            webview.load_html(html)

        webview.connect("decide-policy", self._on_webview_decide_policy)
        self.add(webview)
        self.show_all()

        webview.connect('key_press_event', self.on_key_press)
        webview.connect('context-menu', self.customize_context_menu)
        self.post = post
        self.url = post.url

    @log
    def customize_context_menu(self, webview, context_menu, event, hit_test_result):
        items = context_menu.get_items()
        labels = [x.get_action().get_label() for x in items]
        try:
            reload_index = labels.index('_Reload')
            context_menu.remove(items[reload_index])
        except ValueError:
            pass
        return False

    @staticmethod
    @log
    def _on_webview_decide_policy(web_view, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            uri = decision.get_request().get_uri()
            if uri != "about:blank" and decision.get_navigation_type() == WebKit2.NavigationType.LINK_CLICKED:
                decision.ignore()
                try:
                    Gtk.show_uri(None, uri, Gdk.CURRENT_TIME)
                except GLib.Error:
                    # for example, irc://irc.gimp.org/#guadec
                    logger.warning("Couldn't open URI: %s" % uri)
                return True
        return False

    @log
    def on_key_press(self, widget, event):
        # Return to previous view when Esc is pressed
        if event.keyval == Gdk.KEY_Escape:
            self.emit('go-back')

        # Show previous post (if available) if Left (arrow) is pressed
        elif event.keyval in [Gdk.KEY_leftarrow, Gdk.KEY_Left]:
            self.emit('show-prev-post')

        # Show previous post (if available) if Right (arrow) is pressed
        elif event.keyval in [Gdk.KEY_rightarrow, Gdk.KEY_Right]:
            self.emit('show-next-post')


class NewView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'new', _("New"))

        self.tracker.connect('items-updated', self.update)

    @log
    def update(self, _=None):
        self.emit('toggle-progressbar', True)
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        self.posts = self.tracker.get_post_sorted_by_date(unread=True)
        [self._add_a_new_preview(post) for post in self.posts]
        self.show_all()

        self.show_empty_view(len(self.posts) is 0)
        self.emit('toggle-progressbar', False)


class FeedsView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'feeds', _("Feeds"))

        # url -> (feed, row)
        self.feeds = {}

        app = Gio.Application.get_default()
        delete_channel_action = app.lookup_action('delete_channel')
        delete_channel_action.connect('activate', self.delete_channel)

        self.tracker.connect('items-updated', self.update_items)
        self.tracker.connect('feeds-updated', self.update)

    @log
    def update_items(self, _=None):
        for flowbox in self.feed_stack.get_children():
            url = self.feed_stack.child_get_property(flowbox, 'name')

            [flowbox.remove(old_feed) for old_feed in flowbox.get_children()]

            posts = self.tracker.get_posts_for_channel(url)
            [self._add_a_new_preview(post, flowbox) for post in posts]

    @log
    def update(self, _=None):
        self.emit('toggle-progressbar', True)
        new_feeds = self.tracker.get_channels()
        new_feed_urls = [new_feed['url'] for new_feed in new_feeds]

        # Remove old feeds
        for feed in list(self.feeds.keys()):
            if feed not in new_feed_urls:
                logger.info("Removing channel %s" % feed)
                self.feed_stack.remove(self.feed_stack.get_child_by_name(feed))
                self.listbox.remove(self.feeds[feed][1])
                del self.feeds[feed]

        # Add new feeds
        for new_feed in new_feeds:
            if new_feed['url'] not in self.feeds:
                logger.info("Adding channel %s" % new_feed['url'])
                self._add_new_feed(new_feed)

        self.show_empty_view(len(new_feeds) is 0)
        self.emit('toggle-progressbar', False)

    @log
    def _add_new_feed(self, feed):
        # Check if we're not adding an already added feed
        if feed['url'] in self.feeds:
            return

        # Add a row to the listbox
        row = Gtk.ListBoxRow()
        row.add(Gtk.Label(label=feed['title'], margin=10, xalign=0))
        row.set_tooltip_text(feed['url'])
        row.feed = feed
        row.show_all()

        self.listbox.add(row)
        self.feeds[feed['url']] = (feed, row)

    @log
    def load_posts_for_feed(self, row):
        self.emit('toggle-progressbar', True)
        feed = row.feed
        # Add a flowbox with the items
        flowbox = Gtk.FlowBox(
            min_children_per_line=2,
            activate_on_single_click=True,
            row_spacing=10, column_spacing=10,
            valign=Gtk.Align.START,
            margin=15,
            selection_mode=Gtk.SelectionMode.NONE)
        flowbox.get_style_context().add_class('feeds-list')
        flowbox.connect('child-activated', self._post_activated)
        flowbox.show()

        flowbox.row = row
        flowbox.feed = feed

        posts = self.tracker.get_posts_for_channel(feed['url'])
        [self._add_a_new_preview(post, flowbox) for post in posts]

        if not feed['title']:
            feed['title'] = _("Unknown feed")
        self.feed_stack.add_titled(flowbox, feed['url'], feed['title'])
        self.emit('toggle-progressbar', False)

    @log
    def delete_channel(self, action, index_variant):
        try:
            index = index_variant.get_int32()
            row = self.listbox.get_children()[index]
            url = row.feed['url']
            self.tracker.remove_channel(url)
        except Exception as e:
            logger.warn("Failed to remove feed %s: %s" % (str(index_variant), str(e)))

    @log
    def setup_layout(self):
        self.feed_stack = Gtk.Stack(
            transition_type=Gtk.StackTransitionType.CROSSFADE,
            transition_duration=100,
            visible=True,
            can_focus=False)
        self.feed_stack.connect('notify::visible-child-name', self.visible_feed_changed)

        feedstackScrolledWindow = Gtk.ScrolledWindow(expand=True)
        feedstackScrolledWindow.add(self.feed_stack)

        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        self.listbox.set_sort_func(self.sort_function)
        self.listbox.connect('button-release-event', self._on_button_release)
        self.listbox.connect('row-selected', self._on_row_selected)

        listboxScrolledWindow = Gtk.ScrolledWindow(min_content_width=200)
        listboxScrolledWindow.add(self.listbox)

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._box.add(listboxScrolledWindow)
        self._box.add(Gtk.Separator.new(Gtk.Orientation.VERTICAL))
        self._box.add(feedstackScrolledWindow)

        self.add_named(self._box, 'view')

        self._box.show_all()

    @log
    def visible_feed_changed(self, stack, property_name):
        if stack.get_visible_child():
            row = stack.get_visible_child().row
            self.listbox.select_row(row)

    @log
    def _on_row_selected(self, listbox, row, _=None):
        if row:
            url = row.feed['url']
            loaded_urls = [x.feed['url'] for x in self.feed_stack.get_children()]
            if url not in loaded_urls:
                self.load_posts_for_feed(row)
            self.feed_stack.set_visible_child_name(url)
            self.posts = self.tracker.get_posts_for_channel(url)

    @log
    def _on_button_release(self, w, event):
        selected_row = self.listbox.get_row_at_y(event.y)
        (_, button) = event.get_button()

        # Abort if the click is not in any row
        if not selected_row:
            return Gdk.EVENT_PROPAGATE

        # Left click
        if button is Gdk.BUTTON_PRIMARY:
            self.feed_stack.set_visible_child_name(selected_row.feed['url'])

            return Gdk.EVENT_PROPAGATE

        # Right click
        elif button is Gdk.BUTTON_SECONDARY:
            try:
                index = selected_row.get_index()

                menu = Gio.Menu()
                menu.append("Remove", "app.delete_channel(%s)" % index)

                popover = Gtk.Popover.new_from_model(selected_row, menu)
                popover.position = Gtk.PositionType.BOTTOM
                popover.show()

            except Exception as e:
                logger.warn("Error showing popover: %s" % str(e))

            return Gdk.EVENT_STOP

    def sort_function(self, row1, row2, _=None):
        row1_title = row1.feed['title'] or ''
        row2_title = row2.feed['title'] or ''
        return row1_title > row2_title


class StarredView(GenericFeedsView):
    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'starred', _("Starred"))

        # Setup a custom empty view
        self.remove(self._empty_view)

        self._empty_view = self._ui.get_object('empty-starred-view')
        self.add_named(self._empty_view, 'empty')

        self.tracker.connect('items-updated', self.update)

    @log
    def update(self, _=None):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        self.posts = self.tracker.get_post_sorted_by_date(starred=True)
        [self._add_a_new_preview(post) for post in self.posts]
        self.show_all()

        self.show_empty_view(len(self.posts) is 0)


class SearchView(GenericFeedsView):

    __gproperties__ = {
        'search-query': (str, 'Query', 'Search query', "", GObject.ParamFlags.READWRITE)
    }

    def __init__(self, tracker):
        GenericFeedsView.__init__(self, tracker, 'search')

        self.search_query = ""

        # Setup a custom empty view
        self.remove(self._empty_view)

        self._empty_view = self._ui.get_object('empty-search-view')
        self.add_named(self._empty_view, 'empty')

    @log
    def do_get_property(self, prop):
        if prop.name == 'search-query':
            return self.search_query
        else:
            raise AttributeError('Unknown property %s' % prop.name)

    @log
    def do_set_property(self, prop, value):
        if prop.name == 'search-query':
            self.search_query = value
            self.update_search()
        else:
            raise AttributeError('Unknown property %s' % prop.name)

    @log
    def update_search(self):
        [self.flowbox.remove(old_feed) for old_feed in self.flowbox.get_children()]

        if len(self.search_query) is 0:
            return

        posts = self.tracker.get_text_matches(self.search_query)
        [self._add_a_new_preview(post) for post in posts]
        self.show_all()

        self.show_empty_view(len(posts) is 0)
