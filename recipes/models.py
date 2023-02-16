#!/usr/bin/python

from bson.objectid import ObjectId

from djongo import models

# Create your models here.


class serializable:
    def serialize(self):
        serialization = dict()
        for column in self.__columns__:
            column_value = getattr(self, column)
            if isinstance(column_value, bytes):
                column_value = codecs.decode(column_value)
            elif isinstance(column_value, ObjectId):
                column_value = str(column_value)
            elif hasattr(column_value, 'serialize'):
                column_value = column_value.serialize()
            elif isinstance(column_value, list):
                if not len(column_value):
                    column_value = []
                elif isinstance(column_value[0], dict):
                    column_value = [value_subd.copy() for value_subd in column_value]
                else:
                    column_value = column_value.copy()
            elif isinstance(column_value, dict):
                column_value = column_value.copy()
            serialization[column] = column_value
        return serialization


class Food(models.Model, serializable):
    __columns__ = ('_id', 'fdc_id', 'food_name', 'serving_size', 'serving_units', 'energy_kcal', 'total_fat_g',
                   'saturated_fat_g', 'trans_fat_g', 'cholesterol_mg', 'sodium_mg', 'total_carbohydrates_g',
                   'dietary_fiber_g', 'sugars_g', 'protein_g', 'vitamin_D_mcg', 'potassium_mg', 'iron_mg', 'calcium_mg',
                   'vitamin_E_mg', 'thiamin_B1_mg', 'riboflavin_B2_mg', 'niacin_B3_mg', 'folate_B9_mcg',
                   'biotin_B7_mcg', 'pantothenic_acid_B5_mg', 'phosphorous_mg', 'iodine_mcg', 'magnesium_mg', 'zinc_mg',
                   'copper_mg')

    _id                    = models.ObjectIdField(primary_key=True)
    fdc_id                 = models.PositiveIntegerField(     default=0,  verbose_name="Food Data Central ID")
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
        app_label = 'recipes'


class Ingredient(models.Model, serializable):
    __columns__ = '_id', 'servings_number', 'food'

    _id                    = models.ObjectIdField(primary_key=True)
    servings_number        = models.FloatField(               default=0,  verbose_name="Servings number")
    food                   = models.EmbeddedField(model_container=Food,   verbose_name="Food")

    class Meta:
        managed = False
        db_table = 'ingredients'
        app_label = 'recipes'


class Recipe(models.Model, serializable):
    __columns__ = '_id', 'owner', 'recipe_name', 'complete', 'ingredients'

    _id                    = models.ObjectIdField(primary_key=True)
    owner                  = models.CharField(max_length=32, default="", verbose_name="Username")
    recipe_name            = models.CharField(max_length=200, default="", verbose_name="Recipe name")
    complete               = models.BooleanField(default=True, verbose_name="Recipe has been completed")
    ingredients            = models.ArrayField(model_container=Ingredient, verbose_name="Recipe ingredients")

    class Meta:
        managed = False
        db_table = 'recipes'
        app_label = 'recipes'

