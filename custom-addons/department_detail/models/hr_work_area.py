from odoo import _, api, fields, models, tools, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class WorkAreaCategory(models.Model):
    _name = 'work.area.category'
    _description = 'Work Area Category'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Name', index='trigram', required=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    parent_id = fields.Many2one('work.area.category', string='Parent Category', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many('work.area.category', 'parent_id', string='Child Categories')
    area_count = fields.Integer('# Count', compute='_compute_area_count')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name
    
    def _compute_area_count(self):
        read_group_res = self.env['hr.work.area'].read_group([('categ_id', 'child_of', self.ids)], ['categ_id'], ['categ_id'])
        group_data = dict((data['categ_id'][0], data['categ_id_count']) for data in read_group_res)
        for categ in self:
            area_count = 0
            for sub_categ_id in categ.search([('id', 'child_of', categ.ids)]).ids:
                area_count += group_data.get(sub_categ_id, 0)
            categ.area_count = area_count
    
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    def name_get(self):
        if not self.env.context.get('hierarchical_naming', True):
            return [(record.id, record.name) for record in self]
        return super().name_get()

    @api.ondelete(at_uninstall=False)
    def _unlink_except_default_category(self):
        main_category = self.env.ref('department_detail.work_area_category_data_building', raise_if_not_found=False)
        if main_category and main_category in self:
            raise UserError(_("You cannot delete this area category, it is the default generic category."))


class HRWorkArea(models.Model):
    _name = 'hr.work.area'
    _description = 'HR Work Area'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    used_by = fields.Selection([
        ('all', 'All'),
        ('department', 'Department'),
        ('employee', 'Employee'),
    ], string='Used By', default='all', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employee')
    department_ids = fields.Many2many('hr.department', string='Department')

    @tools.ormcache()
    def _get_default_category_id(self):
        # Deletion forbidden (at least through unlink)
        return self.env.ref('department_detail.work_area_category_data_building')

    def _read_group_categ_id(self, categories, domain, order):
        category_ids = self.env.context.get('default_categ_id')
        if not category_ids and self.env.context.get('group_expand'):
            category_ids = categories._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    name = fields.Char('Name', index='trigram', required=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    parent_id = fields.Many2one('hr.work.area', string='Parent Area')
    parent_path = fields.Char(index=True, unaccent=False)
    location_id = fields.Many2one('hr.work.location', string='Location', ondelete='cascade', required=True)
    categ_id = fields.Many2one('work.area.category', string='Area Category', default=_get_default_category_id, change_default=True, group_expand='_read_group_categ_id', required=True)
    child_ids = fields.One2many('hr.work.area', 'parent_id', string='Child Area')
    child_count = fields.Integer('# Count', compute='_compute_child_count')

    def _compute_child_count(self):
        read_group_res = self.env['hr.work.area'].read_group([('parent_id', 'child_of', self.ids)], ['parent_id'], ['parent_id'])
        group_data = dict((data['parent_id'][0], data['parent_id_count']) for data in read_group_res)
        for categ in self:
            child_count = 0
            for sub_parent_id in categ.search([('id', 'child_of', categ.ids)]).ids:
                child_count += group_data.get(sub_parent_id, 0)
            categ.child_count = child_count
    
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive area.'))

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    def name_get(self):
        if not self.env.context.get('hierarchical_naming', True):
            return [(record.id, record.name) for record in self]
        return super().name_get()

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for area in self:
            if area.parent_id:
                location_len = len(area.location_id.name)+3
                area.complete_name = '[%s] %s / %s' % (area.location_id.name, area.parent_id.complete_name[location_len:], area.name)
            else:
                area.complete_name = '[%s] %s' % (area.location_id.name, area.name)

    def action_show_child_ids(self):
        self.ensure_one()
        action = self.env.ref('department_detail.hr_work_area_action').sudo().read()[0]
        action['domain'] = [('parent_id', '=', self.id)]
        return action


class HRWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    area_ids = fields.One2many('hr.work.area', 'location_id', string='Area')
    area_count = fields.Integer('Area Count', compute="_compute_area_count")

    @api.depends('area_ids')
    def _compute_area_count(self):
        for record in self:
            record.area_count = len(record.area_ids)

    def action_show_work_area(self):
        self.ensure_one()
        if self.area_count == 0:
            return
        
        action = self.env.ref('department_detail.hr_work_area_action').sudo().read()[0]
        action['domain'] = [('id', 'in', self.area_ids.ids)]
        return action