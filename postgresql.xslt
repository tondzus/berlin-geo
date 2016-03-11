<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	
	<!--  Now put in your preferred elements -->
	<xsl:template match="/Map/Layer/Datasource[Parameter[@name='type' and text()='postgis']]">
	    <xsl:copy>
	        <xsl:apply-templates/>
	            <Parameter name='host'>HOST</Parameter>
	            <Parameter name='user'>USER</Parameter>
	            <Parameter name='password'>PASSWD</Parameter>
	    </xsl:copy>
	</xsl:template>
	
	<!--  Identity transform -->
	<xsl:template match="@*|node()">
	    <xsl:copy>
	        <xsl:apply-templates select="@*|node()"/>
	    </xsl:copy>
	</xsl:template>    

</xsl:stylesheet>
