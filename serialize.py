import xml.dom.minidom
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parse
import cStringIO
import os
import gtk

from sugar.datastore import datastore

from constants import Constants
from instance import Instance
import utils
from recorded import Recorded
import recorded
from savedmap  import SavedMap

def fillMediaHash( index, m ):
	doc = None
	if (os.path.exists(index)):
		try:
			doc = parse( os.path.abspath(index) )
		except:
			doc = None
	if (doc == None):
		return

	try:
		lastLat = doc.documentElement.getAttributeNode(Constants.mapLat).nodeValue
		lastLng = doc.documentElement.getAttributeNode(Constants.mapLng).nodeValue
		lastZoom = doc.documentElement.getAttributeNode(Constants.mapZoom).nodeValue
		m.ca.preComet()
		m.ca.cometLogic.handleReceivedMap(lastLat,lastLng,lastZoom)
		m.ca.postComet()
	except:
		# likely an old saved map
		lastLat = 0

	recdElements = doc.documentElement.getElementsByTagName(Constants.recdMapItem)
	for el in recdElements:
		_loadMediaIntoHash( el, m )

	saveElements = doc.documentElement.getElementsByTagName(Constants.recdSavedMapItem)
	for el in saveElements:
		_loadSavedMap( el, m )

	saveElements = doc.documentElement.getElementsByTagName(Constants.recdInfoMarker)
	for el in saveElements:
		_loadInfoMarker( el, m )

	saveElements = doc.documentElement.getElementsByTagName(Constants.recdLine)
	for el in saveElements:
		_loadLine( el, m )

def _loadSavedMap( el, m ):
	latNode = el.getAttributeNode(Constants.recdLat)
	lat = latNode.nodeValue
	lngNode = el.getAttributeNode(Constants.recdLng)
	lng = lngNode.nodeValue
	
	zoomNode = el.getAttributeNode(Constants.recdZoom)
	zoom = zoomNode.nodeValue
	notesNode = el.getAttributeNode(Constants.recdNotes)
	notes = notesNode.nodeValue
	tagsNode = el.getAttributeNode(Constants.recdTags)
	tags = tagsNode.nodeValue

	m.ca.addSavedMap(lat,lng,zoom,notes,False)

def _loadInfoMarker( el, m ):
	latNode = el.getAttributeNode(Constants.recdLat)
	lat = latNode.nodeValue
	lngNode = el.getAttributeNode(Constants.recdLng)
	lng = lngNode.nodeValue
	infoNode = el.getAttributeNode(Constants.recdInfo)
	info = infoNode.nodeValue
	iconNode = el.getAttributeNode(Constants.recdIcon)
	icon = iconNode.nodeValue
	m.setInfo(lat,lng,info,icon)

def _loadLine( el, m ):
	idNode = el.getAttributeNode(Constants.lineID)
	id = idNode.nodeValue
	colorNode = el.getAttributeNode(Constants.lineColor)
	color = colorNode.nodeValue
	thickNode = el.getAttributeNode(Constants.lineThick)
	thick = thickNode.nodeValue
	ptsNode = el.getAttributeNode(Constants.linePts)
	pts = ptsNode.nodeValue
	m.setLine(id,color,thick,pts)

def _loadMediaIntoHash( el, m ):
	if (el.getAttributeNode(Constants.recdDatastoreId) == None):
		return

	datastoreNode = el.getAttributeNode(Constants.recdDatastoreId)
	if (datastoreNode != None):
		datastoreId = datastoreNode.nodeValue
		if (datastoreId != None):
			#quickly check: if you have a datastoreId that the file hasn't been deleted,
			#cause if you do, we need to flag your removal
			#2904 trac
			datastoreOb = getMediaFromDatastore(datastoreId)
			if (datastoreOb != None):

				lat = 0
				lng = 0

				if (el.getAttributeNode(Constants.recdLat) != None):
					latNode = el.getAttributeNode(Constants.recdLat)
					lat = latNode.nodeValue
				else:
					return

				if (el.getAttributeNode(Constants.recdLng) != None):
					lngNode = el.getAttributeNode(Constants.recdLng)
					lng = lngNode.nodeValue
				else:
					return

				m.addMedia( lat, lng, datastoreOb )


def getMediaFromDatastore( id ):
	mediaObject = None
	try:
		mediaObject = datastore.get( id )
	finally:
		if (mediaObject == None):
			return None

	return mediaObject


def fillRecdFromNode( recd, el ):
	latNode = el.getAttributeNode(Constants.recdLat)
	if (latNode != None):
		recd.latitude = latNode.nodeValue
	lngNode = el.getAttributeNode(Constants.recdLng)
	if (lngNode != None):
		recd.longitude = lngNode.nodeValue

	return recd


def _addRecdXmlAttrs( el, recd ):
	el.setAttribute(Constants.recdDatastoreId, str(recd.datastoreId))
	el.setAttribute(Constants.recdLat, str(recd.latitude))
	el.setAttribute(Constants.recdLng, str(recd.longitude))

def _addInfoXmlAttrs( el, recd ):
	el.setAttribute(Constants.recdInfo, recd[2])
	el.setAttribute(Constants.recdIcon, recd[3])	
	el.setAttribute(Constants.recdLat, str(recd[0]))
	el.setAttribute(Constants.recdLng, str(recd[1]))

def _addLineXmlAttrs( el, recd ):
	el.setAttribute(Constants.lineID, recd[0])
	el.setAttribute(Constants.lineColor, recd[1])
	el.setAttribute(Constants.lineThick, recd[2])
	el.setAttribute(Constants.linePts, recd[3])

def _addSaveXmlAttrs( el, smap ):
	el.setAttribute(Constants.recdLat, str(smap.lat))
	el.setAttribute(Constants.recdLng, str(smap.lng))
	el.setAttribute(Constants.recdZoom, str(smap.zoom))
	el.setAttribute(Constants.recdNotes, str(smap.notes))
	el.setAttribute(Constants.recdTags, smap.tags)
	#el.setAttribute(Constants.recdDensity, str(smap.density))

	if (smap.recdDatastoreId != None):
		el.setAttribute(Constants.recdRecdId, smap.recdDatastoreId)
		el.setAttribute(Constants.recdRecdLat, smap.recdLat)
		el.setAttribute(Constants.recdRecdLng, smap.recdLng)


def saveMediaHash( m ):
	impl = getDOMImplementation()
	album = impl.createDocument(None, Constants.recdAlbum, None)
	root = album.documentElement

	for i in range (0, len(m.recs)):
		recd = m.recs[i]
		mediaEl = album.createElement(Constants.recdMapItem)
		root.appendChild( mediaEl )
		_addRecdXmlAttrs( mediaEl, recd )

	for k, iMarker in m.infoMarkers.iteritems():
		mediaEl = album.createElement(Constants.recdInfoMarker)
		root.appendChild( mediaEl )
		_addInfoXmlAttrs( mediaEl, iMarker.split(";~") )

	for k, iMarker in m.lineData.iteritems():
		mediaEl = album.createElement(Constants.recdLine)
		root.appendChild( mediaEl )
		_addLineXmlAttrs( mediaEl, iMarker.split(";~") )

	for i in range (0, len(m.savedMaps)):
		smap = m.savedMaps[i]
		saveEl = album.createElement(Constants.recdSavedMapItem)
		root.appendChild( saveEl )
		_addSaveXmlAttrs( saveEl, smap )

	return album
