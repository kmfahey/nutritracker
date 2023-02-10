#!/usr/bin/python

from django.db import models

class Food(models.Model):
    fdc_id                 = models.PositiveIntegerField(     default=0,  verbose_name="Food Data Central ID")
    food_name              = models.CharField(max_length=200, default="", verbose_name="food name")
    serving_size           = models.PositiveSmallIntegerField(default=1,  verbose_name="serving size")
    serving_size_alt       = models.PositiveSmallIntegerField(default=1,  verbose_name="serving size (alternate)")
    serving_units          = models.CharField(max_length=30,  default="", verbose_name="serving units")
    energy_kcal            = models.PositiveSmallIntegerField(default=0,  verbose_name="energy (kcal)")
    total_fat_g            = models.PositiveSmallIntegerField(default=0,  verbose_name="total fat (g)")
    saturated_fat_g        = models.PositiveSmallIntegerField(default=0,  verbose_name="saturated fat (g)")
    trans_fat_g            = models.PositiveSmallIntegerField(default=0,  verbose_name="trans fat (g)")
    cholesterol_mg         = models.PositiveSmallIntegerField(default=0,  verbose_name="cholesterol (mg)")
    sodium_mg              = models.PositiveSmallIntegerField(default=0,  verbose_name="sodium (mg)")
    total_carbohydrates_g  = models.PositiveSmallIntegerField(default=0,  verbose_name="total carbohydrates (g)")
    dietary_fiber_g        = models.PositiveSmallIntegerField(default=0,  verbose_name="dietary fiber (g)")
    sugars_g               = models.PositiveSmallIntegerField(default=0,  verbose_name="sugars (g)")
    protein_g              = models.PositiveSmallIntegerField(default=0,  verbose_name="protein (g)")
    vitamin_D_mcg          = models.PositiveSmallIntegerField(default=0,  verbose_name="vitamin D (mcg)")
    potassium_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="potassium (mg)")
    iron_mg                = models.PositiveSmallIntegerField(default=0,  verbose_name="iron (mg)")
    calcium_mg             = models.PositiveSmallIntegerField(default=0,  verbose_name="calcium (mg)")
    vitamin_E_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="vitamin E (mg)")
    thiamin_B1_mg          = models.PositiveSmallIntegerField(default=0,  verbose_name="thiamin (vitamin B1) (mg)")
    riboflavin_B2_mg       = models.PositiveSmallIntegerField(default=0,  verbose_name="riboflavin (vitamin B2) (mg)")
    niacin_B3_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="niacin (vitamin B3) (mg)")
    folate_B9_mcg          = models.PositiveSmallIntegerField(default=0,  verbose_name="folate (vitamin B9) (mcg)")
    biotin_B7_mcg          = models.PositiveSmallIntegerField(default=0,  verbose_name="biotin (vitamin B7) (mcg)")
    pantothenic_acid_B5_mg = models.PositiveSmallIntegerField(default=0,  verbose_name="pantothenic acid (vitamin B5) (mg)")
    phosphorous_mg         = models.PositiveSmallIntegerField(default=0,  verbose_name="phosphorus (mg)")
    iodine_mcg             = models.PositiveSmallIntegerField(default=0,  verbose_name="iodine (mcg)")
    magnesium_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="magnesium (mg)")
    zinc_mg                = models.PositiveSmallIntegerField(default=0,  verbose_name="zinc (mg)")
    copper_mg              = models.PositiveSmallIntegerField(default=0,  verbose_name="copper (mg)")






