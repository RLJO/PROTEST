from odoo import fields, models
import dateutil.parser
import datetime


class Pr(models.Model):
    _inherit = "hr.employee"

    hours_worked_between_two_dates = fields.Float(
        compute='_compute_hours_worked_between_two_dates', groups="hr_attendance.group_hr_attendance_user")
    hours_worked_between_two_dates_display = fields.Char(
        compute='_compute_hours_worked_between_two_dates', groups="hr_attendance.group_hr_attendance_user")

    def _compute_hours_worked_between_two_dates(self):
        for employee in self:
            payslip = self.env['hr.payslip'].search([
                ('employee_id', '=', employee.id),
            ])
            if payslip:
                payslip = payslip[0]
                date1 = payslip.date_from
                date2 = payslip.date_to
                pr = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    '&',
                    ('check_out', '<=', date2),
                    ('check_in', '>=', date1),
                ])

                hours = 0
                for p in pr:
                    check_in = p.check_in
                    check_out = p.check_out
                    hours += (check_out - check_in).total_seconds() / 3600.0

                employee.hours_worked_between_two_dates = round(hours, 2)
                employee.hours_worked_between_two_dates_display = "%g" % employee.hours_worked_between_two_dates
