"""
	-*- coding: utf-8 -*-
	networks.py
	Provided by Package: eapeak
	
	Author: Spencer McIntyre <smcintyre [at] securestate [dot] com>
	
	Copyright 2011 SecureState
	
	This program is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; either version 2 of the License, or
	(at your option) any later version.
	
	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.
	
	You should have received a copy of the GNU General Public License
	along with this program; if not, write to the Free Software
	Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
	MA 02110-1301, USA.
		
"""

from scapy.layers.l2 import eap_types as EAP_TYPES
from xml.sax.saxutils import escape as XMLEscape
from base64 import standard_b64encode as b64encode
from M2Crypto import X509
EAP_TYPES[0] = 'NONE'


class WirelessNetwork:
	ssid = ''	# this is unique
	
	def __init__(self, ssid, bssid = ''):
		self.bssids = []
		self.clients = {}	# indexed by client MAC
		self.eapTypes = []
		self.ssid = ssid
		self.x509certs = []	# list of certificates
		
		if bssid:
			self.bssids.append(bssid)
		#self.datastore = {}	# I love metasploit
			
	def addBSSID(self, bssid):
		if bssid not in self.bssids:
			self.bssids.append(bssid)
			
	def addCertificate(self, certificate):
		"""
		Certificates are either packed binary strings in DER format, or
		instances of m2crypto.X509.X509
		"""
		if not isinstance(certificate, X509.X509):
			try:
				certificate = X509.load_cert_string(certificate, X509.FORMAT_DER)
			except:
				return 1
				
		newFingerprint = certificate.get_fingerprint()
		for oldcert in self.x509certs:
			if newFingerprint == oldcert.get_fingerprint():
				return -1
				
		self.x509certs.append(certificate)
		return 0
			
	def addEapType(self, eapType):
		if eapType not in self.eapTypes and eapType not in [1, 3]:
			self.eapTypes.append(eapType)

	def addClient(self, clientobj):
		if not clientobj.mac in self.clients.keys():
			self.clients[clientobj.mac] = clientobj
			
	def hasClient(self, client_mac):
		"""
		Checks that a client has been seen with this network.
		"""
		if client_mac in self.clients.keys():
			return True
		else:
			return False
	
	def getClient(self, client_mac):
		"""
		Returns a client associated with the give MAC address.
		"""
		if client_mac in self.clients.keys():
			return self.clients[client_mac]
		else:
			return None
		
	def show(self):
		"""
		This returns a string of human readable information describing
		the network object.
		"""
		output = 'SSID: ' + self.ssid + '\n'
		if self.bssids:
			output += 'BSSIDs:\n\t' + "\n\t".join(self.bssids) + '\n'
		if self.eapTypes:
			output += '\tEAP Types:\n'
			for eapType in self.eapTypes:
				if eapType in EAP_TYPES.keys():
					output += '\t\t' + EAP_TYPES[eapType] + '\n'
				else:
					output += '\t\tEAP Type: ' + str(eapType) + '\n'
		if self.clients:
			output += '\tClient Data:\n'
			i = 1
			for client in self.clients.values():
				output += '\t\tClient #' + str(i) + '\n' + client.show(2) + '\n'
				i += 1
		if self.x509certs:
			output += '\tCertificates:\n'
			i = 1
			for cert in self.x509certs:
				output += '\n\tCertificate #' + str(i)
				output += '\n\tExpiration Date: ' + str(cert.get_not_after())
				data = cert.get_issuer()
				output += '\n\tIssuer:'
				for X509_Name_Entry_inst in data.get_entries_by_nid(13): 	# 13 is CN
					output += '\n\t\tCN: ' + X509_Name_Entry_inst.get_data().as_text()
				for X509_Name_Entry_inst in data.get_entries_by_nid(18): 	# 18 is OU
					output += '\n\t\tOU: ' + X509_Name_Entry_inst.get_data().as_text()
				
				data = cert.get_subject()
				output += '\n\tSubject:'
				for X509_Name_Entry_inst in data.get_entries_by_nid(13): 	# 13 is CN
					output += '\n\t\tCN: ' + X509_Name_Entry_inst.get_data().as_text()
				for X509_Name_Entry_inst in data.get_entries_by_nid(18): 	# 18 is OU
					output += '\n\t\tOU: ' + X509_Name_Entry_inst.get_data().as_text()
				key_size = (cert.get_pubkey().size()) * 8
				del data
				output += '\n'
				i += 1
			del cert
		return output[:-1]
		
	def updateSSID(self, ssid):
		self.ssid = ssid

	def getXML(self):
		"""
		This returns the XML representation of the client object.
		"""
		from xml.etree import ElementTree
		root = ElementTree.Element('wireless-network')
		for bssid in self.bssids:
			ElementTree.SubElement(root, 'BSSID').text = bssid
		tmp = ElementTree.SubElement(root, 'SSID')
		ElementTree.SubElement(tmp, 'type').text = 'Beacon'
		essid = ElementTree.SubElement(tmp, 'essid')
		essid.set('cloaked', 'false')
		essid.text = XMLEscape(self.ssid)
		if self.eapTypes:
			ElementTree.SubElement(tmp, 'eap-types').text = ",".join([str(i) for i in self.eapTypes])

		for client in self.clients.values():
			root.append(client.getXML())
		for cert in self.x509certs:
			tmp = ElementTree.SubElement(root, 'certificate')
			tmp.text = b64encode(cert.as_der())
			tmp.set('encoding', 'DER')
			
		return root
