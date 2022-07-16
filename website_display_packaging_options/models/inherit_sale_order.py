#  -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2018-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
import logging

from odoo import api, fields, models,tools
from odoo.exceptions import ValidationError, UserError
import base64
import os

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res =  super(SaleOrder,self)._cart_update(product_id=product_id, line_id=line_id,add_qty=add_qty, set_qty=set_qty, **kwargs)
        if self.env['sale.order.line'].sudo().browse([int(res.get('line_id'))]).exists():
            lines = self.env['sale.order.line'].sudo().browse([int(res.get('line_id'))])
            if kwargs.get('kwargs'):
                if lines.product_id.packaging_ids and kwargs.get('kwargs').get('attrib'):
                    lines.write({'product_packaging_id':int(kwargs.get('kwargs').get('attrib'))})
                    lines._onchange_update_product_packaging_qty()
        return res


    @api.model
    def demo_data_product_website(self):
        rec_products=self.env['product.product'].sudo().search([('type','=','product'),('name','ilike','Test Product'),]).filtered(lambda rec:True if len(rec.packaging_ids)>0 else False)

        addons_paths = tools.config['addons_path'].split(',')
        for addons_path in addons_paths:
            try:
                path = os.path.join(addons_path, 'website_display_packaging_options')
            except Exception:
                continue
        for rec_product in rec_products:
            rec_product.website_published=True
            rec_product.website_sequence=1
            rec_product.image_1920 = base64.b64encode(open(os.path.join(path,'data','pack.jpeg'), 'rb').read())
    
        return True




