from django.core.exceptions import ValidationError
from django.db import models
import datetime

class Customer(models.Model):
    CustomerName = models.CharField('Customer Name', max_length=40)
    def __unicode__(self):
        return self.CustomerName

class ShirtStyle(models.Model):
    ShirtStyleNumber = models.CharField('Style Number', max_length=20, unique=True)
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
    SortKey = models.IntegerField()
    def __unicode__(self):
        return self.ShirtSizeName
    class Meta:
        ordering = ["SortKey"]    

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
    class Meta:
        ordering = ["ShirtSize"]  

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
    Customer = models.ForeignKey(Customer)
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
    ShippedQuantity = models.IntegerField('Shipped Quantity', default=0)
    def __unicode__(self):
        return str(self.ShirtPrice.ShirtStyle) + " " + str(self.ShirtPrice)
    class Meta:
        ordering = ["ShirtPrice"]  

    def clean(self, *args, **kwargs):

        super(ShirtOrderSKU, self).clean(*args, **kwargs)

        if ShirtOrderSKU.objects.filter(
            ShirtPrice__ShirtStyle=self.ShirtPrice.ShirtStyle,
            ShirtStyleVariation=self.ShirtStyleVariation,
            Color=self.Color,
            ShirtPrice__ShirtSize=self.ShirtPrice.ShirtSize,
            ShirtOrder=self.ShirtOrder
        ).count() > 0:
            raise ValidationError(
                "Each shirt order SKU must have a unique combination of style, style variation, color, size, and order"
            )

    def save(self, *args, **kwargs):
        self.full_clean()	# Django won't validate models automatically on save
        super(ShirtOrderSKU, self).save(*args, **kwargs)

class ShirtSKUTransaction(models.Model):
    Color = models.ForeignKey(Color)
    ShirtPrice = models.ForeignKey(ShirtPrice)
    ShirtStyleVariation = models.ForeignKey(ShirtStyleVariation, null=True, blank=True)
    CutOrder = models.CharField('Cut Order', max_length=20)
    Pieces = models.IntegerField()
    Date = models.DateField(default = datetime.datetime.today())
    def save(self):
        super(ShirtSKUTransaction, self).save()
        try:
            skuinventory = ShirtSKUInventory.objects.get(Color=self.Color, ShirtPrice=self.ShirtPrice, ShirtStyleVariation=self.ShirtStyleVariation, CutOrder=self.CutOrder)
            skuinventory.Inventory += self.Pieces
            skuinventory.save()
        except ShirtSKUInventory.DoesNotExist:
            ShirtSKUInventory(Color=self.Color, ShirtPrice=self.ShirtPrice, ShirtStyleVariation=self.ShirtStyleVariation, Inventory=self.Pieces, CutOrder=self.CutOrder).save()
    
class ShirtSKUInventory(models.Model):
    Color = models.ForeignKey(Color)
    ShirtPrice = models.ForeignKey(ShirtPrice)
    ShirtStyleVariation = models.ForeignKey(ShirtStyleVariation, null=True, blank=True)
    CutOrder = models.CharField('Cut Order', max_length=20)
    Inventory = models.IntegerField()

class Shipment(models.Model):
    CustomerAddress = models.ForeignKey(CustomerAddress)
    DateShipped = models.DateTimeField('Date Shipped', default = datetime.datetime.today())
    TrackingNumber = models.CharField('Tracking Number', max_length=50)

class ShipmentSKU(models.Model):
    Shipment = models.ForeignKey(Shipment)
    ShirtOrderSKU = models.ForeignKey(ShirtOrderSKU)
    CutOrder = models.CharField('Cut Order', max_length=20)
    BoxNumber = models.IntegerField('Box #')
    ShippedQuantity = models.IntegerField('Shipped Quantity')
    #overwrite save method to modify inventory/order fields that calculate total shipment amounts
    def save(self):
        #determine old value and save record
        try:
            oldvalue = ShipmentSKU.objects.get(pk=self.pk).ShippedQuantity
        except ShipmentSKU.DoesNotExist:
            oldvalue = 0
        super(ShipmentSKU, self).save()
        
        #update total on-hand inventory
        changevalue = self.ShippedQuantity - oldvalue
        inventory = ShirtSKUInventory.objects.get(Color=self.ShirtOrderSKU.Color, 
                                                  ShirtPrice=self.ShirtOrderSKU.ShirtPrice, 
                                                  ShirtStyleVariation=self.ShirtOrderSKU.ShirtStyleVariation,
                                                  CutOrder=self.CutOrder)
        inventory.Inventory -= changevalue
        inventory.save()
        
        #update amount shipped for ordersku
        ordersku = ShirtOrderSKU.objects.get(pk=self.ShirtOrderSKU.pk)
        ordersku.ShippedQuantity += changevalue
        ordersku.save()
    #overwrite delete method to modify inventory/order fields that calculate total shipment amounts
    def delete(self):
        #determine old value and delete record
        oldvalue = ShipmentSKU.objects.get(pk=self.pk).ShippedQuantity
        super(ShipmentSKU, self).delete()
        
        #update total on-hand inventory
        inventory = ShirtSKUInventory.objects.get(Color=self.ShirtOrderSKU.Color, 
                                                  ShirtPrice=self.ShirtOrderSKU.ShirtPrice, 
                                                  ShirtStyleVariation=self.ShirtOrderSKU.ShirtStyleVariation,
                                                  CutOrder=self.CutOrder)
        inventory.Inventory += oldvalue
        inventory.save()
        
        #update amount shipped for ordersku
        ordersku = ShirtOrderSKU.objects.get(pk=self.ShirtOrderSKU.pk)
        ordersku.ShippedQuantity -= oldvalue
        ordersku.save()
    class Meta:
        ordering = ["ShirtOrderSKU"]  
