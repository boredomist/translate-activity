# Copyright (C) 2013 Erik Price

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

from gettext import gettext as _

import babel
from babel import Locale

from gi.repository import Gtk, Gdk, Pango, GObject

import sugar3.logger

from sugar3.activity import activity
from sugar3.activity import widgets
from sugar3.activity.widgets import DescriptionItem
from sugar3.activity.widgets import ShareButton
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import TitleEntry
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.alert import Alert, NotifyAlert

import translate.client
from translate.client.exceptions import TranslateException


class TranslateActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        GObject.threads_init()

        self.set_title(_("Translate Activity"))

        # XXX: Is this the right way of doing it? I mean, it works...
        self._logger = sugar3.logger.logging
        self._logger.info('Starting translate activity')

        # XXX: This really needs to be configurable.
        self.client = translate.client.Client(
            'translate.erikprice.net', port=80)

        toolbar_box = ToolbarBox()
        activity_button = widgets.ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, 0)
        activity_button.show()

        title_entry = TitleEntry(self)
        toolbar_box.toolbar.insert(title_entry, -1)
        title_entry.show()

        description_item = DescriptionItem(self)
        description_item.show()

        share_button = ShareButton(self)
        toolbar_box.toolbar.insert(share_button, -1)
        share_button.show()

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        separator.show()

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        stop_button.show()

        self.set_toolbar_box(toolbar_box)
        toolbar_box.show()

        # Main vertical layout of this window
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        # Text areas
        text_hbox = Gtk.Box(spacing=6)
        # Selection area (langs + translate button)
        select_hbox = Gtk.Box(spacing=6)

        vbox.pack_start(select_hbox, False, True, 6)
        vbox.pack_start(text_hbox, True, True, 0)

        # Spacers
        text_hbox.pack_start(Gtk.Box(), False, True, 10)
        text_hbox.pack_end(Gtk.Box(), False, True, 10)
        select_hbox.pack_start(Gtk.Box(), False, True, 10)
        select_hbox.pack_end(Gtk.Box(), False, True, 10)
        vbox.pack_end(Gtk.Box(), False, True, 10)

        select_hbox.pack_start(Gtk.Label(_("Translate from:")),
                               False, False, 0)

        # Models for the ComboBoxes
        from_lang_store = Gtk.ListStore(str, str)
        to_lang_store = Gtk.ListStore(str, str)

        self.lang_from = Gtk.ComboBox.new_with_model_and_entry(from_lang_store)
        self.lang_to = Gtk.ComboBox.new_with_model_and_entry(to_lang_store)

        self.lang_from.connect("changed", self._lang_from_changed_cb)

        self.lang_from.set_entry_text_column(1)
        self.lang_to.set_entry_text_column(1)

        select_hbox.pack_start(self.lang_from, False, False, 0)
        select_hbox.pack_start(Gtk.Label(_("Translate to:")), False, False, 6)
        select_hbox.pack_start(self.lang_to, False, False, 0)

        self.translate_button = Gtk.Button(_("Translate text!"))

        # Disable the button
        self.translate_button.set_sensitive(False)

        self.translate_button.connect("clicked", self._translate_btn_cb)
        select_hbox.pack_end(self.translate_button, False, False, 0)

        # Visible while waiting for results from server.
        self.translate_spinner = Gtk.Spinner()
        self.translate_spinner.start()
        select_hbox.pack_end(self.translate_spinner, False, True, 6)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(False)
        scrolled_window.set_vexpand(True)

        self.text_from = Gtk.TextView()
        self.text_from.get_buffer().set_text("This is where you would type in \
some text to translate.")

        scrolled_window.add(self.text_from)
        text_hbox.pack_start(scrolled_window, True, True, 0)

        # Spacer
        text_hbox.pack_start(Gtk.Box(), False, True, 10)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(False)
        scrolled_window.set_vexpand(True)

        self.text_to = Gtk.TextView()
        self.text_to.get_buffer().set_text("This is where the translated text \
would show up.")
        self.text_to.set_editable(False)
        self.text_to.set_cursor_visible(False)

        scrolled_window.add(self.text_to)
        text_hbox.pack_start(scrolled_window, True, True, 0)

        self.text_from.override_font(Pango.FontDescription("Sans 13"))
        self.text_to.override_font(Pango.FontDescription("Sans 13"))

        self.set_canvas(vbox)
        vbox.show_all()

        self.translate_spinner.hide()

        alert = self._create_alert(_("Connecting"),
                                   _("Trying to reach server..."))

        # Run the rest of the initialization in the background
        GObject.idle_add(self._init_translate, alert)

    def _init_translate(self, alert):
        """Run in background at startup, initializes data, contacts server,
        does that sort of setup procedure.
        """

        # XXX: Maybe instead of failing here, how about creating a transient
        #      local server, would use whatever web APIs possible. Not really
        #      sure.

        if not self.client.can_connect():
            self.remove_alert(alert)
            self._create_alert(
                _("Connection error"),
                _("Couldn't connect to the server!"))

        from_lang_store = self.lang_from.get_model()

        # Try to set the default from language selection to the user's
        # locale.

        # XXX: If default_locale fails (theoretically could if ENV isn't
        #      proper), this will raise babel.core.UnknownLocaleError.
        locale = babel.default_locale(category="LANG")
        self.locale = Locale(locale)

        self._logger.info("Setting locale to %s", repr(self.locale))

        pairs = self.client.language_pairs()

        from_langs = set()

        # TODO: maybe try falling back to first two letters?
        for pair in pairs:
            try:
                from_locale = Locale.parse(pair[0])
                from_name = from_locale.get_language_name(self.locale)
            except (babel.UnknownLocaleError, ValueError):
                # Fall back to language code
                from_name = pair[0]
                self._logger.error('Failed to get a locale for %s', pair[0])

            from_langs.add((pair[0], from_name))

        from_langs = sorted(list(from_langs), (lambda x, y: cmp(x[1], y[1])))

        for lang in from_langs:
            from_lang_store.append(lang)

        # Fall back to whatever the first option is.
        self.lang_from.set_active(0)

        for idx, lang in enumerate(from_langs):
            # Check if the user's locale is "good enough".
            #
            # e.g. if locale is "en_US", and "en" is in the combobox, then will
            # return non-None.
            if babel.negotiate_locale([lang[0]], [locale]) is not None:
                self.lang_from.set_active(idx)
                break

        # Make sure the to_lang combobox is up to date
        self._lang_from_changed_cb(self.lang_from)

        # Enable the button
        self.translate_button.set_sensitive(True)
        self.remove_alert(alert)

    def _translate_btn_cb(self, button):
        """Callback function for when the "translate text" button is
        clicked. This just calls the "real" callback function, which is run off
        the main thread.
        """

        self.translate_spinner.show()
        self.translate_spinner.start()

        # Change our cursor to a spinner
        gdk_window = self.get_root_window()
        gdk_window.set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

        # Run the translation request in the background
        GObject.idle_add(self._translate_in_background)

    def _translate_in_background(self):
        """Get the text and language choices from the UI elements, and query
        the server for a translation in the background.
        """

        def _reset_gui():
            """Clean up spinner / cursor state."""

            self.translate_spinner.hide()

            # Reset the cursor
            gdk_window = self.get_root_window()
            gdk_window.set_cursor(Gdk.Cursor(Gdk.CursorType.TOP_LEFT_ARROW))

        # TODO: This needs to be made way more robust / featureful

        buf = self.text_from.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(),
                            include_hidden_chars=False)

        # Don't bother doing anything with blank text input.
        if text is None or text.strip() == '':
            self.text_to.get_buffer().set_text('')
            _reset_gui()
            return

        from_lang_iter = self.lang_from.get_active_iter()
        to_lang_iter = self.lang_to.get_active_iter()

        # This shouldn't happen, but let's make sure
        if from_lang_iter is None or to_lang_iter is None:

            self._create_timed_alert(
                _("Select languages!"),
                _("You need to select languages to translate between!"))

            _reset_gui()
            return

        from_lang = self.lang_from.get_model()[from_lang_iter][0]
        to_lang = self.lang_to.get_model()[to_lang_iter][0]

        try:
            result = self.client.translate(text=text, from_lang=from_lang,
                                           to_lang=to_lang)
            self.text_to.get_buffer().set_text(result)

        except TranslateException as exc:
            self._logger.error("Error occured while translating: %s", str(exc))

            self._create_timed_alert(
                _("Couldn't translate text."),
                _("An error occured while trying to translate your text. Try \
again soon."))

        finally:
            _reset_gui()

    def _lang_from_changed_cb(self, combo):
        lang_iter = combo.get_active_iter()

        if lang_iter is not None:
            model = combo.get_model()
            code, lang = model[lang_iter][:2]

            # Remove all the old choices
            self.lang_to.get_model().clear()

            to_langs = set()

            for to_lang in self.client.languages_from(from_lang=code):
                try:
                    to_locale = Locale.parse(to_lang)
                    to_name = to_locale.get_language_name(self.locale)
                except (babel.UnknownLocaleError, ValueError):
                    # Fall back to language code
                    to_name = to_lang
                    self._logger.error('Failed to get locale for %s', to_lang)

                to_langs.add((to_lang, to_name))

            for lang in sorted(list(to_langs), (lambda x, y: cmp(x[1], y[1]))):
                self.lang_to.get_model().append(lang)

            self.lang_to.set_active(0)

    def _create_timed_alert(self, title, msg, timeout=10):
        alert = NotifyAlert(timeout)
        alert.props.title = title
        alert.props.msg = msg
        alert.connect('response', self._alert_cancel_cb)

        self.add_alert(alert)

    def _create_alert(self, title, msg):
        """Create and display an alert that cannot be dismissed by the user."""

        alert = Alert()
        alert.props.title = title
        alert.props.msg = msg
        alert.connect('response', self._alert_cancel_cb)

        self.add_alert(alert)

        return alert

    def _alert_cancel_cb(self, alert, resp_id):
        self.remove_alert(alert)
