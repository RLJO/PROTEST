from odoo import fields, models, api, _
from datetime import date, datetime, timedelta


class ExitServiceStockWizard(models.TransientModel):
    _name = 'fishing.service.stock.wizard'

    will_invoice = fields.Boolean(string="Invoice", default=False)
    start = fields.Datetime(string="Start", default=lambda self: self._context.get('start'))
    end = fields.Datetime(string="End", default=datetime.now())
    total_duration = fields.Float(string="Duration", readonly=True, compute="_compute_duration")
    unit_price = fields.Float(string="Unit price",
                              default=lambda self: self.env.ref('fishing.product_service_stock').list_price)

    @api.depends('start', 'end')
    def _compute_duration(self):
        if self.start and self.end:
            self.total_duration = (self.end - self.start).seconds / 3600

    @api.onchange('start', 'end')
    def _compute_duration(self):
        if self.start and self.end:
            self.total_duration = (self.end - self.start).seconds / 3600

    def action_exit(self):
        act_id = self._context.get('active_id')
        act_model = self._context.get('active_model')
        value = self.env[act_model]
        quantity_data = value.browse(act_id)
        if not self.will_invoice:
            quantity_data.write({'is_ready_out': True})
            return

        inv_vals = {
            'partner_id': quantity_data.customer_id.id,
            'payment_reference': quantity_data.ref,
            'invoice_date': datetime.today(),
            'move_type': 'out_invoice',
            'state': 'draft',
        }

        inv = self.env['account.move'].create(inv_vals)
        context = {'check_move_validity': False}
        inv_line_vals = {
            'product_id': self.env.ref('fishing.product_service_stock').id,
            'account_id': self.env.ref('l10n_fr.1_pcg_706').id,
            'quantity': quantity_data.qte,
            'move_id': inv.id,
            'price_unit': self.unit_price,
            'price_subtotal': self.unit_price * quantity_data.qte,
            'price_total': self.unit_price * quantity_data.qte,
        }
        self.with_context(context).env['account.move.line'].create(inv_line_vals)
        quantity_data.write({'is_ready_out': True})
