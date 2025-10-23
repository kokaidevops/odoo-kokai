# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RABCategory(models.Model):
    _name = 'kokai.rab.category'
    _description = 'RAB Category'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    parent_id = fields.Many2one(
        'kokai.rab.category',
        string='Parent Category',
        index=True,
        ondelete='cascade'
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'kokai.rab.category',
        'parent_id',
        string='Child Categories'
    )
    complete_name = fields.Char(
        'Complete Name',
        compute='_compute_complete_name',
        store=True
    )
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (
                    category.parent_id.complete_name, category.name
                )
            else:
                category.complete_name = category.name
    
    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))