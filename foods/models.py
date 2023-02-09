#!/usr/bin/python

from django.db import models

class Food(models.Model):
    foodDataCentralID  = models.PositiveIntegerField(     default=0,  verbose_name="Food Data Central ID")
    foodName           = models.CharField(max_length=200, default="", verbose_name="food name")
    servingSize        = models.PositiveSmallIntegerField(default=1,  verbose_name="serving size")
    servingUnits       = models.CharField(max_length=30,  default="", verbose_name="serving units")
    calories           = models.PositiveSmallIntegerField(default=0,  verbose_name="calories")
    totalFat           = models.PositiveSmallIntegerField(default=0,  verbose_name="total fat")
    saturatedFat       = models.PositiveSmallIntegerField(default=0,  verbose_name="saturated fat")
    transFat           = models.PositiveSmallIntegerField(default=0,  verbose_name="trans fat")
    cholesterol        = models.PositiveSmallIntegerField(default=0,  verbose_name="cholesterol")
    sodium             = models.PositiveSmallIntegerField(default=0,  verbose_name="sodium")
    totalCarbohydrates = models.PositiveSmallIntegerField(default=0,  verbose_name="total carbohydrates")
    dietaryFiber       = models.PositiveSmallIntegerField(default=0,  verbose_name="dietary fiber")
    sugars             = models.PositiveSmallIntegerField(default=0,  verbose_name="sugars")
    protein            = models.PositiveSmallIntegerField(default=0,  verbose_name="protein")
    vitaminD           = models.PositiveSmallIntegerField(default=0,  verbose_name="vitamin D")
    potassium          = models.PositiveSmallIntegerField(default=0,  verbose_name="potassium")
    iron               = models.PositiveSmallIntegerField(default=0,  verbose_name="iron")
    calcium            = models.PositiveSmallIntegerField(default=0,  verbose_name="calcium")
    vitaminE           = models.PositiveSmallIntegerField(default=0,  verbose_name="vitamin E")
    thiaminB1          = models.PositiveSmallIntegerField(default=0,  verbose_name="thiamin (vitamin B1)")
    riboflavin         = models.PositiveSmallIntegerField(default=0,  verbose_name="riboflavin (vitamin B2)")
    niacinB6           = models.PositiveSmallIntegerField(default=0,  verbose_name="niacin (vitamin B6)")
    folate             = models.PositiveSmallIntegerField(default=0,  verbose_name="folate")
    biotin             = models.PositiveSmallIntegerField(default=0,  verbose_name="biotin")
    pantothenicAcid    = models.PositiveSmallIntegerField(default=0,  verbose_name="pantothenicAcid")
    phosphorous        = models.PositiveSmallIntegerField(default=0,  verbose_name="phosphorus")
    iodine             = models.PositiveSmallIntegerField(default=0,  verbose_name="iodine")
    magnesium          = models.PositiveSmallIntegerField(default=0,  verbose_name="magnesium")
    zinc               = models.PositiveSmallIntegerField(default=0,  verbose_name="zinc")
    copper             = models.PositiveSmallIntegerField(default=0,  verbose_name="copper")






