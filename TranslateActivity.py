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

from gi.repository import Gtk, Gdk, Pango

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

        self.set_title("Translate Activity")
        self.client = translate.client.Client('TODO', port='TODO')

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

        self.lang_to = Gtk.ComboBoxText()
        self.lang_to.connect("changed", self.on_lang_changed)
        self.lang_to.set_entry_text_column(0)
        select_hbox.pack_start(self.lang_to, False, False, 0)

        for lang in ['these', 'are', 'fake', 'language', 'entries']:
            self.lang_from.append_text(lang)
            self.lang_to.append_text(lang)

        button = Gtk.Button(_("Translate text!"))
        select_hbox.pack_end(button, False, False, 6)

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

    def on_translate_clicked(self, button):
        pass

    def on_lang_changed(self, combo):
        pass
