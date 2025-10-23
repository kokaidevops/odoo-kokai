from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PriceQuery(models.Model):
    _name = 'price.query'
    _description = 'Price Query Form'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'date ASC'

    active = fields.Boolean('Active', default=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Request By', readonly=True, default=lambda self: self.env.user, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
    
    name = fields.Char('Name', default='New', readonly=True, tracking=True)
    opportunity_id = fields.Many2one('crm.lead', string='Lead', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', related='opportunity_id.partner_id', tracking=True)
    inquiry_id = fields.Many2one('sale.order', string='Inquiry', tracking=True)
    department_ids = fields.Many2many('hr.department', string='Department', tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True)
    due_date = fields.Date('Due Date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', required=True, readonly=True, default='draft', compute='_compute_state', store=True, tracking=True)
    line_ids = fields.One2many('price.query.line', 'query_id', string='Line', tracking=True)
    note = fields.Text('Note', tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Priority', required=True, default='high')
    has_processed = fields.Boolean('Has Processed', default=False, tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='File Price Query', tracking=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', default=lambda self: self.env.ref('price_query.crm_stage_data_price_query').id)

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('price.query')
        return super(PriceQuery, self).create(vals)

    @api.depends('line_ids.state')
    def _compute_state(self):
        for record in self:
            has_process = record.mapped('line_ids').filtered(lambda line: line.state in ['requested', 'draft'])
            if len(has_process) == 0 and len(record.line_ids) > 0:
                record.action_done()

    def action_draft(self):
        self.ensure_one()
        self.write({ 'state': 'draft' })

    def action_process(self):
        self.ensure_one()
        if len(self.department_ids) == 0:
            raise ValidationError("Select Department First to Process Request Price Query")
        for department in self.department_ids:
            batch = self.env['ir.sequence'].next_by_code('assignment.activity')
            for user in department.user_ids:
                self.env['mail.activity'].create({
                    'res_model_id': self.env.ref('price_query.model_price_query').id,
                    'res_id': self._origin.id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'date_deadline': fields.Date.today(),
                    'user_id': user.id,
                    'summary': 'Please process the following Price Query as soon as possible. Thank You!',
                    'batch': batch,
                    'handle_by': 'all',
                })
        for line in self.line_ids:
            line.action_requested()
        self.write({ 'state': 'process' })

    def action_done(self):
        self.ensure_one()
        batch = self.env['ir.sequence'].next_by_code('assignment.activity')
        self.env['mail.activity'].create({
            'res_model_id': self.env.ref('price_query.model_price_query').id,
            'res_id': self._origin.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'date_deadline': fields.Date.today(),
            'user_id': self.user_id.id,
            'summary': 'Please process the following Price Query as soon as possible. Thank You!',
            'batch': batch,
            'handle_by': 'all',
        })
        self.write({ 'state': 'done' })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel' })

    def process_price_query(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.state not in ['approved', 'potential'] or not line.new_request or line.product_id:
                continue
            line.generate_product()
        self.write({ 'has_processed': True })

    def action_show_line(self):
        self.ensure_one()
        action = self.env.ref('price_query.price_query_line_action').read()[0]
        action['domain'] = [('query_id', '=', self.id)]
        return action


class PriceQueryLine(models.Model):
    _name = 'price.query.line'
    _description = 'Line Order of Price Query Form'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, tracking=True)
    name = fields.Char('Name', compute='_compute_name', store=True)
    query_id = fields.Many2one('price.query', string='Doc Reference', required=True, ondelete='cascade', tracking=True)
    inquiry_id = fields.Many2one('sale.order', string='Project', required=True, related='query_id.inquiry_id', tracking=True)
    line_id = fields.Many2one('sale.order.line', string='Line', tracking=True)
    product_id = fields.Many2one('product.product', string='Product', tracking=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template', required=True, tracking=True, domain="[('detailed_type', '=', 'product')]")
    qty = fields.Float('Qty', default=1.0, required=True, tracking=True)
    uom_id = fields.Many2one('uom.uom', string='UoM', required=True, tracking=True)
    need_price = fields.Boolean('Need Price', default=True, tracking=True)
    price_unit = fields.Float('Price Unit', tracking=True)
    need_sheet = fields.Boolean('Need Drawing Sheet', default=True, tracking=True)
    variant_ids = fields.One2many('line.variant', 'line_id', string='Attributes & Variant', tracking=True)
    specification_ids = fields.One2many('line.specification', 'line_id', string='Specification', tracking=True)
    bom_id = fields.Many2one('mrp.bom', string='BoM')
    bom_line_ids = fields.One2many('mrp.bom.line', 'query_line_id', string='BoM Line')
    reference_ids = fields.One2many('line.reference', 'line_id', string='Reference Price', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('potential', 'Potential'),
        ('refused', 'Refused'),
    ], string='State', required=True, readonly=True, default='draft', tracking=True)
    remark = fields.Char('Remark', tracking=True)
    new_request = fields.Boolean('Is New Request?', default=True, tracking=True)
    description = fields.Text('Description', tracking=True)
    reference_id = fields.Many2one('price.query.line', string='Reference', domain="[('product_id', '=', product_id)]", tracking=True)
    is_won = fields.Boolean('Is Won?', tracking=True)
    stage_id = fields.Many2one('crm.stage', string='Stage', default=lambda self: self.env.ref('price_query.crm_stage_data_price_query').id)
    read_only = fields.Boolean('Read Only')

    @api.depends('product_id', 'query_id', 'inquiry_id')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.product_id.display_name or '[]'} - {record.query_id.inquiry_id.name or '[]'} {record.query_id.inquiry_id.alias or ''}"

    def action_requested(self):
        self.ensure_one()
        self.write({ 'state': 'requested' })

    def action_approved(self):
        self.ensure_one()
        self.write({ 'state': 'approved' })

    def action_potential(self):
        self.ensure_one()
        self.write({ 'state': 'potential' })
        self.product_id.write({ 'potential_product': True })

    def action_refused(self):
        self.ensure_one()
        self.write({ 'state': 'refused' })

    def action_generate(self):
        self.ensure_one()
        self.generate_product()
        self.generate_bom()

    @api.onchange('product_tmpl_id')
    def generate_drawing_datasheet(self):
        self.ensure_one()
        self.write({
            'variant_ids': [(5,0,0)],
            'specification_ids': [(5,0,0)],
        })
        if not self.product_tmpl_id:
            return
        specifications = self.env['manufacturing.type'].search([ ('type', '=', 'product') ])
        self.write({
            'variant_ids': [(0,0,{
                'attribute_id': attribute.attribute_id.id,
            }) for attribute in self.product_tmpl_id.attribute_line_ids],
            'specification_ids': [(0,0,{
                'type_id': specification.id,
            }) for specification in specifications],
        })
    
    def generate_product(self):
        self.ensure_one()
        try:
            ProductProduct = self.env['product.product']
            product = ProductProduct._product_find(self.product_tmpl_id, self.variant_ids)
            if not product:
                product_template_attribute_values = self.env['product.template.attribute.value'].browse()
                for product_attribute_value in self.variant_ids.mapped('value_id'):
                    product_attribute = product_attribute_value.attribute_id
                    existing_attribute_line = (
                        self.product_tmpl_id.attribute_line_ids.filtered(
                            lambda l: l.attribute_id == product_attribute
                        )
                    )
                    product_template_attribute_values |= (
                        existing_attribute_line.product_template_value_ids.filtered(
                            lambda v: v.product_attribute_value_id == product_attribute_value
                        )
                    )
                product = ProductProduct.create({
                    'name': self.product_tmpl_id.name,
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'product_template_attribute_value_ids': [
                        (6, 0, product_template_attribute_values.ids)
                    ],
                })
            self.write({ 'product_id': product.id, 'read_only': True })
        except:
            raise ValidationError("Can't create Product Variant")

    def _prepare_bom_value(self):
        self.ensure_one()
        return {
            'product_resource': 'finish',
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_id': self.product_id.id,
            'type': 'normal',
        }

    def generate_bom(self):
        self.ensure_one()
        val = self._prepare_bom_value()
        bom = self.env['mrp.bom'].create(val)
        self.write({ 'bom_id': bom.id })

    def action_show_bom(self):
        self.ensure_one()
        self._generate_bom()
        action = self.env.ref('mrp.mrp_bom_form_action').read()[0]
        action['domain'] = [('query_line_id', '=', self.id)]
        action['views'] = [(self.env.ref('mrp.mrp_bom_form_view').id, 'form')]
        action['res_id'] = self.bom_id.id
        return action


class LineVariant(models.Model):
    _name = 'line.variant'
    _description = 'Variant of Price Query Line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    line_id = fields.Many2one('price.query.line', string='Line Ref', required=True, ondelete='cascade')
    attribute_id = fields.Many2one('product.attribute', string='Attribute', required=True)
    value_id = fields.Many2one('product.attribute.value', string='Value', domain="[('attribute_id', '=', attribute_id)]")


class LineSpecification(models.Model):
    _name = 'line.specification'
    _description = 'Specification of Price Query Line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    line_id = fields.Many2one('price.query.line', string='Line Ref', ondelete='cascade')
    type_id = fields.Many2one('manufacturing.type', string='Specification')
    value_id = fields.Many2one('manufacturing.type.value', string='Value', domain="[('type_id', '=', type_id)]")


class LineReference(models.Model):
    _name = 'line.reference'
    _description = 'Line Reference'

    line_id = fields.Many2one('price.query.line', string='Line Ref', ondelete='cascade')
    project = fields.Char('Project')
    price_unit = fields.Float('Price Unit')