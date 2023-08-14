# Part of Odoo. See LICENSE file for full co
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import math
import os
import configparser
import sys

class PriceAnalysis(models.Model):

    _name = 'price.analysis'
    _description = "Analyse the price, cost and margin for the products"

    channel = fields.Many2one('crm.team', store= False)
    sku = fields.Many2one('product.product', store= False)
    size = fields.Char(readonly = True, store = False)
    units = fields.Integer(store = False, default=1)
    size_text = fields.Char(readonly = True, store = False)
    p_weight = fields.Float(store = False)
    p_length = fields.Float(store = False)
    p_width  = fields.Float(store = False)
    p_height = fields.Float(store = False)
    volume = fields.Float(store = False, readonly = True)
    import_cost = fields.Float(store = False, readonly = True)
    item_cost = fields.Float(store = False)
    labor = fields.Float(store = False, readonly = True)
    over_head = fields.Float(store = False, readonly = True)
    amazon_storage_fee = fields.Float(store = False, readonly = True)
    amazon_fba_weight_handling = fields.Float(store = False, readonly = True)
    amazon_comission = fields.Float(store = False, readonly = True)
    price = fields.Float(store = False)
    total_cost = fields.Float(store = False, readonly = True)
    profit = fields.Float(store = False, readonly = True)
    margin = fields.Float(store = False, readonly = True)
    dimensional_weight = fields.Float(store = False, readonly = True)
    variation = fields.Float(store = False)
    is_fba = fields.Boolean(store = False)
    tacos = fields.Float(store = False)
    amazon_fba_outbound_shiping_weight = fields.Float(store = False, readonly = True)
    clasification = fields.Selection([('local',"LOCAL"), ('cross_border', 'CROSS BORDER')], store= False)
    country = fields.Selection([('US',"US"), ('UK', 'UK'), ('DE', 'DE'), ('ES', 'ES'), ('IT', 'IT'), ('FR', 'FR')], store= False)

    SMALL = 'small'
    STANDARD = 'standard'
    SMALL_OVERSIZE = 'small_oversize'
    OVERSIZE = 'oversize'
    MEDIUM_OVERSIZE = 'medium_oversize'
    LARGE_OVERSIZE = 'large_oversize'
    SMALL_TEXT = 'Small'
    STANDARD_TEXT = 'Standard'
    OVERSIZE_TEXT = 'Oversize'
    SMALL_OVERSIZE_TEXT = 'Small Oversize'
    MEDIUM_OVERSIZE_TEXT = 'Medium Oversize'
    LARGE_OVERSIZE_TEXT = 'Large Oversize'
    EU_WEIGHT = {
        'small':[150, 400, 900, 1400, 1900, 3900],
        'standard':[150, 400, 900, 1400, 1900, 2900, 3900, 5900, 8900, 9900, 11900],
        'small_oversize':[760, 1260, 1760, 17609999],
        'oversize':[760, 1760, 2760, 3760, 4760, 9760, 14760, 19760, 24760, 29760, 297609999],
        'large_oversize':[4760, 9760, 14760, 19760, 24760, 31500, 315009999],
    }
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__))+'/values_eu_amazon.cfg')

    @api.onchange('sku','channel', 'country')
    def _set_sku_values(self):
        try:
            multipli = 2.205
            channel_id = self.channel.id
            sku_id = self.sku.id
            if channel_id and sku_id :
                self.p_weight = self.sku.weight * multipli
                self.p_length = self.sku.wk_length
                self.p_width = self.sku.width
                self.p_height = self.sku.height
                self.price = self.sku.list_price
                obj_product_supplier = self.sku.variant_seller_ids.filtered(lambda r: r.product_id.id == self.sku.id)
                if obj_product_supplier:
                    self.item_cost = obj_product_supplier[0].price
                else:
                    self.item_cost = self.sku.standard_price
                self._calculate_size()
            else:
                self.p_weight = 0
                self.p_length = 0
                self.p_width =  0
                self.p_height = 0
                self.volume = 0
                self.price = 0
                self.item_cost = 0
        except Exception as e:
            self.p_weight = 0
            self.p_length = 0
            self.p_width =  0
            self.p_height = 0
            self.price = 0
            self.item_cost = 0
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


    def _calculate_size(self):
        try:
            if self.sku.id and self.channel.id:
                self.is_fba = True if self.channel.name in ['Amazon', 'Amazon EU', 'Amazon UK', 'Amazon CA'] else False
                if self.country == "US":
                    if ((self.p_length > 154.4) | (self.p_width > 76.2) | (self.p_weight > 70)) | (((self.p_width + self.p_height)* 2 + self.p_length ) > 330.2):
                        self.size = self.MEDIUM_OVERSIZE
                        self.size_text = self.MEDIUM_OVERSIZE_TEXT
                    elif(self.p_length > 45.71) | (self.p_width > 35.55) | (self.p_height > 20.31) | (self.p_weight > 20):
                        self.size = self.OVERSIZE
                        self.size_text = self.OVERSIZE_TEXT
                    else:
                        self.size = self.STANDARD
                        self.size_text = self.STANDARD_TEXT
                else:
                    if ((self.p_length <= 35) & (self.p_width <= 25) & (self.p_weight <= 12)) :
                        self.size = self.SMALL
                        self.size_text = self.SMALL_TEXT
                    elif((self.p_length <= 45) & (self.p_width <= 34) & (self.p_height <= 26)):
                        self.size = self.STANDARD
                        self.size_text = self.STANDARD_TEXT
                    elif((self.p_length <= 61) & (self.p_width <= 46) & (self.p_height <= 46)):
                        self.size = self.SMALL_OVERSIZE
                        self.size_text = self.SMALL_OVERSIZE_TEXT
                    elif((self.p_length <= 120) & (self.p_width <= 60) & (self.p_height <= 60)):
                        self.size = self.OVERSIZE
                        self.size_text = self.OVERSIZE_TEXT
                    else:
                        self.size = self.LARGE_OVERSIZE
                        self.size_text = self.LARGE_OVERSIZE_TEXT
                if self.country:
                    self._volume_set()
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


    @api.onchange('variation', 'item_cost', 'price', 'p_weight', 'p_length', 'p_width', 'p_height')
    def _recalculate(self):
        self._calculate_size()

    def _volume_set(self):
        self.volume = self.p_length* self.p_width* self.p_height
        try:
            self._dimensional_weight_set()
            self._amazon_fba_outbound_shiping_weight_set()
            self._import_cost_set()
            self._labor_set()
            self._overhead_set()
            self._amazon_storage_fee_set()
            self._amazon_fba_weight_handling_set()
            self._amazon_comission_set()
            self._total_cost_set()
            self._profit_set()
            self._margin_set()
            self._tacos_set()
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


    def _amazon_fba_outbound_shiping_weight_set(self):
        try:
            if self.country == "US":
                if self.size == self.STANDARD:
                    # if self.p_weight <= 1:
                    #     self.amazon_fba_outbound_shiping_weight = self.p_weight
                    if self.p_weight > self.dimensional_weight:
                        self.amazon_fba_outbound_shiping_weight = self.p_weight
                    else:
                        self.amazon_fba_outbound_shiping_weight = self.dimensional_weight
                    decimal = self.amazon_fba_outbound_shiping_weight - int(self.amazon_fba_outbound_shiping_weight)
                    if decimal >= 0.5:
                        self.amazon_fba_outbound_shiping_weight = int(self.amazon_fba_outbound_shiping_weight) + 1
                    else: 
                        self.amazon_fba_outbound_shiping_weight = int(self.amazon_fba_outbound_shiping_weight) + 0.5
                else:
                    if self.p_weight > self.dimensional_weight:
                        self.amazon_fba_outbound_shiping_weight = math.ceil(self.p_weight)
                    else:
                        self.amazon_fba_outbound_shiping_weight = math.ceil(self.dimensional_weight)
            else:
                selected_weight_value = self.volume/ 5000 if self.volume/ 5000 >= self.p_weight else self.p_weight
                self.amazon_fba_outbound_shiping_weight = self._get_the_value_by_country_weight(selected_weight_value) / 1000
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)


    def _dimensional_weight_set(self):
        if self.country == 'US':
            self.dimensional_weight = self.p_length* 0.39 * self.p_width* 0.39 * self.p_height * 0.39 / 139
        else:    
            self.dimensional_weight = self.p_length* self.p_width* self.p_height / 5000
    
    def _import_cost_set(self):
        if self.is_fba:
            self.import_cost = self.volume * 0.000135
        else:
            self.import_cost = self.volume * 0.0001834 * self.units
    
    def _labor_set(self):
        if self.is_fba:
            self.labor = self.price * 0.0422
        else:
            self.labor = self.price * 0.0491
    
    def _overhead_set(self):
        if self.is_fba:
            self.over_head = self.price * 0.0035
        else:
            self.over_head = self.price * 0.0084
    
    def _amazon_storage_fee_set(self):
        if self.is_fba:
            if self.size == self.STANDARD:
                # self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 1.2225) * 2 #nuevo 2022
                self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 1.2525) * 2 #actuall 2023
            else:
                # self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 0.6975) * 2 #nuevo 2022
                self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 0.77) * 2#actuall 2023
        else:
            if self.size == self.STANDARD:
                # self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 1.2225) * 2 #nuevo 2022
                self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 1.1625) * 2 * self.units#actuall 2021
            else:
                # self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 0.6975) * 2 #nuevo 2022
                self.amazon_storage_fee = (((self.volume * 0.0610237)/ 1728) * 0.66) * 2 * self.units#actuall 2021
            
    
    def _amazon_fba_weight_handling_set(self):
        if self.country == "US":
            if self.is_fba:
                if self.size == self.SMALL:
                    if self.amazon_fba_outbound_shiping_weight <= 0.25:
                        self.amazon_fba_weight_handling = 3.22
                    elif self.amazon_fba_outbound_shiping_weight > 0.25 and self.amazon_fba_outbound_shiping_weight <= 0.5:
                        self.amazon_fba_weight_handling = 3.40
                    elif self.amazon_fba_outbound_shiping_weight > 0.5 and self.amazon_fba_outbound_shiping_weight <= 0.75:
                        self.amazon_fba_weight_handling = 3.58
                    elif self.amazon_fba_outbound_shiping_weight > 0.75 and self.amazon_fba_outbound_shiping_weight <= 1:
                        self.amazon_fba_weight_handling = 3.77
                elif self.size == self.STANDARD:
                    if self.amazon_fba_outbound_shiping_weight <= 0.25:
                        self.amazon_fba_weight_handling = 3.86
                    elif self.amazon_fba_outbound_shiping_weight > 0.25 and self.amazon_fba_outbound_shiping_weight <= 0.5:
                        self.amazon_fba_weight_handling = 4.08
                    elif self.amazon_fba_outbound_shiping_weight > 0.5 and self.amazon_fba_outbound_shiping_weight <= 0.75:
                        self.amazon_fba_weight_handling = 4.24
                    elif self.amazon_fba_outbound_shiping_weight > 0.75 and self.amazon_fba_outbound_shiping_weight <= 1:
                        self.amazon_fba_weight_handling = 4.75
                    elif self.amazon_fba_outbound_shiping_weight > 1 and self.amazon_fba_outbound_shiping_weight <= 1.5:
                        self.amazon_fba_weight_handling = 5.40
                    elif self.amazon_fba_outbound_shiping_weight > 1.5 and self.amazon_fba_outbound_shiping_weight <= 2:
                        self.amazon_fba_weight_handling = 5.69
                    elif self.amazon_fba_outbound_shiping_weight > 2 and self.amazon_fba_outbound_shiping_weight <= 2.5:
                        self.amazon_fba_weight_handling = 6.10
                    elif self.amazon_fba_outbound_shiping_weight > 2.5 and self.amazon_fba_outbound_shiping_weight <= 3:
                        self.amazon_fba_weight_handling = 6.39
                    elif self.amazon_fba_outbound_shiping_weight > 3 and self.amazon_fba_outbound_shiping_weight <= 20:
                        self.amazon_fba_weight_handling = (((self.amazon_fba_outbound_shiping_weight - 3) * 0.16) * 2) + 7.17
                elif self.size == self.OVERSIZE:
                    if self.amazon_fba_outbound_shiping_weight <= 70:
                        self.amazon_fba_weight_handling = (((self.amazon_fba_outbound_shiping_weight - 1) * 0.42) *2) + 9.73
                elif self.size == self.MEDIUM_OVERSIZE:
                    if self.amazon_fba_outbound_shiping_weight <= 150:
                        self.amazon_fba_weight_handling = (((self.amazon_fba_outbound_shiping_weight - 1) * 0.42) * 2) + 19.05
                elif self.size == self.LARGE_OVERSIZE:
                    if self.amazon_fba_outbound_shiping_weight <= 150:
                        self.amazon_fba_weight_handling = (((self.amazon_fba_outbound_shiping_weight - 90) * 0.83) * 2) + 89.98
            else:
                const_fee  = 0.38
                if self.size == self.STANDARD:
                    if self.units <= 1:
                        if self.amazon_fba_outbound_shiping_weight <= 1:
                            self.amazon_fba_weight_handling = 6.2 * self.units
                        else:
                            self.amazon_fba_weight_handling = 6.39 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                    elif self.units <= 2:
                        if self.amazon_fba_outbound_shiping_weight <= 1:
                            self.amazon_fba_weight_handling = 4.3 * self.units
                        else:
                            self.amazon_fba_weight_handling = 4.35 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                    elif self.units <= 3:
                        if self.amazon_fba_outbound_shiping_weight <= 1:
                            self.amazon_fba_weight_handling = 3.75 * self.units
                        else:
                            self.amazon_fba_weight_handling = 3.8 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                    elif self.units <= 4:
                        if self.amazon_fba_outbound_shiping_weight <= 1:
                            self.amazon_fba_weight_handling = 3.19 * self.units
                        else:
                            self.amazon_fba_weight_handling = 3.35 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                    else:
                        if self.amazon_fba_outbound_shiping_weight <= 1:
                            self.amazon_fba_weight_handling = 2.79 * self.units
                        else:
                            self.amazon_fba_weight_handling = 2.85 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                elif self.size == self.OVERSIZE:
                    if self.amazon_fba_outbound_shiping_weight <= 30:
                        if self.units <= 1:
                            self.amazon_fba_weight_handling = 12.9 * self.units * 0.29
                        elif self.units <= 2:
                            self.amazon_fba_weight_handling = 7.48 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                        elif self.units <= 3:
                            self.amazon_fba_weight_handling = 6.38 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                        elif self.units <= 4:
                            self.amazon_fba_weight_handling = 5.28 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                        elif self.units <= 4:
                            self.amazon_fba_weight_handling = 5.28 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                        else:
                            self.amazon_fba_weight_handling = 4.18 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                    else:
                        self.amazon_fba_weight_handling = 20.59 + ((self.amazon_fba_outbound_shiping_weight - 2) * const_fee) * self.units
                elif self.size == self.MEDIUM_OVERSIZE:
                    self.amazon_fba_weight_handling = 16.85 + ((self.amazon_fba_outbound_shiping_weight - 2) * 0.43) * self.units
                else:
                    self.amazon_fba_weight_handling = 0
        else:
            value_weight = self._get_the_value_by_country_weight(int(self.amazon_fba_outbound_shiping_weight))
            try:
                amazon_fba_weight_handling = float(self.config[self.country][self.size+"_"+str(value_weight)])
                if str(self.size+"_"+str(value_weight)).find('9999') != -1:
                    if self.size == self.SMALL_OVERSIZE:
                        self.amazon_fba_weight_handling = amazon_fba_weight_handling + ((self.p_weight * 100 - 1760) * 0.01)
                    elif self.size == self.OVERSIZE:
                        self.amazon_fba_weight_handling = amazon_fba_weight_handling + ((self.p_weight * 100 - 29760) * 0.01)
                    elif self.size == self.LARGE_OVERSIZE:
                        self.amazon_fba_weight_handling = amazon_fba_weight_handling + ((self.p_weight * 100 - 31500) * 0.01)
                else:
                    self.amazon_fba_weight_handling = self.config[self.country][self.size+"_"+str(value_weight)]
            except Exception as e:
                print(e,'es')
                pass

    def _amazon_comission_set(self):
        if self.is_fba:
            comission = 0.15
            if self.country == "US":
                if self.price <= 200:
                    self.amazon_comission = float(self.price) * comission
                else:
                    self.amazon_comission = ((self.price - 200) * 0.1) + 200 * comission
            elif self.country == "CA":
                comission += 0.07
                if self.price <= 200:
                    self.amazon_comission = self.price * comission
                else:
                    self.amazon_comission = ((self.price - 200) * 0.1) + 200 * comission
            else:
                if self.country in ["FR", "IT"]:
                    comission = comission + 0.0045
                if self.price <= 200:
                    self.amazon_comission = self.price * comission
                else:
                    self.amazon_comission = ((self.price - 200) * 0.1) + 200 * comission
        elif self.channel.name in ['Etsy', 'Etsy Sales']:
            comission_per_order = 0.25
            comission_per_unit = 0.2
            comission = 0.065
            comission_after_tax = 0.03
            self.amazon_comission = comission_per_order + comission_per_unit + comission + comission_after_tax
        else:
            self.amazon_comission = 0

    def _total_cost_set(self):
        self.total_cost = self.variation + self.item_cost  + self.import_cost + self.labor + self.over_head + self.amazon_storage_fee + self.amazon_fba_weight_handling + self.amazon_comission + self.tacos

    def _profit_set(self):
        self.profit = self.price - self.total_cost

    def _margin_set(self):
        try:
            self.margin = (self.profit / self.total_cost) * 100
        except:
            self.margin = 0
    
    def _tacos_set(self):
        self.tacos = self.price * 0.12

    def _get_the_value_by_country_weight(self, selected_weight):
        # print(self, selected_weight)
        try:
            returnd_value = []
            try:
                returnd_value[:] = [x for x in self.EU_WEIGHT[self.size] if x>= int(selected_weight) * 1000]
                if not returnd_value:
                    returnd_value[:] = [x for x in self.EU_WEIGHT[self.size] if x<= int(selected_weight) * 1000]
            except Exception as s:
                try:
                    return 0
                except Exception as falla:
                    print(falla)
            return returnd_value[0]
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
