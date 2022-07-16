# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    property_stock_transit = fields.Many2one(
        'stock.location', 'Delivery Location',
        domain=[('usage', 'in', ['internal', 'transit']), ('capacity_type', '=', 'model'), ('occupied_order', '=', False)],
        inverse='_set_occupied_order',
    )

    # 注意，只有开启多公司间关联交易，该公司才会有仓库值 warehouse_id，具体查看 inter_company_rules
    # odoo13 已有此方法，本身不用
    # @api.onchange('company_id')
    # def _onchange_company_id(self):
    #     warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company_id.id)], limit=1)
    #     self.warehouse_id = warehouse

    def _set_occupied_order(self):
        for rec in self:
            occupied_order = '%s,%s' % (self._name, rec.id)
            # 找到设置了本so的，清空
            self.env['stock.location'].search([('occupied_order', '=', occupied_order)]).write({
                'occupied_order': None,
            })
            # 如设置了值，则赋值 location
            if rec.property_stock_transit:
                rec.property_stock_transit.occupied_order = '%s,%s' % (self._name, rec.id)

    # done, cancel, unlink 时，清空占用
    def write(self, vals):
        if 'state' in vals:
            if vals['state'] in ('done', 'cancel'):
                vals['property_stock_transit'] = False

        res = super(SaleOrder, self).write(vals)
        return res

    def unlink(self):
        for rec in self:
            occupied_order = '%s,%s' % (rec._name, rec.id)
            # 找到设置了本so的，清空
            self.env['stock.location'].search([('occupied_order', '=', occupied_order)]).update({
                'occupied_order': None,
            })
        return super(SaleOrder, self).unlink()
