from django.db import models

class Customer(models.Model):
	CustomerName = models.CharField('Customer Name', max_length=40)
	def __unicode__(self):
        	return self.CustomerName

class ShirtStyle(models.Model):
	ShirtStyleNumber = models.CharField('Style Number', max_length=20)
	ShirtStyleDescription = models.CharField('Description', max_length=200)
	Customer = models.ForeignKey(Customer, null=True)
	KnitStyleName = models.CharField('Knit Style', max_length=10)
	def __unicode__(self):
        	return self.ShirtStyleNumber + ' ' + self.ShirtStyleDescription	

class StyleColorCategory(models.Model):
	StyleColorCategoryName = models.CharField('Color Category', max_length=20)
	def __unicode__(self):
		return self.StyleColorCategoryName

class StyleColor(models.Model):
	StyleColorCategory = models.ForeignKey(StyleColorCategory)
	StyleColorName = models.CharField('Color Name', max_length=20)
	def __unicode__(self):
		return self.StyleColorName

class ShirtStylePrice(models.Model):
	ShirtStyle = models.ForeignKey(ShirtStyle)
	StyleColorCategory = models.ForeignKey(StyleColorCategory)
	ShirtStyleSize = models.CharField('Size', max_length=10)
	FabricRollYield = models.IntegerField('Fabric Roll Yield', null=True, blank=True)
	KnitSize = models.FloatField('Knit Size', null=True, blank=True)
	SizePrice = models.FloatField('Size Price')
	Active = models.BooleanField()
	def __unicode__(self):
        	return self.ShirtStyleSize

class ShirtStyleSKU(models.Model):
	ShirtStylePrice = models.ForeignKey(ShirtStylePrice)
	StyleColor = models.ForeignKey(StyleColor)

class CustomerAddress(models.Model):
	Customer = models.ForeignKey(Customer)
	Address1 = models.CharField('Address 1', max_length=40)
	Address2 = models.CharField('Address 2', max_length=40, blank=True)
	City = models.CharField(max_length=20)
	State = models.CharField(max_length=2)
	PostalCode = models.CharField(max_length=10)
	ContactName = models.CharField(max_length=40)

class ShirtOrder(models.Model):
	CustomerAddress = models.ForeignKey(CustomerAddress)
	PONumber = models.CharField('PO#', max_length=20)
	Complete = models.BooleanField()
	def __unicode__(self):
        	return self.PONumber

class ShirtOrderSKU(models.Model):
	ShirtOrder = models.ForeignKey(ShirtOrder)
	ShirtStyleSKU = models.ForeignKey(ShirtStyleSKU)
	OrderQuantity = models.IntegerField('Quantity')
	Price = models.FloatField()
	CustomLabel = models.BooleanField('Custom Label')
	
class ShirtSKUInventory(models.Model):
	ShirtStyleSKU = models.ForeignKey(ShirtStyleSKU)
	CutOrder = models.CharField('Cut Order', max_length=20)
	Pieces = models.IntegerField()
	Add = models.BooleanField()

class Shipment(models.Model):
	DateShipped = models.DateTimeField('Date Shipped')
	TrackingNumber = models.CharField('Tracking Number', max_length=50)

class ShipmentSKU(models.Model):
	Shipment = models.ForeignKey(Shipment)
	ShirtOrderSKU = models.ForeignKey(ShirtOrderSKU)
	CutOrder = models.CharField('Cut Order', max_length=20)
