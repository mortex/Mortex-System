from django.db import models

class ShirtStyles(models.Model):
	ShirtStyleNumber = models.CharField('Style Number', max_length=20)
	ShirtStyleDescription = models.CharField('Description', max_length=200)
	def __unicode__(self):
        	return self.ShirtStyleNumber + ' ' + self.ShirtStyleDescription	

class StyleColorCategories(models.Model):
	StyleColorCategoryName = models.CharField('Color Category', max_length=20)

class ShirtStyleSKUs(models.Model):
	ShirtStyle = models.ForeignKey(ShirtStyles)
	StyleColorCategory = models.ForeignKey(StyleColorCategories)
	ShirtStyleSize = models.CharField('Size', max_length=2)
	FabricRollYield = models.IntegerField('Fabric Roll Yield')
	KnitSize = models.FloatField('Knit Size')
	SizePrice = models.FloatField('Size Price')
	Active = models.BooleanField()
	def __unicode__(self):
        	return self.ShirtStyleSize
	
class Customers(models.Model):
	CustomerName = models.CharField('Customer Name', max_length=40)
	def __unicode__(self):
        	return self.CustomerName

class ShirtOrders(models.Model):
	Customer = models.ForeignKey(Customers)
	PONumber = models.CharField('PO#', max_length=20)
	Complete = models.BooleanField()
	def __unicode__(self):
        	return self.PONumber

class ShirtOrderSKUs(models.Model):
	ShirtOrder = models.ForeignKey(ShirtOrders)
	ShirtStyleSKU = models.ForeignKey(ShirtStyleSKUs)
	OrderQuantity = models.IntegerField('Quantity')
	
class Shipments(models.Model):
	DateShipped = models.DateTimeField('Date Shipped')
	
class ShirtSKUInventory(models.Model):
	CutOrder = models.CharField('Cut Order', max_length=20)
	Pieces = models.IntegerField()
	Add = models.BooleanField()

class ShipmentSKUs(models.Model):
	Shipment = models.ForeignKey(Shipments)
	ShirtOrderSKU = models.ForeignKey(ShirtOrderSKUs)
	CutOrder = models.CharField('Cut Order', max_length=20)
