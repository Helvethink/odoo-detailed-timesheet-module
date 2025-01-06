# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists, SQL


class TimesheetsAnalysisReporting(models.Model):
    _name = "timesheets.analysis.reporting"
    _inherit = "hr.manager.department.report"
    _description = "Timesheets Analysis Report With Details"
    _auto = False
    _register = True

    name = fields.Char("Description", readonly=True)
    user_id = fields.Many2one("res.users", string="User", readonly=True)
    project_id = fields.Many2one("project.project", string="Project", readonly=True)
    task_id = fields.Many2one("project.task", string="Task", readonly=True)
    task_name = fields.Char("Task Name", readonly=True)
    parent_task_id = fields.Many2one("project.task", string="Parent Task", readonly=True)
    manager_id = fields.Many2one("hr.employee", "Manager", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    department_id = fields.Many2one("hr.department", string="Department", readonly=True)
    currency_id = fields.Many2one('res.currency', string="Currency", readonly=True)
    date = fields.Date("Date", readonly=True)
    amount = fields.Monetary("Amount", currency_field="currency_id", readonly=True)
    unit_amount = fields.Float("Time Spent", readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner", readonly=True)
    milestone_id = fields.Many2one('project.milestone', related='task_id.milestone_id')
    message_partner_ids = fields.Many2many('res.partner', compute='_compute_message_partner_ids',
                                           search='_search_message_partner_ids', readonly=True)
    pay_ref  = fields.Char("Payment ref", readonly=True)
    pay_state = fields.Char("Payment Status", readonly=True)
    invoice_date = fields.Date("Invoice Date", readonly=True)
    invoice_due_date = fields.Date("Due date", readonly=True)
    order_id = fields.Many2one("sale.order", string="Sales Order", readonly=True)
    so_line = fields.Many2one("sale.order.line", string="Sales Order Item", readonly=True)
    timesheet_invoice_type = fields.Selection(TIMESHEET_INVOICE_TYPES, string="Billable Type", readonly=True)
    timesheet_invoice_id = fields.Many2one("account.move", string="Invoice", readonly=True, help="Invoice created from the timesheet")
    timesheet_revenues = fields.Monetary("Timesheet Revenues", currency_field="currency_id", readonly=True, help="Number of hours spent multiplied by the unit price per hour/day.")
    margin = fields.Monetary("Margin", currency_field="currency_id", readonly=True, help="Timesheets revenues minus the costs")
    billable_time = fields.Float("Billable Time", readonly=True, help="Number of hours/days linked to a SOL.")
    non_billable_time = fields.Float("Non-billable Time", readonly=True, help="Number of hours/days not linked to a SOL.")


    @api.depends('project_id.message_partner_ids', 'task_id.message_partner_ids')
    def _compute_message_partner_ids(self):
        for line in self:
            line.message_partner_ids = line.task_id.message_partner_ids | line.project_id.message_partner_ids

    def _search_message_partner_ids(self, operator, value):
        return self.env['account.analytic.line']._search_message_partner_ids(operator, value)

    @property
    def _table_query(self):
        return "%s %s %s" % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        return """
            SELECT
                A.id AS id,
                A.name AS name,
                A.user_id AS user_id,
                A.project_id AS project_id,
                A.task_id AS task_id,
                B.name AS task_name,
                A.parent_task_id AS parent_task_id,
                A.employee_id AS employee_id,
                A.manager_id AS manager_id,
                A.company_id AS company_id,
                A.department_id AS department_id,
                A.currency_id AS currency_id,
                A.date AS date,
                A.amount AS amount,
                A.unit_amount AS unit_amount,
                A.partner_id AS partner_id,
                C.payment_reference as pay_ref,
                C.payment_state as pay_state,
                C.invoice_date as invoice_date,
                C.invoice_date_due as invoice_due_date,
                C.amount_untaxed as timesheet_revenues,
                A.order_id AS order_id,
                A.so_line AS so_line,
                A.timesheet_invoice_type AS timesheet_invoice_type,
                A.timesheet_invoice_id AS timesheet_invoice_id,
                CASE
                    WHEN A.order_id IS NULL OR T.service_type in ('manual', 'milestones')
                    THEN 0
                    WHEN T.invoice_policy = 'order' AND SOL.qty_delivered != 0
                    THEN (SOL.price_subtotal / SOL.qty_delivered) * (A.unit_amount * sol_product_uom.factor / a_product_uom.factor)
                    ELSE A.unit_amount * SOL.price_unit * sol_product_uom.factor / a_product_uom.factor
                END AS timesheet_revenues,
                CASE WHEN A.order_id IS NULL THEN 0 ELSE A.unit_amount END AS billable_time
        """

    @api.model
    def _from(self):
        return """
            FROM account_analytic_line A 
            LEFT JOIN project_task B on A.task_id=B.id 
            LEFT JOIN account_move C on C.id=A.timesheet_invoice_id
            LEFT JOIN sale_order_line SOL ON A.so_line = SOL.id
            LEFT JOIN uom_uom sol_product_uom ON sol_product_uom.id = SOL.product_uom
            INNER JOIN uom_uom a_product_uom ON a_product_uom.id = A.product_uom_id
            LEFT JOIN product_product P ON P.id = SOL.product_id
            LEFT JOIN product_template T ON T.id = P.product_tmpl_id
        """

    @api.model
    def _where(self):
        return "WHERE A.project_id IS NOT NULL"

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(SQL("""CREATE or REPLACE VIEW %s as (%s)""", SQL.identifier(self._table), SQL(self._table_query)))
