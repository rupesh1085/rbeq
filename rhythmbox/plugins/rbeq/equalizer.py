# equalizer.py
#
# Implements a 10-channel equalizer via GStreamer for the Rhythmbox Equalizer 
# plugin.
#
#       Copyright 2009 Christopher Kruse <kruse.christopher@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
import pygst
import gst
import pygtk
import gtk
import gconf
import gobject

gconf_str = "/apps/rhythmbox/plugins/rbeq/last_values"
last_preset = "/apps/rhythmbox/plugins/rbeq/last_preset"

class Equalizer:
    presetListStore = gtk.ListStore(gobject.TYPE_STRING)
    sliders = []
    combo = gtk.ComboBoxEntry()
    def __init__(self):
        self.equ = gst.element_factory_make("equalizer-10bands")
        self.conf_client = gconf.client_get_default()
        try:
            preset= self.conf_client.get_string(last_preset)
        except RuntimeError:
            self.conf_client.set_string(last_preset, "")
        try:
            level_str = self.conf_client.get_string(gconf_str)
            self.current_levels = list(float(i) for i in level_str.split(","))
            self.update_preset_list()
        except AttributeError:
            lst = list(str(0) for i in range(0,10))
            values = ",".join(lst)
            self.conf_client.set_string(gconf_str, values)
            self.current_levels = list(self.equ.get_property('band' + str(i)) for i in range(0,10))
    
    def change_levels(self, levels):
        for i in range(0,10):
            self.equ.set_property('band' + str(i), levels[i]) 
    
    def get_eq(self):
        return self.equ

    def get_current_levels(self):
        levels = list(self.get_eq().get_property('band' + str(i)) for i in range(0,10))
        return levels

    def set_current_levels(self, lvls):
        self.current_levels = lvls
        self.conf_client.set_string(gconf_str,",".join(str(i) for i in lvls))
    
    def preset_changed(self, preset_combo):
        model = preset_combo.get_model()
        current_sel = preset_combo.get_active_iter()
        if current_sel != None :
            selected = model.get_value(current_sel,0)
            gst.Preset.load_preset(self.get_eq(), selected)
            self.conf_client.set_string(last_preset, selected)
    
    def set_initial_levels(self):
        self.change_levels(self.get_current_levels())

    def read_presets(self):
        prop_names = sorted(gst.Preset.get_preset_names(self.equ))
        return prop_names

    def update_sliders(self, preset_combo):
        current_lvls = self.get_current_levels()
        for i in range(0,len(current_lvls)):
            value = current_lvls[i]
            self.sliders[i].set_value(value)

    def on_slider_change(self, action, sliders):
        slider_values = list(i.get_value() for i in sliders)
        self.change_levels(slider_values)
        self.set_current_levels(slider_values)
    
    def on_dialog_delete(self, action, source, dialog):
        dialog.hide()

    def add_preset(self, dialog, response,rb_context,entry):
        if response == gtk.RESPONSE_ACCEPT:
            gst.Preset.save_preset(self.get_eq(),entry.get_text())
            self.conf_client.set_string(last_preset,entry.get_text())
            self.update_preset_list()
        dialog.destroy()

    def delete_preset(self, calling_btn, rb_context, preset_combo):
        model = preset_combo.get_model()
        sel = preset_combo.get_active_iter()
        val = model.get_value(sel, 0)
        gst.Preset.delete_preset(self.get_eq(), val)
        self.update_preset_list()
        preset_combo.set_active(0)

    def confirm_save(self, calling_btn, rb_context, parent):
        save_dialog = gtk.Dialog("Save Preset", parent, 
            gtk.DIALOG_MODAL, (gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT,
            gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT))
        content_area = save_dialog.get_content_area()
        save_label = gtk.Label("Preset Name:")
        content_area.add(save_label)
        save_entry = gtk.Entry()
        save_entry.set_activates_default(True)
        content_area.add(save_entry)
        content_area.show_all()
        save_dialog.set_default_response(gtk.RESPONSE_ACCEPT)
        save_dialog.connect("response",self.add_preset,rb_context,save_entry)
        save_dialog.run()

    def update_preset_list(self):
        self.presetListStore.clear()
        names = self.read_presets()
        for i,name in zip(range(len(names)),names):
            iter = self.presetListStore.append()
            self.presetListStore.set(iter,0,name)
            if name == self.conf_client.get_string(last_preset) :
                self.combo.set_active(i)

    def set_dialog(self,action, rb_context):
        builder = gtk.Builder()
        builder.add_from_file(rb_context.find_file("rbeq_ui.xml"))
        dialog = builder.get_object("window1")
        dialog.connect('delete-event', self.on_dialog_delete, dialog)
        self.sliders = list(builder.get_object(
            "slider"+str(i)) for i in range(1,11))
        lvl = self.get_current_levels()
        for i in range(0,len(self.sliders)):
            self.sliders[i].connect("value-changed", self.on_slider_change,
                self.sliders)
            self.sliders[i].set_value(lvl[i])
        self.presetListStore = builder.get_object("presetListStore")

        self.combo = builder.get_object("presetCombo")
        cell = gtk.CellRendererText()
        cell.set_fixed_height_from_font(1)
        self.combo.pack_start(cell,False)
        self.combo.add_attribute(cell, 'text',0)
        if self.conf_client.get_string(last_preset) == "" :
            self.combo.set_active(0)

        self.combo.connect("changed", self.preset_changed)
        self.combo.connect("changed", self.update_sliders)

        # Set Preset Button actions
        del_preset_btn = builder.get_object("deletePresetBtn")
        del_preset_btn.connect("clicked", self.delete_preset, 
            rb_context, self.combo)
        save_preset_btn = builder.get_object("savePresetBtn")    
        save_preset_btn.connect("clicked", self.confirm_save, 
            rb_context, dialog)
        self.update_preset_list()
        dialog.show() 

