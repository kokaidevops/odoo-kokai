from odoo import _, api, fields, models


class BrandAssessmentPoint(models.Model):
    _name = 'brand.assessment.point'
    _description = 'Brand Assessment Point'
    _order = 'sequence ASC, id DESC'

    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)
    name = fields.Char('Name')


class BrandAssessmentLine(models.Model):
    _name = 'brand.assessment.line'
    _description = 'Brand Assessment Line'

    point_id = fields.Many2one('brand.assessment.point', string='Point')
    assessment_id = fields.Many2one('brand.assessment', string='Assessment')
    is_check = fields.Boolean('OK?')


class BrandAssessment(models.Model):
    _name = 'brand.assessment'
    _description = 'Brand Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string='Request By', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    name = fields.Char('Name', default='New')
    brand_id = fields.Many2one('res.brand', string='Brand')
    survey_id = fields.Many2one('survey.survey', string='survey')
    line_ids = fields.One2many('brand.assessment.line', 'assessment_id', string='Line')
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='brand_id.product_categ_id', store=True)
    brand_category = fields.Selection(related='brand_id.category', string='Brand Category', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('evaluate', 'Evaluate'),
        ('request', 'Request'),
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('obsolete', 'Obsolete'),
    ], string='State', default='draft')
    remarks = fields.Text('Remarks')
    category = fields.Selection([
        ('init_eval', 'Initial Evaluation'),
        ('re_eval', 'Re-Evaluation'),
    ], string='Category', default='init_eval')
    date = fields.Date('Submit Date', default=fields.Date.today())
    issue_date = fields.Date('Issue Date')
    expired_date = fields.Date('Expired Date')

    def _generate_survey(self):
        self.ensure_one()

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_evaluate(self):
        self.ensure_one()
        self.write({ 'state': 'evaluate' })

    def action_request(self):
        self.ensure_one()
        self.write({ 'state': 'request' })

    def action_accept(self):
        self.ensure_one()
        self.write({ 'state': 'accept' })

    def action_reject(self):
        self.ensure_one()
        self.write({ 'state': 'reject' })

    def action_obsolete(self):
        self.ensure_one()
        self.write({ 'state': 'obsolete' })


class ResBrand(models.Model):
    _inherit = 'res.brand'

    product_categ_id = fields.Many2one('product.category', string='Product Category')
    category = fields.Selection([
        ('end_supplier', 'End Supplier'),
        ('supply_chain', 'Supply Chain'),
    ], string='Category', default='supply_chain')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('evaluate', 'Evaluate'),
        ('accept', 'Validate'),
        ('reject', 'Blacklist'),
        ('obsolete', 'Obsolete'),
    ], string='State', default='draft', compute='_compute_state', store=True)
    assessment_ids = fields.One2many('brand.assessment', 'brand_id', string='Assessment')
    assessment_count = fields.Integer('Assessment Count', compute='_compute_assessment_count', store=True)
    @api.depends('assessment_ids')
    def _compute_assessment_count(self):
        for record in self:
            record.assessment_count = len(record.assessment_ids)

    @api.depends('assessment_ids', 'assessment_ids.state')
    def _compute_state(self):
        for record in self:
            record.state

    def action_show_assessment(self):
        self.ensure_one()
        if self.assessment_count == 0:
            return
        action = (self.env.ref('brand_assessment.brand_assessment_action').sudo().read()[0])
        action['domain'] = [('id', 'in', self.assessment_ids.ids)]
        return action
