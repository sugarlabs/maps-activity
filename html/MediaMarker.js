function MediaMarker(){
return{
	initialize:function(pt, markerServer, markerId, tags, info, icon)
	{this.markerServer=markerServer;
	this.markerId=markerId;
	this.pt=pt;
	this.tags=tags;
	this.info=info;
	if(icon==null){icon="null";}
	this.icon=icon;
	this.iconDiv=null;
	if((this.tags == undefined)||(this.tags==null))
	{this.tags = "";}
	},
	getLatLng:function(){return this.pt;},
	get_position:function(){return this.pt;},
	get_info:function(){return this.info;},
	getMarkerServer:function(){return this.markerServer;},
	getMarkerId:function(){return this.markerId;}
};
}