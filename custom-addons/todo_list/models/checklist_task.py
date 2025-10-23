from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    checklist_type_ids = fields.One2many('checklist.type', 'department_id', string='Checklist Type')
    checklist_count = fields.Integer('Checklist Count', compute='_compute_checklist_count')

    @api.depends('checklist_type_ids')
    def _compute_checklist_count(self):
        for record in self:
            record.checklist_count = len(record.checklist_type_ids)

    def action_show_checklist(self):
        self.ensure_one()
        action = self.env.ref('todo_list.checklist_type_action').sudo().read()[0]
        action['domain'] = [('department_id', '=', self.id)]
        action['context'] = {'default_department_id': self.id}
        return action


class ChecklistType(models.Model):
    _name = 'checklist.type'
    _description = 'Checklist Type'

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', string='Module')
    department_id = fields.Many2one('hr.department', string='Department')
    template_ids = fields.One2many('checklist.template', 'type_id', string='Template')
    template_count = fields.Integer('Template Count', )

    @api.depends('template_ids')
    def _compute_template_count(self):
        for record in self:
            record.template_count = len(record.template_ids)

    def action_show_template(self):
        self.ensure_one()
        action = self.env.ref('todo_list.checklist_template_action').sudo().read()[0]
        action['domain'] = [('type_id', '=', self.id)]
        action['context'] = {'default_type_id': self.id}
        return action


class ChecklistTemplate(models.Model):
    _name = 'checklist.template'
    _description = 'Checklist Template'

    name = fields.Char('Name')
    type_id = fields.Many2one('checklist.type', string='Type')
    line_ids = fields.One2many('checklist.line', 'template_id', string='Line')


class ChecklistLine(models.Model):
    _name = 'checklist.line'
    _description = 'Checklist Line'
    _order = 'sequence ASC, id ASC'

    sequence = fields.Integer('Sequence', default=10)
    template_id = fields.Many2one('checklist.template', string='Checklist')
    name = fields.Char('name')
    date = fields.Datetime('Date')
    description = fields.Html('Description')
    result = fields.Char('Result')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete', 'Complete'),
        ('cancel', 'Cancel'),
    ], string='State', default='draft', required=True)
    is_last = fields.Boolean('Is Last', default=True)

    @api.onchange('sequence')
    def _onchange_sequence(self):
        for record in self:
            self.env.cr.execute(f"UPDATE checklist_line SET is_last=False WHERE template_id={record.template_id.id}")
            self.env.cr.execute(f"UPDATE checklist_line SET is_last=True WHERE template_id={record.template_id.id} ORDER BY sequence DESC, id DESC LIMIT 1")

    def action_complete(self):
        self.ensure_one()
        self.write({ 'state': 'complete', 'date': fields.Datetime.now() })

    def action_cancel(self):
        self.ensure_one()
        self.write({ 'state': 'cancel', 'date': fields.Datetime.now() })

    def action_next_checklist(self):
        self.ensure_one()
        next_checklist = self.env['checklist.line'].search([
            ('template_id', '=', self.template_id),
            ('sequence', '>=', self.sequence),
            ('id', '!=', self._origin.id),
        ], limit=1)
        if next_checklist.is_last:
            return
        
        if next_checklist:
            view = self.env.ref("todo_list.checklist_line_view_form")
            return {
                "name": _("Checklist"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "checklist.line",
                "views": [(view.id, "form")],
                "view_id": view.id,
                "target": "new",
                "res_id": next_checklist.id,
                "context": dict(self.env.context),
            }