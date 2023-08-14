# Part of Odoo. See LICENSE file for full co
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import math
import os
import configparser

class InheritProducts(models.Model):
    _inherit = 'product.template'

    channel_mapp_ids = fields.One2many('ziruma.mapp.channel.prices', inverse_name = 'sku')
    # sku = fields.Many2one('product.product')
    # price = fields.Float()
    
class MapChannelPrices(models.Model):
    _name = 'ziruma.mapp.channel.prices'
    _description = 'Map the channel with the prices'

    
    channel_id = fields.Many2one('crm.team')
    sku = fields.Many2one('product.product')
    price = fields.Float()