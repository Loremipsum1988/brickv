# -*- coding: utf-8 -*-
"""
RED Plugin
Copyright (C) 2014 Ishraq Ibne Ashraf <ishraq@tinkerforge.com>

red_tab_settings_ap.py: RED settings access point tab implementation

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

import json
from PyQt4 import Qt, QtCore, QtGui
from brickv.plugin_system.plugins.red.ui_red_tab_settings_ap import Ui_REDTabSettingsAP
from brickv.plugin_system.plugins.red.api import *
from brickv.plugin_system.plugins.red import config_parser
from brickv.async_call import async_call
from brickv.utils import get_main_window

BUTTON_STATE_DEFAULT = 1
BUTTON_STATE_REFRESH = 2
BUTTON_STATE_APPLY   = 3

AP_INTERFACE_IP_USER_ROLE = QtCore.Qt.UserRole + 1
AP_INTERFACE_MASK_USER_ROLE = QtCore.Qt.UserRole + 2

HOSTAPD_CONF_PATH = '/etc/hostapd/hostapd.conf'
DNSMASQ_CONF_PATH = '/etc/dnsmasq.conf'

class REDTabSettingsAP(QtGui.QWidget, Ui_REDTabSettingsAP):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setupUi(self)
        
        self.session        = None # Set from REDTabSettings
        self.script_manager = None # Set from REDTabSettings

        self.is_tab_on_focus = False

        self.applying = False
        self.ap_mode = False
        self.label_ap_disabled.hide()
        self.label_applying.hide()
        self.pbar_applying.hide()
        
        self.cbox_ap_interface.currentIndexChanged.connect(self.slot_cbox_ap_interface_current_index_changed)
        self.chkbox_ap_wpa_key_show.stateChanged.connect(self.slot_chkbox_ap_wpa_key_show_state_changed)
        self.chkbox_ap_enable_dns_dhcp.stateChanged.connect(self.slot_chkbox_ap_enable_dns_dhcp_state_changed)
        self.pbutton_ap_refresh.clicked.connect(self.slot_pbutton_ap_refresh_clicked)
        self.pbutton_ap_apply.clicked.connect(self.slot_pbutton_ap_apply_clicked)

    def tab_on_focus(self):
        self.is_tab_on_focus = True
        
        if self.applying:
            return

        self.slot_pbutton_ap_refresh_clicked()

    def tab_off_focus(self):
        self.is_tab_on_focus = False

    def tab_destroy(self):
        pass

    def update_button_text_state(self, state):
        if state == BUTTON_STATE_DEFAULT:
            self.pbutton_ap_refresh.setEnabled(True)
            self.pbutton_ap_refresh.setText('Refresh')
            self.pbutton_ap_apply.setText('Apply')

        elif state == BUTTON_STATE_REFRESH:
            self.pbutton_ap_refresh.setText('Refreshing...')
            self.pbutton_ap_refresh.setEnabled(False)
            self.pbutton_ap_apply.setText('Apply')

        else:
            self.pbutton_ap_refresh.setText('Refresh')
            self.pbutton_ap_apply.setText('Applying...')

    def dns_dhcp_gui(self, enable):
        if enable:
            self.ledit_ap_domain.setEnabled(True)
            self.sbox_ap_pool_start1.setEnabled(True)
            self.sbox_ap_pool_start2.setEnabled(True)
            self.sbox_ap_pool_start3.setEnabled(True)
            self.sbox_ap_pool_start4.setEnabled(True)
            
            self.sbox_ap_pool_end1.setEnabled(True)
            self.sbox_ap_pool_end2.setEnabled(True)
            self.sbox_ap_pool_end3.setEnabled(True)
            self.sbox_ap_pool_end4.setEnabled(True)
            
            self.sbox_ap_pool_mask1.setEnabled(True)
            self.sbox_ap_pool_mask2.setEnabled(True)
            self.sbox_ap_pool_mask3.setEnabled(True)
            self.sbox_ap_pool_mask4.setEnabled(True)
        else:
            self.ledit_ap_domain.setEnabled(False)
            self.sbox_ap_pool_start1.setEnabled(False)
            self.sbox_ap_pool_start2.setEnabled(False)
            self.sbox_ap_pool_start3.setEnabled(False)
            self.sbox_ap_pool_start4.setEnabled(False)
            
            self.sbox_ap_pool_end1.setEnabled(False)
            self.sbox_ap_pool_end2.setEnabled(False)
            self.sbox_ap_pool_end3.setEnabled(False)
            self.sbox_ap_pool_end4.setEnabled(False)
            
            self.sbox_ap_pool_mask1.setEnabled(False)
            self.sbox_ap_pool_mask2.setEnabled(False)
            self.sbox_ap_pool_mask3.setEnabled(False)
            self.sbox_ap_pool_mask4.setEnabled(False)

    def slot_cbox_ap_interface_current_index_changed(self, index):
        ip = self.cbox_ap_interface.itemData(index, AP_INTERFACE_IP_USER_ROLE).toString()
        mask = self.cbox_ap_interface.itemData(index, AP_INTERFACE_MASK_USER_ROLE).toString()

        if ip and mask:
            ip_list = ip.split('.')
            ip1 = ip_list[0]
            ip2 = ip_list[1]
            ip3 = ip_list[2]
            ip4 = ip_list[3]
            
            mask_list = mask.split('.')
            mask1 = mask_list[0]
            mask2 = mask_list[1]
            mask3 = mask_list[2]
            mask4 = mask_list[3]
            
            self.sbox_ap_intf_ip1.setValue(int(ip1))
            self.sbox_ap_intf_ip2.setValue(int(ip2))
            self.sbox_ap_intf_ip3.setValue(int(ip3))
            self.sbox_ap_intf_ip4.setValue(int(ip4))
            
            self.sbox_ap_intf_mask1.setValue(int(mask1))
            self.sbox_ap_intf_mask2.setValue(int(mask2))
            self.sbox_ap_intf_mask3.setValue(int(mask3))
            self.sbox_ap_intf_mask4.setValue(int(mask4))

    def slot_chkbox_ap_wpa_key_show_state_changed(self, state):
        if state == QtCore.Qt.Checked:
            self.ledit_ap_wpa_key.setEchoMode(QtGui.QLineEdit.Normal)
        else:
            self.ledit_ap_wpa_key.setEchoMode(QtGui.QLineEdit.Password)

    def slot_chkbox_ap_enable_dns_dhcp_state_changed(self, state):
        if state == QtCore.Qt.Checked:
            self.dns_dhcp_gui(True)
        else:
            self.dns_dhcp_gui(False)

    def slot_pbutton_ap_refresh_clicked(self):
        def cb_settings_network_apmode_check(result):
            self.update_button_text_state(BUTTON_STATE_DEFAULT)

            if not self.is_tab_on_focus:
                return

            if result and not result.stderr and result.exit_code == 0:
                ap_mode_check = json.loads(result.stdout)
                if ap_mode_check['ap_interface'] is None or \
                   ap_mode_check['ap_enabled'] is None or \
                   ap_mode_check['ap_active'] is None:
                        self.label_ap_status.setText('-')
                        QtGui.QMessageBox.critical(get_main_window(),
                                                   'Settings | Access Point',
                                                   'Error checking access point mode.',
                                                   QtGui.QMessageBox.Ok)
                elif ap_mode_check['ap_interface'] and \
                     ap_mode_check['ap_enabled']:
                        if ap_mode_check['ap_active']:
                            self.label_ap_status.setText('Active')
                        else:
                            self.label_ap_status.setText('Inactive')

                        self.ap_mode_enabled()
                else:
                    self.label_ap_status.setText('-')
                    self.ap_mode_disabled()

            else:
                self.label_ap_status.setText('-')
                self.update_button_text_state(BUTTON_STATE_DEFAULT)
                err_msg = 'Error checking access point mode\n\n'+unicode(result.stderr)
                QtGui.QMessageBox.critical(get_main_window(),
                                           'Settings | Access Point',
                                           err_msg,
                                           QtGui.QMessageBox.Ok)

        self.update_button_text_state(BUTTON_STATE_REFRESH)

        self.script_manager.execute_script('settings_network_apmode_check',
                                           cb_settings_network_apmode_check)

    def slot_pbutton_ap_apply_clicked(self):      
        def cb_settings_network_apmode_apply(result):
            self.label_applying.hide()
            self.pbar_applying.hide()
            self.applying = False
            self.sarea_ap.setEnabled(True)
            self.update_button_text_state(BUTTON_STATE_DEFAULT)

            if result and result.exit_code == 0:
                self.slot_pbutton_ap_refresh_clicked()

                QtGui.QMessageBox.information(get_main_window(),
                                              'Settings | Access Point',
                                              'Access point settings applied.',
                                              QtGui.QMessageBox.Ok)
            else:
                err_msg = 'Error applying access point settings.\n\n' + result.stderr
                QtGui.QMessageBox.critical(get_main_window(),
                                           'Settings | Access Point',
                                           err_msg,
                                           QtGui.QMessageBox.Ok)

        apply_dict = {'interface'       : None,
                      'interface_ip'    : None,
                      'interface_mask'  : None,
                      'ssid'            : None,
                      'ssid_hidden'     : None,
                      'wpa_key'         : None,
                      'channel'         : None,
                      'enabled_dns_dhcp': None,
                      'server_name'     : None,
                      'domain'          : None,
                      'dhcp_start'      : None,
                      'dhcp_end'        : None,
                      'dhcp_mask'       : None}
        try:
            interface = self.cbox_ap_interface.currentText()
            interface_ip = self.cbox_ap_interface.itemData(self.cbox_ap_interface.currentIndex(),
                                                           AP_INTERFACE_IP_USER_ROLE).toString()
            interface_mask = self.cbox_ap_interface.itemData(self.cbox_ap_interface.currentIndex(),
                                                             AP_INTERFACE_MASK_USER_ROLE).toString()
            ssid = self.ledit_ap_ssid.text()
            
            if self.chkbox_ap_ssid_hidden.checkState() == QtCore.Qt.Checked:
                ssid_hidden = True
            else:
                ssid_hidden = False
            
            wpa_key = self.ledit_ap_wpa_key.text()
            channel = unicode(self.sbox_ap_channel.value())
            
            if self.chkbox_ap_enable_dns_dhcp.checkState() == QtCore.Qt.Checked:
                enabled_dns_dhcp =  True
            else:
                enabled_dns_dhcp =  False
            
            server_name = self.ledit_ap_server_name.text()
            
            domain = self.ledit_ap_domain.text()

            dhcp_start_list = []
            dhcp_start_list.append(unicode(self.sbox_ap_pool_start1.value()))
            dhcp_start_list.append(unicode(self.sbox_ap_pool_start2.value()))
            dhcp_start_list.append(unicode(self.sbox_ap_pool_start3.value()))
            dhcp_start_list.append(unicode(self.sbox_ap_pool_start4.value()))
            dhcp_start = '.'.join(dhcp_start_list)
            
            dhcp_end_list = []
            dhcp_end_list.append(unicode(self.sbox_ap_pool_end1.value()))
            dhcp_end_list.append(unicode(self.sbox_ap_pool_end2.value()))
            dhcp_end_list.append(unicode(self.sbox_ap_pool_end3.value()))
            dhcp_end_list.append(unicode(self.sbox_ap_pool_end4.value()))
            dhcp_end = '.'.join(dhcp_end_list)
            
            dhcp_mask_list = []
            dhcp_mask_list.append(unicode(self.sbox_ap_pool_mask1.value()))
            dhcp_mask_list.append(unicode(self.sbox_ap_pool_mask2.value()))
            dhcp_mask_list.append(unicode(self.sbox_ap_pool_mask3.value()))
            dhcp_mask_list.append(unicode(self.sbox_ap_pool_mask4.value()))
            dhcp_mask = '.'.join(dhcp_mask_list)

            if not interface:
                QtGui.QMessageBox.critical(get_main_window(),
                                           'Settings | Access Point',
                                           'Interface empty.',
                                           QtGui.QMessageBox.Ok)
                return

            elif not ssid:
                QtGui.QMessageBox.critical(get_main_window(),
                                           'Settings | Access Point',
                                           'SSID empty.',
                                           QtGui.QMessageBox.Ok)
                return

            elif not wpa_key:
                QtGui.QMessageBox.critical(get_main_window(),
                                           'Settings | Access Point',
                                           'WPA key empty.',
                                           QtGui.QMessageBox.Ok)
                return
            
            elif not server_name:
                QtGui.QMessageBox.critical(get_main_window(),
                                           'Settings | Access Point',
                                           'Server name empty.',
                                           QtGui.QMessageBox.Ok)
                return

            elif not domain:
                QtGui.QMessageBox.critical(get_main_window(),
                                           'Settings | Access Point',
                                           'Domain empty.',
                                           QtGui.QMessageBox.Ok)
                return

            apply_dict['interface']        = interface
            apply_dict['interface_ip']     = interface_ip
            apply_dict['interface_mask']   = interface_mask
            apply_dict['ssid']             = ssid
            apply_dict['ssid_hidden']      = ssid_hidden
            apply_dict['wpa_key']          = wpa_key
            apply_dict['channel']          = channel
            apply_dict['enabled_dns_dhcp'] = enabled_dns_dhcp
            apply_dict['server_name']      = server_name
            apply_dict['domain']           = domain
            apply_dict['dhcp_start']       = dhcp_start
            apply_dict['dhcp_end']         = dhcp_end
            apply_dict['dhcp_mask']        = dhcp_mask

            self.applying = True
            self.label_applying.show()
            self.pbar_applying.show()
            self.sarea_ap.setEnabled(False)
            self.update_button_text_state(BUTTON_STATE_APPLY)

            self.script_manager.execute_script('settings_network_apmode_apply',
                                               cb_settings_network_apmode_apply,
                                               [json.dumps(apply_dict)])

        except Exception as e:
            self.label_applying.hide()
            self.pbar_applying.hide()
            self.applying = False
            self.sarea_ap.show()
            self.update_button_text_state(BUTTON_STATE_DEFAULT)
            err_msg = 'Error occured while processing input data.\n\n' + str(e)

            QtGui.QMessageBox.critical(get_main_window(),
                                       'Settings | Access Point',
                                       err_msg,
                                       QtGui.QMessageBox.Ok)

    def ap_mode_enabled(self):
        self.ap_mode = True
        self.label_ap_disabled.hide()
        self.sarea_ap.show()

        self.hostapd_conf_rfile = REDFile(self.session)
        self.dnsmasq_conf_rfile = REDFile(self.session)
        self.interfaces_conf_rfile = REDFile(self.session)
        
        def cb_open_hostapd_conf(red_file):
            def cb_read(red_file, result):
                red_file.release()

                if not self.is_tab_on_focus:
                    return

                if result and result.data and not result.error:
                    try:
                        def cb_settings_network_apmode_get_interfaces(result):
                            if not self.is_tab_on_focus:
                                return
                        
                            if result and not result.stderr and result.exit_code == 0:
                                ap_mode_interfaces = json.loads(result.stdout)

                                self.cbox_ap_interface.clear()

                                self.cbox_ap_interface.currentIndexChanged.disconnect()

                                for intf in ap_mode_interfaces:
                                    self.cbox_ap_interface.addItem(intf)
                                    current_item_index = self.cbox_ap_interface.count() - 1

                                    if ap_mode_interfaces[intf]['ip']:
                                        self.cbox_ap_interface.setItemData(current_item_index,
                                                                           QtCore.QVariant(ap_mode_interfaces[intf]['ip']),
                                                                           AP_INTERFACE_IP_USER_ROLE)
                                    else:
                                        self.cbox_ap_interface.setItemData(current_item_index,
                                                                           QtCore.QVariant('192.168.42.1'),
                                                                           AP_INTERFACE_IP_USER_ROLE)

                                    if ap_mode_interfaces[intf]['mask']:
                                        self.cbox_ap_interface.setItemData(current_item_index,
                                                                           QtCore.QVariant(ap_mode_interfaces[intf]['mask']),
                                                                           AP_INTERFACE_MASK_USER_ROLE)

                                    else:
                                        self.cbox_ap_interface.setItemData(current_item_index,
                                                                           QtCore.QVariant('255.255.255.0'),
                                                                           AP_INTERFACE_MASK_USER_ROLE)
                                self.cbox_ap_interface.setCurrentIndex(-1)
                                self.cbox_ap_interface.currentIndexChanged.connect(self.slot_cbox_ap_interface_current_index_changed)

                                if not interface:
                                    self.cbox_ap_interface.setCurrentIndex(0)

                                elif not interface and self.cbox_ap_interface.count() > 0:
                                    self.cbox_ap_interface.setCurrentIndex(0)

                                else:
                                    broke = False
                                    for i in range(0, self.cbox_ap_interface.count()):
                                        if self.cbox_ap_interface.itemText(i) == interface:
                                            self.cbox_ap_interface.setCurrentIndex(i)
                                            broke = True
                                            break

                                    if not broke:
                                        self.cbox_ap_interface.setCurrentIndex(0)
                            else:
                                err_msg = 'Error getting access point interfaces.\n\n' + result.stderr
                                QtGui.QMessageBox.critical(get_main_window(),
                                                           'Settings | Access Point',
                                                           err_msg,
                                                           QtGui.QMessageBox.Ok)

                        hostapd_conf = result.data.decode('utf-8')
                        
                        if hostapd_conf:
                            lines = hostapd_conf.splitlines()

                            interface   = ''
                            ssid        = ''
                            channel     = 1
                            ssid_hidden = '0'
                            wpa_key     = ''

                            for l in lines:
                                l_split = l.strip().split('=')
    
                                if len(l_split) != 2:
                                    continue
    
                                if l_split[0].strip(' ') == 'interface':
                                    interface = l_split[1].strip(' ')
    
                                elif l_split[0].strip(' ') == 'ssid':
                                    ssid = l_split[1].strip(' ')
                                
                                elif l_split[0].strip(' ') == 'channel':
                                    channel = l_split[1].strip(' ')
                                
                                elif l_split[0].strip(' ') == 'ignore_broadcast_ssid':
                                    ssid_hidden = l_split[1].strip(' ')
                                
                                elif l_split[0].strip(' ') == 'wpa_passphrase':
                                    wpa_key = l_split[1]

                            self.script_manager.execute_script('settings_network_apmode_get_interfaces',
                                                               cb_settings_network_apmode_get_interfaces)
                            self.ledit_ap_ssid.setText(ssid)

                            if ssid_hidden == '0':
                                self.chkbox_ap_ssid_hidden.setCheckState(QtCore.Qt.Unchecked)
                            else:
                                self.chkbox_ap_ssid_hidden.setCheckState(QtCore.Qt.Checked)

                            self.sbox_ap_channel.setValue(int(channel))
                            self.ledit_ap_wpa_key.setText(wpa_key)

                    except Exception as e:
                        err_msg = 'Error parsing hostapd.conf\n\n' + str(e)
                        QtGui.QMessageBox.critical(get_main_window(),
                                                   'Settings | Access Point',
                                                   err_msg,
                                                   QtGui.QMessageBox.Ok)
                else:
                    err_msg = 'Error reading hostapd.conf\n\n'+result.error
                    QtGui.QMessageBox.critical(get_main_window(),
                                               'Settings | Access Point',
                                               err_msg,
                                               QtGui.QMessageBox.Ok)

            red_file.read_async(4096, lambda x: cb_read(red_file, x))

        def cb_open_error_hostapd_conf():
            err_msg = 'Error opening hostapd.conf'
            QtGui.QMessageBox.critical(get_main_window(),
                                       'Settings | Access Point',
                                       err_msg,
                                       QtGui.QMessageBox.Ok)

        def cb_open_dnsmasq_conf(red_file):
            def cb_read(red_file, result):
                red_file.release()

                if not self.is_tab_on_focus:
                    return

                if result and result.data and not result.error:
                    try:
                        dnsmasq_conf = result.data.decode('utf-8')
                        if dnsmasq_conf:
                            dns_dhcp_enabled = True
                            dhcp_range_start = '192.168.42.50'
                            dhcp_range_end = '192.168.42.254'
                            server_name = 'red-brick'
                            domain = 'tf.local'
                            dhcp_option_netmask = '255.255.255.0'

                            lines = dnsmasq_conf.splitlines()

                            for l in lines:
                                if l.strip().strip(' ') == '#Enabled':
                                    dns_dhcp_enabled = True
                                elif l.strip().strip(' ') == '#Disabled':
                                    dns_dhcp_enabled = False

                                l_split = l.strip().split('=')
    
                                if len(l_split) != 2:
                                    continue

                                if l_split[0].strip(' ') == 'dhcp-range':
                                    dhcp_range = l_split[1].strip(' ').split(',')
                                    dhcp_range_start = dhcp_range[0]
                                    dhcp_range_end = dhcp_range[1]
    
                                elif l_split[0].strip(' ') == 'address':
                                    l_split1 = l_split[1].split('/')
                                    if len(l_split1) == 3:
                                        server_name = l_split1[1]
    
                                elif l_split[0].strip(' ') == 'domain':
                                    domain= l_split[1].strip(' ')
                                
                                elif l_split[0].strip(' ') == 'dhcp-option':
                                    dhcp_option = l_split[1].strip(' ').split(',')
                                    if len(dhcp_option) == 2:
                                        if dhcp_option[0].strip(' ') == 'option:netmask':
                                            dhcp_option_netmask = dhcp_option[1]
                            
                            if dns_dhcp_enabled:
                                self.chkbox_ap_enable_dns_dhcp.setCheckState(QtCore.Qt.Unchecked)
                                self.chkbox_ap_enable_dns_dhcp.setCheckState(QtCore.Qt.Checked)
                            else:
                                self.chkbox_ap_enable_dns_dhcp.setCheckState(QtCore.Qt.Checked)
                                self.chkbox_ap_enable_dns_dhcp.setCheckState(QtCore.Qt.Unchecked)

                            if server_name:
                                self.ledit_ap_server_name.setText(server_name)

                            if domain:
                                self.ledit_ap_domain.setText(domain)

                            dhcp_range_start_list = dhcp_range_start.split('.')
                            dhcp_range_end_list = dhcp_range_end.split('.')
                            dhcp_option_netmask_list = dhcp_option_netmask.split('.')
                            
                            self.sbox_ap_pool_start1.setValue(int(dhcp_range_start_list[0]))
                            self.sbox_ap_pool_start2.setValue(int(dhcp_range_start_list[1]))
                            self.sbox_ap_pool_start3.setValue(int(dhcp_range_start_list[2]))
                            self.sbox_ap_pool_start4.setValue(int(dhcp_range_start_list[3]))
                            
                            self.sbox_ap_pool_end1.setValue(int(dhcp_range_end_list[0]))
                            self.sbox_ap_pool_end2.setValue(int(dhcp_range_end_list[1]))
                            self.sbox_ap_pool_end3.setValue(int(dhcp_range_end_list[2]))
                            self.sbox_ap_pool_end4.setValue(int(dhcp_range_end_list[3]))
                            
                            self.sbox_ap_pool_mask1.setValue(int(dhcp_option_netmask_list[0]))
                            self.sbox_ap_pool_mask2.setValue(int(dhcp_option_netmask_list[1]))
                            self.sbox_ap_pool_mask3.setValue(int(dhcp_option_netmask_list[2]))
                            self.sbox_ap_pool_mask4.setValue(int(dhcp_option_netmask_list[3]))

                    except Exception as e:
                        err_msg = 'Error parsing dnsmasq.conf\n\n' + str(e)
                        QtGui.QMessageBox.critical(get_main_window(),
                                                   'Settings | Access Point',
                                                   err_msg,
                                                   QtGui.QMessageBox.Ok)
                else:
                    err_msg = 'Error reading dnsmasq.conf\n\n'+result.error
                    QtGui.QMessageBox.critical(get_main_window(),
                                               'Settings | Access Point',
                                               err_msg,
                                               QtGui.QMessageBox.Ok)

            red_file.read_async(4096, lambda x: cb_read(red_file, x))

        def cb_open_error_dnsmasq_conf():
            err_msg = 'Error opening dnsmasq.conf'
            QtGui.QMessageBox.critical(get_main_window(),
                                       'Settings | Access Point',
                                       err_msg,
                                       QtGui.QMessageBox.Ok)
        
        async_call(self.hostapd_conf_rfile.open,
                   (HOSTAPD_CONF_PATH, REDFile.FLAG_READ_ONLY | REDFile.FLAG_NON_BLOCKING, 0, 0, 0),
                   cb_open_hostapd_conf,
                   cb_open_error_hostapd_conf)

        async_call(self.dnsmasq_conf_rfile.open,
                   (DNSMASQ_CONF_PATH, REDFile.FLAG_READ_ONLY | REDFile.FLAG_NON_BLOCKING, 0, 0, 0),
                   cb_open_dnsmasq_conf,
                   cb_open_error_dnsmasq_conf)

    def ap_mode_disabled(self):
        self.ap_mode = False
        self.label_ap_disabled.show()
        self.sarea_ap.hide()