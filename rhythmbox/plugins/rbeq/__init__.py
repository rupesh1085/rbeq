# __init__.py
# 
# Rhythmbox Equalizer plugin - a 10-band +-12dB equalizer plugin for 
# Rhythmbox.
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

import pygtk
pygtk.require('2.0')

import gtk
import rb
import equalizer

class RbeqPlugin (rb.Plugin):
    def __init__(self):
        rb.Plugin.__init__(self)
    
    def activate(self,shell):
        self.eq = equalizer.Equalizer()
        self.add_menubar(shell)
        self.eq.set_initial_levels()
        shell.props.shell_player.pause()
        shell.get_player().props.player.add_filter(self.eq.get_eq())
        shell.props.shell_player.play()
    
    def deactivate(self,shell):
        self.eq.change_levels(list(0 for i in range(0,10)))
        uim = shell.get_ui_manager()
        data = shell.get_data('rbeqPluginData')
        uim.remove_ui(data['ui_id'])
        uim.remove_action_group(data['action_group'])
        uim.ensure_update()
        shell.set_data('rbeqPluginData', None)
        del self.eq
        
    def add_menubar(self,shell):
        ui_string = """
        <ui>
          <menubar name="MenuBar">
            <menu name="ToolsMenu" action="Tools">
              <placeholder name="ToolsOps_6">
                <menuitem name="SetEqualizerMenu" action="SetEqualizer" />
              </placeholder>
            </menu>
          </menubar>
        </ui>
        """
        data = dict()
        data['action_group'] = gtk.ActionGroup('RbeqActions')
        action = gtk.Action('SetEqualizer', _('_Set Equalizer'), _("Set the levels of the equalizer"), 'gnome-mime-text-x-python')
        action.connect('activate', self.eq.set_dialog, self)
        data['action_group'].add_action(action)
        uim = shell.get_ui_manager()
        uim.insert_action_group(data['action_group'], 0)
        data['ui_id'] = uim.add_ui_from_string(ui_string)
        shell.set_data('rbeqPluginData', data)
