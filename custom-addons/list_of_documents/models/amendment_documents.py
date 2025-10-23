from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AmendmentDocument(models.Model):
    _name = 'amendment.document'
    _description = 'Amendment Document'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'approved_date DESC, id DESC'

    name = fields.Char('Name', default='New')
    document_id = fields.Many2one('list.of.documents', string='Document', required=True)
    requested_date = fields.Date('Requested Date', required=True, default=fields.Date.today())
    requested_by_id = fields.Many2one('res.users', string='Requested By', required=True, default=lambda self: self.env.user.id)
    approved_date = fields.Date('Approved Date', tracking=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By', tracking=True)
    amendment_article = fields.Char('Amendment Article', default='N/A', tracking=True)
    amendment_page = fields.Char('Amendment Page', default='N/A', tracking=True)
    amendment_section = fields.Char('Amendment Section', default='N/A', tracking=True)
    line_ids = fields.One2many('amendment.line', 'amendment_id', string='Content')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Review'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('need_improvement', 'Need Improvement'),
        ('cancel', 'Cancel'),
    ], string='State', required=True, default='draft', tracking=True)
    team_id = fields.Many2one('department.team', string='Team')
    current_edition = fields.Integer('Current Edition', compute='_compute_current_edition', store=True)
    new_edition = fields.Integer('New Edition')

    approval_ids = fields.One2many('approval.request', 'amendment_document_id', string='Approval')
    approval_count = fields.Integer('Approval Count', compute='_compute_approval_count')
    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for record in self:
            record.approval_count = len(record.approval_ids)

    def action_show_approval(self):
        self.ensure_one()
        if self.approval_count == 0:
            return
        action = (self.env.ref('approvals.approval_request_action_all').sudo().read()[0])
        action['domain'] = [('id', 'in', self.approval_ids.ids)]
        return action

    @api.depends('document_id')
    def _compute_current_edition(self):
        for record in self:
            record.current_edition = record.document_id.edition

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('amendment.document')
        return super(AmendmentDocument, self).create(vals) 

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_review(self):
        self.ensure_one()
        batch = self.env['ir.sequence'].next_by_code('assignment.activity')
        for user in self.team_id.member_ids:
            self.env['mail.activity'].create({
                'res_model_id': self.env.ref('list_of_documents.model_amendment_document').id,
                'res_id': self._origin.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': fields.Date.today(),
                'user_id': user.id,
                'summary': 'Please process the following amendment as soon as possible. Thank You!',
                'batch': batch,
                'handle_by': 'just_one',
            })
        self.write({ 'state': 'review' })

    def action_requested(self):
        self.ensure_one()
        category_pr = self.env.company.approval_amendment_id
        approval = self.env['approval.request'].create({
            'name': 'Request Approval for Amendment ' + self.name,
            'amendment_document_id': self.id,
            'request_owner_id': self.env.user.id,
            'category_id': category_pr.id,
            'reason': f"Request Approval for Amendment {self.name} from {self.requested_by_id.name} \n Amendment Document {self.document_id.name} is request Approval. Please review this amendment"
        })
        if approval:
            approval.action_confirm()
        self.write({ 'state': 'requested' })

    def action_approved(self):
        self.ensure_one()
        # TODO needed notification to user?
        self.write({ 'state': 'approved' })

    def action_need_improvement(self, reason):
        self.ensure_one()
        # notification to user
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('list_of_documents.model_amendment_document').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('custom_activity.mail_act_revision').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.requested_by_id.id,
            'summary': reason,
            'batch': self.env['ir.sequence'].next_by_code('assignment.activity'),
            'handle_by': 'all',
        })
        self.write({ 'state': 'need_improvement' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

class AmendmentLine(models.Model):
    _name = 'amendment.line'
    _description = 'Amendment Line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    amendment_id = fields.Many2one('amendment.document', string='Amendment')
    before_amendment = fields.Text('Before Amendment', required=True, tracking=True)
    after_amendment = fields.Text('After Amendment', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('need_improvement', 'Need Improvement'),
        ('cancel', 'Cancel'),
    ], string='State', required=True, default='draft', tracking=True, related='amendment_id.state')