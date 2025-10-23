from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging


_logger = logging.getLogger(__name__)


CODE_CONTRACT = {
    'tender': 'a',
    'service': 'b',
    'retail': 'c',
}


class RequirementLine(models.Model):
    _name = 'requirement.line'
    _description = 'Requirement Line for Customer and Project'

    order_id = fields.Many2one('sale.order', string='Order', required=True, ondelete='cascade')
    department_id = fields.Many2one('hr.department', string='Department')
    description = fields.Text('Description')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, vals):
        lines = super(RequirementLine, self).create(vals)
        for line in lines:
            msg = f"New Requirement `{line.description}` for {line.department_id.name} has been added."
            line.order_id.message_post(body=msg)
        return lines

    def write(self, vals):
        self._log_requirement_tracking(vals)
        return super(RequirementLine, self).write(vals)

    def unlink(self):
        for line in self:
            msg = f"Requirement `{line.description}` for {line.department_id.name} has been deleted."
            line.order_id.message_post(body=msg)
        return super(RequirementLine, self).unlink()

    def _log_requirement_tracking(self, vals):
        for line in self:
            datum = {}
            if 'description' in vals:
                datum.update({'Description': [line.description, vals.get('description')]})
            if datum:
                line.order_id.message_post_with_view('crm_management.track_requirement_ids', values={'line': line, 'datum': datum})


class OrderTermList(models.Model):
    _name = 'order.term.list'
    _description = 'Order Term List'
    _order = "sequence ASC, id DESC"

    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')
    default_value = fields.Char('Default Value')

class SaleOrderTerm(models.Model):
    _name = 'sale.order.term'
    _description = 'Sale Order Term'

    order_id = fields.Many2one('sale.order', string='Order', ondelete='cascade')
    term_id = fields.Many2one('order.term.list', string='Term', required=True, ondelete='cascade')
    description = fields.Char('Description', related='term_id.default_value', readonly=False, store=True)


class SaleOrderReview(models.Model):
    _name = 'sale.order.review'
    _description = 'Sale Order Review'

    order_id = fields.Many2one('sale.order', string='Order', ondelete='cascade')
    department_id = fields.Many2one('hr.department', string='Department')
    note = fields.Char('Note')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manager_id = fields.Many2one('res.users', string='Manager', related='account_executive_id.department_id.manager_id.user_id', copy=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment')
    state = fields.Selection(selection_add=[ ('inquiry', 'Inquiry') ], ondelete={ 'inquiry': 'cascade' })
    inquiry_number = fields.Char('Inquiry Number', tracking=True, copy=True)
    contract_number = fields.Char('Contract Number', tracking=True)
    frk_type = fields.Selection([
        ('a', 'A - Tender'),
        ('b', 'B - Service'),
        ('c', 'C - Marketplace'),
    ], string='FRK Type', default='c', required=True, tracking=True, compute='_compute_frk_type', store=True, copy=True)
    audit = fields.Selection([
        ('audit', 'Audit'),
        ('no_audit', 'No Audit'),
    ], string='Audit', default='no_audit', copy=True)
    scope = fields.Char('Scope', tracking=True, related='opportunity_id.scope', store=True)
    account_executive_id = fields.Many2one('res.users', string='Account Executive', default=lambda self: self.env.user.id, tracking=True, copy=True)

    # Customer Sales Info in FRK
    customer_inquiry_number = fields.Char('Customer Inquiry Number', tracking=True, copy=True)
    customer_po_number = fields.Char('Customer PO Number', tracking=True)
    due_date = fields.Date('Due Date', tracking=True, copy=True)

    # Form Review for FIR and FRK
    source = fields.Selection([
        ('tender', 'Tender'),
        ('service', 'Service'),
        ('retail', 'Retail'),
    ], string='Source', default='retail', related='opportunity_id.source', store=True)
    inquiry_date = fields.Date('Inquiry Date', tracking=True, copy=True)
    contract_date = fields.Date('Contract Date', tracking=True)
    revision = fields.Integer('Rev', default='0', tracking=True, compute='_compute_revision', store=True)

    # Project Requirement
    contract_issue_ids = fields.One2many('contract.issue', 'order_id', string='Contract Issue')
    term_ids = fields.One2many('sale.order.term', 'order_id', string='Term and Conditions', copy=True)
    project_requirement_ids = fields.One2many('requirement.line', 'order_id', string='Requirement', copy=True)
    review_ids = fields.One2many('sale.order.review', 'order_id', string='Review')

    # approvals sheet
    contract_approval_ids = fields.One2many('approval.request', 'order_id', string='Contract Approval')
    contract_approval_count = fields.Integer('Contract Approval Count', compute='_compute_contract_approval_count')

    @api.depends('source')
    def _compute_frk_type(self):
        for record in self:
            record.frk_type = CODE_CONTRACT[record.source] if record.source else 'c'

    @api.depends('contract_approval_ids')
    def _compute_contract_approval_count(self):
        for record in self:
            record.contract_approval_count = len(record.contract_approval_ids)

    @api.depends('contract_issue_ids', 'state', 'contract_issue_ids.state')
    def _compute_revision(self):
        for record in self:
            source_doc = {
                'inquiry': 'inquiry',
                'draft': 'document',
                'sale': 'document',
                'done': 'document',
            }
            record.revision = len([issue.state != 'cancel' and issue.document == source_doc[record.state] for issue in record.contract_issue_ids])

    @api.model_create_multi
    def create(self, vals):
        records = super(SaleOrder, self).create(vals)
        for record in records:
            if record.state == 'inquiry':
                msg = f"A new inquiry, `{record.name}` has been created"
                record.opportunity_id.message_post(body=msg)
        return records

    def generate_quotation(self):
        self.ensure_one()
        quotation_number = self.env['ir.sequence'].sudo().next_by_code('quotation.order')
        if self.state == 'inquiry':
            self.write({ 'name': quotation_number, 'state': 'draft', })
            self.opportunity_id.change_stage( self.env.ref('crm_management.crm_stage_data_quotation').id )

    def confirm_frk(self):
        self.ensure_one()
        confirm_lines = self.mapped('order_line').filtered(lambda line: line.line_state == 'confirm')
        if len(confirm_lines) == 0:
            raise ValidationError("THERE MUST BE AT LEAST ONE CONFIRMED ITEM. PLEASE CHECK AGAIN!!!")
        source = dict(self.opportunity_id._fields['source'].selection).get(self.source)
        action = (
            self.env["confirmation.wizard"].confirm_message(
                _(f"Is the SOURCE ({source}) from Contract correct?"),
                records=self.env["sale.order"].browse(self.id), # One or more records
                title="Confirm",
                method="generate_frk",
                callback_params={"confirm": True}
            )
        )
        if action:
            return action

    def generate_frk(self, confirm=False):
        self.ensure_one()
        if not confirm:
            return
        try:
            analytic_account = self.opportunity_id._generate_analytic_account(self.opportunity_id, self.frk_type)
            code = CODE_CONTRACT[self.source]
            contract_number = self.env['ir.sequence'].sudo().next_by_code(f"contract.review.{code}")
            self.write({
                'name': contract_number,
                'state': 'draft',
                'analytic_account_id': analytic_account.id,
            })

            # versioning sale order
            lines = self.mapped('order_line').filtered(lambda line: line.line_state != 'confirm')
            if len(lines) > 0:
                val = self._preparing_value_versioning_order()
                order = self.copy(val)
                lines.set_versioning_order(order.id)
                order.action_cancel()

            self.action_confirm()
            self.opportunity_id.change_stage( self.env.ref('crm_management.crm_stage_data_sale_order').id )
        except:
            raise ValidationError("Can't set Quotation to FRK. Please contact administrator")

    def _prepare_approval_request(self):
        self.ensure_one()
        category_pr = self.env.company.contract_approval_id
        orderlines_str = "\n".join([f"{line.product_id.name}-{line.product_uom_qty} {line.product_uom.name}," for line in self.order_line])
        vals = {
            'name': 'Request Approval for ' + self.name,
            'order_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"{self.name} [{self.customer_po_number}]\n{orderlines_str}"
        }
        return vals

    def action_show_wizard_generate_product(self):
        self.ensure_one()
        ctx = dict(self.env.context)
        ctx.update({'default_order_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'generate.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('crm_management.generate_product_wizard_view_form').id,
            'context': ctx,
        }

    def generate_approval_request(self):
        self.ensure_one()
        vals = self._prepare_approval_request()
        request = self.env['approval.request'].create(vals)
        request.action_confirm()

    def action_view_approval_request(self):
        if len(self.contract_approval_ids) == 0:
            return
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        action['domain'] = [('id', 'in', self.contract_approval_ids.ids)]
        return action

    def action_view_contract_issue(self):
        if len(self.contract_issue_ids) == 0:
            return
        action = (self.env.ref('crm_management.contract_issue_action').sudo().read()[0])
        action['domain'] = [('id', 'in', self.contract_issue_ids.ids)]
        return action

    def generate_project_requirements(self):
        self.ensure_one()
        departments = self.env['hr.department'].search([ ('include_in_crm', '=', True) ])
        terms = self.env['order.term.list'].search([ ('active', '=', True) ], order='sequence ASC, id DESC')
        self.write({
            'project_requirement_ids': [(0, 0, {
                'order_id': self.id,
                'department_id': department.id,
                'description': '-',
            }) for department in departments],
            'review_ids': [(0, 0, {
                'order_id': self.id,
                'department_id': department.id,
            }) for department in departments],
            'term_ids': [(0, 0, {
                'order_id': self.id,
                'term_id': term.id,
                'description': '',
            }) for term in terms],
        })

    def action_confirm(self):
        self.ensure_one()
        self.write({ 'contract_number': self.name })
        return super(SaleOrder, self).action_confirm()

    def action_approved(self):
        self.ensure_one()
        # TODO notification to user

    def action_need_improvement(self, reason):
        self.ensure_one()
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('sale.model_sale_order').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.account_executive_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'just_one',
        })

    def _get_approval(self):
        self.ensure_one()
        if len(self.contract_approval_ids) == 0:
            raise ValidationError("Please Request Approval first")
        request = self.contract_approval_ids[self.contract_approval_count-1]
        approvers = [{
            'department': self.account_executive_id.department_id.name,
            'name': self.account_executive_id.name,
            'date': request.date_confirmed,
        }]
        for approver in request.approver_ids:
            approvers.append({
                'department': approver.user_id.department_id.name,
                'name': approver.user_id.name,
                'date': approver.date or '',
            })
        return approvers

    def _get_issue(self):
        self.ensure_one()
        issues = []
        index = 0
        for issue in self.contract_issue_ids:
            if len(issue.approval_ids) == 0:
                raise ValidationError("Please Request Approval first")
            request = issue.approval_ids[len(issue.approval_ids)-1]
            issues.append({
                'index': index,
                'purpose': issue.name,
                'date': issue.issue_date,
                'prepared': issue.user_id.name,
                'approved': request.approver_ids[0].user_id.name,
                'approved_date': request.approver_ids[0].date or '',
            })
            index += 1
        return issues

    def send_reminder_to_fill_review(self):
        self.ensure_one()
        for review in self.review_ids:
            self.env['mail.activity'].create({
                'res_model_id': self.env.ref('sale.model_sale_order').id,
                'res_id': self._origin.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': fields.Date.today(),
                'user_id': review.department_id.pic_id.id,
                'summary': 'Please provide Your review of the following Project. Thank You!',
                'batch': self.name,
                'handle_by': 'all',
            })

    def _preparing_value_versioning_order(self):
        self.ensure_one()
        return {
            'order_line': [],
            'name': self.name,
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    ability = fields.Selection([
        ('ready', 'Ready'),
        ('indent', 'Indent'),
        ('no', 'No Quote'),
    ], string='State', default='indent', required=True, copy=True)
    line_state = fields.Selection([
        ('potential', 'Potential'),
        ('confirm', 'Confirm'),
        ('no_quote', 'No Quote'),
        ('lost', 'Lost Order'),
        ('cancel', 'Cancel'),
    ], string='Line State', default='potential', required=True, tracking=True, copy=True)
    drawing_number = fields.Char('Drawing Number', copy=True)

    def action_show_details(self):
        self.ensure_one()
        view = self.env.ref("sale.sale_order_line_view_form_readonly")
        return {
            "name": _("Detailed Line"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "sale.order.line",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "res_id": self.id,
            "context": dict(self.env.context),
        }

    def set_versioning_order(self, oid):
        self.ensure_one()
        query = f"UPDATE sale_order_line SET order_id={oid} WHERE id={self._origin.id}"
        self.env.cr.execute(query)


class SaleOrderLineSpecification(models.Model):
    _name = 'sale.order.line.specification'
    _description = 'Sale Order Line Specification'

    line_id = fields.Many2one('sale.order.line', string='Line', required=True, ondelete='cascade')
    name = fields.Char('Name')
    value = fields.Char('Value')