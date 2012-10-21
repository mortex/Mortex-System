from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
import datetime

class Customer(models.Model):
    CustomerName = models.CharField('Customer Name', max_length=40, unique=True)
    def __unicode__(self):
        return self.CustomerName

class ShirtStyle(models.Model):

    ShirtStyleNumber = models.CharField('Style Number', max_length=20, unique=True)
    ShirtStyleDescription = models.CharField('Description', max_length=200)
    Customer = models.ForeignKey(Customer, null=True, blank=True)
    KnitStyleName = models.CharField('Knit Style', max_length=10)

    def __unicode__(self):
        return self.ShirtStyleNumber + ' ' + self.ShirtStyleDescription 

    def clean(self, *args, **kwargs):

        super(ShirtStyle, self).clean(*args, **kwargs)

        # Ensure that ShirtStyleNumber is unique not only among ShirtStyles,
        # but among ShirtStyleVariations as well
        if ShirtStyleVariation.objects.filter(
            ShirtStyleNumber=self.ShirtStyleNumber
        ):
            raise ValidationError(
                "ShirtStyle must have ShirtStyleNumber distinct from all ShirtStyleVariations"
            )

    def save(self, *args, **kwargs):
        self.full_clean()	# Django won't validate models automatically on save
        super(ShirtStyle, self).save(*args, **kwargs)

class ShirtStyleVariation(models.Model):

    ShirtStyle = models.ForeignKey(ShirtStyle)
    ShirtStyleNumber = models.CharField('Style Number',
                                        max_length=20,
                                        unique=True)
    Customer = models.ForeignKey(Customer, null=True, blank=True)
    PriceChange = models.DecimalField('Price Change', max_digits=10, decimal_places=2)
    VariationDescription = models.TextField('Variation Description', blank=True)

    def __unicode__(self):
        return self.ShirtStyleNumber + ' ' + self.ShirtStyle.ShirtStyleDescription

    def clean(self, *args, **kwargs):

        super(ShirtStyleVariation, self).clean(*args, **kwargs)

        # Ensure that ShirtStyleNumber is unique not only among
        # ShirtStyleVariations, but among ShirtStyles as well
        if ShirtStyle.objects.filter(ShirtStyleNumber=self.ShirtStyleNumber):
            raise ValidationError(
                "ShirtStyleVariation must have ShirtStyleNumber distinct from all ShirtStyles"
            )

    def save(self, *args, **kwargs):
        self.full_clean()	# Django won't validate models automatically on save
        super(ShirtStyleVariation, self).save(*args, **kwargs)

class ColorCategory(models.Model):
    ColorCategoryName = models.CharField('Color Category', max_length=20, unique=True)
    def __unicode__(self):
        return self.ColorCategoryName

class Color(models.Model):
    ColorCategory = models.ForeignKey(ColorCategory)
    ColorName = models.CharField('Color Name', max_length=20, unique=True)
    BarcodeData = models.CharField('Barcode Data', max_length=10)
    def __unicode__(self):
        return self.ColorName

class ShirtSize(models.Model):
    ShirtSizeName = models.CharField('Size Name', max_length=20, unique=True)
    ShirtSizeAbbr = models.CharField('Size Abbr', max_length=10, unique=True)
    SortKey = models.IntegerField()
    BarcodeData = models.CharField('Barcode Data', max_length=10)
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
    ShirtPrice = models.DecimalField('Size Price', decimal_places=2, max_digits=10)
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
    DueDate = models.DateField('Due Date')
    Complete = models.BooleanField('Shipped Complete')
    def __unicode__(self):
        return self.PONumber

class ShirtOrderSKU(models.Model):
    ShirtOrder = models.ForeignKey(ShirtOrder)
    ShirtPrice = models.ForeignKey(ShirtPrice)
    ShirtStyleVariation = models.ForeignKey(ShirtStyleVariation, null=True, blank=True)
    Color = models.ForeignKey(Color)
    OrderQuantity = models.IntegerField('Quantity')
    Price = models.DecimalField(decimal_places=2, max_digits=10)
    ShippedQuantity = models.IntegerField('Shipped Quantity', default=0)
    def __unicode__(self):
        return str(self.ShirtPrice.ShirtStyle.ShirtStyleNumber) + " " + str(self.Color) + " " + str(self.ShirtPrice.ShirtSize.ShirtSizeAbbr)
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
        ).exclude(pk=self.pk).count() > 0:
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

def updateshipmentsku(changevalue, color, shirtprice, shirtstylevariation, cutorder, pk, shirtorder):
    #update total on-hand inventory
    inventory = ShirtSKUInventory.objects.get(Color=color, 
                                              ShirtPrice=shirtprice, 
                                              ShirtStyleVariation=shirtstylevariation,
                                              CutOrder=cutorder)
    inventory.Inventory -= changevalue
    inventory.save()
    
    #update amount shipped for ordersku
    ordersku = ShirtOrderSKU.objects.get(pk=pk)
    ordersku.ShippedQuantity += changevalue
    ordersku.save()
    
    #check to see if order is complete and mark appropriately
    summedquantities = ShirtOrderSKU.objects.filter(ShirtOrder=shirtorder).aggregate(Sum('OrderQuantity'), Sum('ShippedQuantity'))
    shirtsremaining = summedquantities['OrderQuantity__sum'] - summedquantities['ShippedQuantity__sum']
    if shirtsremaining > 0:
        shirtorder.Complete = False
    else:
        shirtorder.Complete = True
    shirtorder.save()

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
        
        updateshipmentsku(self.ShippedQuantity - oldvalue, self.ShirtOrderSKU.Color, self.ShirtOrderSKU.ShirtPrice, self.ShirtOrderSKU.ShirtStyleVariation, self.CutOrder, self.ShirtOrderSKU.pk, self.ShirtOrderSKU.ShirtOrder)
        
    #overwrite delete method to modify inventory/order fields that calculate total shipment amounts
    def delete(self):
        #determine old value and delete record
        oldvalue = ShipmentSKU.objects.get(pk=self.pk).ShippedQuantity
        super(ShipmentSKU, self).delete()
        
        updateshipmentsku(oldvalue * -1, self.ShirtOrderSKU.Color, self.ShirtOrderSKU.ShirtPrice, self.ShirtOrderSKU.ShirtStyleVariation, self.CutOrder, self.ShirtOrderSKU.pk, self.ShirtOrderSKU.ShirtOrder)
        
    class Meta:
        ordering = ["BoxNumber", "ShirtOrderSKU"]  
