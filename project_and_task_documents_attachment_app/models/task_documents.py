# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,date
from odoo.exceptions import UserError, ValidationError

class ProjectTaskDocuments(models.Model):
	_inherit="project.task"


	attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')

	def _compute_attachment_number(self):
		attachment_data = self.env['ir.attachment'].read_group([
			('res_model', '=', 'project.task'),
			('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
		attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
		for doc in self:
			doc.attachment_number = attachment.get(doc.id, 0)

	def action_get_attachment_view(self):
		self.ensure_one()
		res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
		res['domain'] = [('res_model', '=', 'project.task'), ('res_id', 'in', self.ids)]
		res['context'] = {'default_res_model': 'project.task', 'default_res_id': self.id}
		return res