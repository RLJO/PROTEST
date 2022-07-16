# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from datetime import datetime, timedelta
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController
from odoo.addons.website.controllers.main import Website
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo import fields, http
from odoo.http import request
import logging
import json
_logger = logging.getLogger(__name__)


class Website(WebsiteSale):

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        packaging_attribs = False
        if kw.get('attrib'):
            """This route is called when adding a product to cart (no options)."""
            sale_order = request.website.sale_get_order(force_create=True)
            if sale_order.state != 'draft':
                request.session['sale_order_id'] = None
                sale_order = request.website.sale_get_order(force_create=True)

            product_custom_attribute_values = None
            if kw.get('product_custom_attribute_values'):
                product_custom_attribute_values = json_scriptsafe.loads(kw.get('product_custom_attribute_values'))

            no_variant_attribute_values = None
            if kw.get('no_variant_attribute_values'):
                no_variant_attribute_values = json_scriptsafe.loads(kw.get('no_variant_attribute_values'))

            sale_order._cart_update(
                product_id=int(product_id),
                add_qty=add_qty,
                set_qty=int(request.env['product.packaging'].sudo().browse(int(kw.get('attrib'))).qty)*int(add_qty),
                product_custom_attribute_values=product_custom_attribute_values,
                no_variant_attribute_values=no_variant_attribute_values,
                kwargs=kw
            )

            if kw.get('express'):
                return request.redirect("/shop/checkout?express=1")

            return request.redirect("/shop/cart")
        else:
            return super(Website, self).cart_update(product_id, add_qty, set_qty, **kw)

    @http.route()
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True, **kw):
        packaging_attribs = False
        if kw.get('attrib'):
            order = request.website.sale_get_order(force_create=1)
            if order.state != 'draft':
                request.website.sale_reset()
                if kw.get('force_create'):
                    order = request.website.sale_get_order(force_create=1)
                else:
                    return {}

            pcav = kw.get('product_custom_attribute_values')
            nvav = kw.get('no_variant_attribute_values')
            value = order._cart_update(
                product_id=product_id,
                line_id=False,
                add_qty=add_qty,
                set_qty=int(request.env['product.packaging'].sudo().browse(int(kw.get('attrib'))).qty)*int(add_qty),
                product_custom_attribute_values=json_scriptsafe.loads(pcav) if pcav else None,
                no_variant_attribute_values=json_scriptsafe.loads(nvav) if nvav else None,
                kwargs=kw
            )

            if not order.cart_quantity:
                request.website.sale_reset()
                return value

            order = request.website.sale_get_order()
            value['cart_quantity'] = order.cart_quantity

            if not display:
                return value

            value['website_sale.cart_lines'] = request.env['ir.ui.view']._render_template("website_sale.cart_lines", {
                'website_sale_order': order,
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()
            })
            value['website_sale.short_cart_summary'] = request.env['ir.ui.view']._render_template("website_sale.short_cart_summary", {
                'website_sale_order': order,
            })
            return value
        else:
            return super(Website, self).cart_update_json(product_id, line_id, add_qty, set_qty, display, **kw)

class WebsiteSaleStockVariantController(WebsiteSaleVariantController):
    @http.route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
        res = super(WebsiteSaleStockVariantController, self).get_combination_info_website(product_template_id, product_id, combination, add_qty, **kw)
        wk_packaging = request.env['ir.ui.view']._render_template('website_display_packaging_options.wk_product_inherit',values={'product_variant': request.env['product.product'].browse(res['product_id']),})
        res['wk_packaging'] = wk_packaging
        return res 
