# Copyright (C) 2013 Erik Price
#
# TODO: this is GPLv2, use v3
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

from gettext import gettext as _
import logging
import os
import time
import threading

from gi.repository import Gtk, Gdk, Pango, GObject

from sugar3.activity import activity
from sugar3.activity import widgets
from sugar3.activity.widgets import ActivityButton
from sugar3.activity.widgets import DescriptionItem
from sugar3.activity.widgets import ShareButton
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import TitleEntry
from sugar3.graphics import style
from sugar3.graphics.toolbarbox import ToolbarBox

import translate.client


class TranslateActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        GObject.threads_init()

        self.set_title(_("Translate Activity"))

        # XXX: This really needs to be configurable.
        self.client = translate.client.Client('translate.erikprice.net', port=80)

        # XXX: Maybe instead of failing here, how about creating a transient
        #      local server, would use whatever web APIs possible. Not really
        #      sure.

        # TODO: This also should be done in the background so the user doesn't
        #       have to stare at the startup screen / can get better error
        #       information.
        assert self.client.can_connect()

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
        vbox.pack_end(text_hbox, True, True, 0)

        select_hbox.pack_start(Gtk.Label(_("Translate from:")), False, False, 6)

        self.lang_from = Gtk.ComboBoxText()
        self.lang_from.connect("changed", self.on_lang_changed)
        self.lang_from.set_entry_text_column(0)
        select_hbox.pack_start(self.lang_from, False, False, 0)

        select_hbox.pack_start(Gtk.Label(_("Translate to:")), False, False, 6)

        # TODO: A better approach would be like the JS client, where full
        #       language names are displayed, then ISO-639 names are used
        #       internally. Requires more than simple ComboBoxText widget.
        self.lang_to = Gtk.ComboBoxText()
        self.lang_to.connect("changed", self.on_lang_changed)
        self.lang_to.set_entry_text_column(0)
        select_hbox.pack_start(self.lang_to, False, False, 0)

        # These lines are a mouthful, but relatively straightforward. Generate
        # separate lists of from and to languages, sort them alphabetically,
        # and remove duplicates.
        from_langs = sorted(list(set(map((lambda l: l[0]),
                                         self.client.language_pairs()))))
        to_langs = sorted(list(set(map((lambda l: l[1]),
                                       self.client.language_pairs()))))

        for lang in from_langs:
            self.lang_from.append_text(lang)

        for lang in to_langs:
            self.lang_to.append_text(lang)

        button = Gtk.Button(_("Translate text!"))
        button.connect("clicked", self.on_translate_clicked)
        select_hbox.pack_end(button, False, False, 6)

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

        self.set_canvas(vbox)
        vbox.show_all()

        self.translate_spinner.hide()

    def on_translate_clicked(self, button):
        self.translate_spinner.show()
        self.translate_spinner.start()

        # Change our cursor to a spinner
        gdk_window = self.get_root_window()
        gdk_window.set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))

        # Run the translation request in the background
        GObject.idle_add(self.translate_thread)

    def translate_thread(self):

        # TODO: This needs to be made way more robust / featureful

        buf = self.text_from.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(),
                            include_hidden_chars=False)

        from_lang = self.lang_from.get_active_text()
        to_lang = self.lang_to.get_active_text()

        try:
            result = self.client.translate(text=text, from_lang=from_lang,
                                           to_lang=to_lang)
            self.text_to.get_buffer().set_text(result)
        except:
            print("oops, failed, XXX: handle this")

        self.translate_spinner.hide()

        # Reset the cursor
        # XXX: Is this the right cursor? It looks right, but I don't know if
        #      it's the same one
        gdk_window = self.get_root_window()
        gdk_window.set_cursor(Gdk.Cursor(Gdk.CursorType.TOP_LEFT_ARROW))

    def on_lang_changed(self, combo):

        # TODO: Update combo boxes for available language options.

        pass
