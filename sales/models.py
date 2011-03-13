from django.db import models
import datetime

class Customer(models.Model):
    CustomerName = models.CharField('Customer Name', max_length=40)
    def __unicode__(self):
        return self.CustomerName

class ShirtStyle(models.Model):
    ShirtStyleNumber = models.CharField('Style Number', max_length=20)
    ShirtStyleDescription = models.CharField('Description', max_length=200)
    Customer = models.ForeignKey(Customer, null=True, blank=True)
    KnitStyleName = models.CharField('Knit Style', max_length=10)
    def __unicode__(self):
        return self.ShirtStyleNumber + ' ' + self.ShirtStyleDescription 

class ShirtStyleVariation(models.Model):
    ShirtStyle = models.ForeignKey(ShirtStyle)
    ShirtStyleNumber = models.CharField('Style Number', max_length=20)
    Customer = models.ForeignKey(Customer, null=True, blank=True)
    PriceChange = models.DecimalField('Price Change', max_digits=10, decimal_places=2)
    VariationDescription = models.TextField('Variation Description')
    def __unicode__(self):
        return self.ShirtStyleNumber + ' ' + self.ShirtStyle.ShirtStyleDescription

class ColorCategory(models.Model):
    ColorCategoryName = models.CharField('Color Category', max_length=20)
    def __unicode__(self):
        return self.ColorCategoryName

class Color(models.Model):
    ColorCategory = models.ForeignKey(ColorCategory)
    ColorName = models.CharField('Color Name', max_length=20)
    def __unicode__(self):
        return self.ColorName

class ShirtSize(models.Model):
    ShirtSizeName = models.CharField('Size Name', max_length=20)
    ShirtSizeAbbr = models.CharField('Size Abbr', max_length=10)
    def __unicode__(self):
        return self.ShirtSizeName

class ShirtPrice(models.Model):
    ShirtStyle = models.ForeignKey(ShirtStyle)
    ColorCategory = models.ForeignKey(ColorCategory)
    ShirtSize = models.ForeignKey(ShirtSize)
    FabricRollYield = models.IntegerField('Fabric Roll Yield', null=True, blank=True)
    KnitSize = models.FloatField('Knit Size', null=True, blank=True)
    ShirtPrice = models.FloatField('Size Price')
    Active = models.BooleanField()
    def __unicode__(self):
        return str(self.ShirtSize) + ' - ' + str(self.ColorCategory)

class ShirtSKU(models.Model):
    ShirtPrice = models.ForeignKey(ShirtPrice)
    Color = models.ForeignKey(Color)
    def __unicode__(self):
        return str(self.Color) + ' - ' + str(self.ShirtPrice)

class CustomerAddress(models.Model):
    Customer = models.ForeignKey(Customer)
    Address1 = models.CharField('Address 1', max_length=40)
    Address2 = models.CharField('Address 2', max_length=40, blank=True)
    City = models.CharField(max_length=20)
    State = models.CharField(max_length=2)
    PostalCode = models.CharField(max_length=10)
    ContactName = models.CharField(max_length=40)
    def __unicode__(self):
        return "%s, %s" % (self.Address1, self.City)

class ShirtOrder(models.Model):
    CustomerAddress = models.ForeignKey(CustomerAddress)
    PONumber = models.CharField('PO#', max_length=20)
    Complete = models.BooleanField()
    def __unicode__(self):
        return self.PONumber

class ShirtOrderSKU(models.Model):
    ShirtOrder = models.ForeignKey(ShirtOrder)
    ShirtPrice = models.ForeignKey(ShirtPrice)
    ShirtStyleVariation = models.ForeignKey(ShirtStyleVariation, null=True, blank=True)
    Color = models.ForeignKey(Color)
    OrderQuantity = models.IntegerField('Quantity')
    Price = models.FloatField()

class ShirtSKUInventory(models.Model):
    Color = models.ForeignKey(Color)
    ShirtPrice = models.ForeignKey(ShirtPrice)
    ShirtStyleVariation = models.ForeignKey(ShirtStyleVariation, null=True, blank=True)
    CutOrder = models.CharField('Cut Order', max_length=20)
    Pieces = models.IntegerField()
    Add = models.BooleanField(default = True)
    Date = models.DateField(default = datetime.datetime.today())

class Shipment(models.Model):
    DateShipped = models.DateTimeField('Date Shipped')
    TrackingNumber = models.CharField('Tracking Number', max_length=50)

class ShipmentSKU(models.Model):
    Shipment = models.ForeignKey(Shipment)
    ShirtOrderSKU = models.ForeignKey(ShirtOrderSKU)
    CutOrder = models.CharField('Cut Order', max_length=20)
