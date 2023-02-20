#!/usr/bin/python

from djongo import models


class Food(models.Model):
    _id                    = models.ObjectIdField(primary_key=True)
    fdc_id                 = models.PositiveIntegerField(     default=0,  verbose_name="Food Data Central ID")
    nt_hash_id             = models.PositiveIntegerField(     default=0,  verbose_name="Nutritracker hash ID")
    food_name              = models.CharField(max_length=200, default="", verbose_name="Food name")
    serving_size           = models.FloatField(               default=1,  verbose_name="Serving size")
    serving_units          = models.CharField(max_length=30,  default="", verbose_name="Serving units")
    energy_kcal            = models.PositiveSmallIntegerField(default=0,  verbose_name="Energy (kcal)")
    total_fat_g            = models.PositiveSmallIntegerField(default=0,  verbose_name="Total fat (g)")
    saturated_fat_g        = models.PositiveSmallIntegerField(default=0,  verbose_name="Saturated fat (g)")
    trans_fat_g            = models.PositiveSmallIntegerField(default=0,  verbose_name="Trans fat (g)")
    cholesterol_mg         = models.PositiveSmallIntegerField(default=0,  verbose_name="Cholesterol (mg)")
    sodium_mg              = models.PositiveSmallIntegerField(default=0,  verbose_name="Sodium (mg)")
    total_carbohydrates_g  = models.PositiveSmallIntegerField(default=0,  verbose_name="Total carbohydrates (g)")
    dietary_fiber_g        = models.PositiveSmallIntegerField(default=0,  verbose_name="Dietary fiber (g)")
    sugars_g               = models.PositiveSmallIntegerField(default=0,  verbose_name="Sugars (g)")
    protein_g              = models.PositiveSmallIntegerField(default=0,  verbose_name="Protein (g)")
    vitamin_D_mcg          = models.PositiveSmallIntegerField(default=0,  verbose_name="Vitamin D (mcg)")
    potassium_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="Potassium (mg)")
    iron_mg                = models.PositiveSmallIntegerField(default=0,  verbose_name="Iron (mg)")
    calcium_mg             = models.PositiveSmallIntegerField(default=0,  verbose_name="Calcium (mg)")
    vitamin_E_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="Vitamin E (mg)")
    thiamin_B1_mg          = models.PositiveSmallIntegerField(default=0,  verbose_name="Thiamin (vitamin B1) (mg)")
    riboflavin_B2_mg       = models.PositiveSmallIntegerField(default=0,  verbose_name="Riboflavin (vitamin B2) (mg)")
    niacin_B3_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="Niacin (vitamin B3) (mg)")
    folate_B9_mcg          = models.PositiveSmallIntegerField(default=0,  verbose_name="Folate (vitamin B9) (mcg)")
    biotin_B7_mcg          = models.PositiveSmallIntegerField(default=0,  verbose_name="Biotin (vitamin B7) (mcg)")
    pantothenic_acid_B5_mg = models.PositiveSmallIntegerField(default=0,  verbose_name="Pantothenic acid (vitamin B5) (mg)")
    phosphorous_mg         = models.PositiveSmallIntegerField(default=0,  verbose_name="Phosphorus (mg)")
    iodine_mcg             = models.PositiveSmallIntegerField(default=0,  verbose_name="Iodine (mcg)")
    magnesium_mg           = models.PositiveSmallIntegerField(default=0,  verbose_name="Magnesium (mg)")
    zinc_mg                = models.PositiveSmallIntegerField(default=0,  verbose_name="Zinc (mg)")
    copper_mg              = models.PositiveSmallIntegerField(default=0,  verbose_name="Copper (mg)")

    class Meta:
        managed = False
        db_table = 'foods'
        app_label = 'foods'
