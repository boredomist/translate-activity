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

        vbox = Gtk.Box(spacing=6)
        hbox = Gtk.Box(spacing=6)
        hbox.orientation = Gtk.Orientation.HORIZONTAL

        button = Gtk.Button(_("Translate text"))
        button.connect("clicked", self.on_translate_clicked)
        vbox.pack_start(button, True, True, 0)

        # This is so wrong.

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(False)
        scrolled_window.set_vexpand(True)

        from_textview = Gtk.TextView()
        from_textview.get_buffer().set_text("This is where you would type in \
some text to translate.")

        scrolled_window.add(from_textview)
        hbox.pack_start(scrolled_window, True, True, 0)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(False)
        scrolled_window.set_vexpand(True)

        to_textview = Gtk.TextView()
        to_textview.get_buffer().set_text("This is where the translated text \
would show up.")

        scrolled_window.add(to_textview)
        hbox.pack_start(scrolled_window, True, True, 0)


        vbox.pack_start(hbox, True, True, 0)

        self.set_canvas(vbox)
        vbox.show_all()

    def on_translate_clicked(self, button):
        pass
