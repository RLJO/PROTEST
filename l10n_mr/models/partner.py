# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _


class ChartTemplate(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self):
        last_client_code = self.env["account.account"].search([("code", '>=', 410000), ("code", '<', 420000)])
        last_vendor_code = self.env["account.account"].search([("code", '>=', 400000), ("code", '<', 410000)])
        