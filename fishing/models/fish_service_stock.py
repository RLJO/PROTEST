from odoo import fields, models, api, _
from datetime import datetime


class ServiceStock(models.Model):
    _name = "fish.service.stock"
    _rec_name = 'ref'

    ref = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: _('New'))
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    stock_id = fields.Many2one('stock.warehouse', 'Stock',
                               default=lambda self: self.env.ref("fishing.main_stock_id"))
    location_id = fields.Many2one('stock.location', 'Location',
                                  default=lambda self: self.env.ref("fishing.temporary_id"))
    product_id = fields.Many2one(comodel_name='product.product', string='Product', required=False)
    category_id = fields.Many2one(comodel_name='product.category', string='Category', required=True)
    qte = fields.Float(string='Quantity', required=True)
    receive_date = fields.Datetime(string='Receive date', required=False, default=datetime.now())
    expected_exit_date = fields.Datetime(string='Expected exit date', required=False)
    exit_date = fields.Datetime(string='Exit date', required=False)
    is_out = fields.Boolean(string='Exit', default=False)
    is_ready_out = fields.Boolean(string='Ready', default=False)

    @api.model
    def create(self, vals):
        if vals.get('ref', _('New')) == _('New'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('fish.service.stock') or _('New')
        result = super(ServiceStock, self).create(vals)

        return result

    def exit_stock(self):
        self.is_out = True
        self.exit_date = datetime.now()

    def exit_stock_ready(self):
        view_id = self.env.ref('fishing.stock_exit_form_view')
        return {
            'name': _('Stock exit'),
            'res_model': 'fishing.service.stock.wizard',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'type': 'ir.actions.act_window',
            'context': {
                'active_model': 'fish.service.stock',
                'active_ids': self.ids,
                'start': self.receive_date
            }
        }

