# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    # RAB Information
    rab_ids = fields.One2many(
        'kokai.rab',
        'opportunity_id',
        string='RAB List'
    )
    rab_count = fields.Integer(
        string='RAB Count',
        compute='_compute_rab_count',
        store=True
        
    )
    total_rab_amount = fields.Monetary(
        string='Total RAB Amount',
        compute='_compute_rab_amount',
        currency_field='company_currency'
    )
    approved_rab_amount = fields.Monetary(
        string='Approved RAB Amount',
        compute='_compute_rab_amount',
        currency_field='company_currency'
    )
    has_approved_rab = fields.Boolean(
        string='Has Approved RAB',
        compute='_compute_rab_amount',
        store=True
    )
    
    status_quotation = fields.Char(
        string='Status Quotation'
    )
    
    approved_by = fields.Char(
        string='Approved By'
    )

    # quotation_ids = fields.One2many(
    #     'indo.quotation',
    #     'opportunity_id',
    #     string='Quotation List'
    # )

    # project_id = fields.One2many(
    #     'project.project',
    #     'opportunity_id',
    #     string='Projects'
    # )

    # Line product_id
    # product_id = fields.Many2one(
    #     'product.product',
    #     string='Product',
    #     required=True,
    #     domain=[('purchase_ok', '=', True)],
    #     ondelete='cascade',
    #     index=True,
    #     tracking=True,
    #     store=True
    # )
    
    # project_count = fields.Integer(
    #     string='Project Count',
    #     compute='_compute_project_count',
    #     store=True
    # )
    
    # @api.depends('project_ids')
    # def _compute_project_count(self):
    #     for lead in self:
    #         lead.project_count = len(lead.project_ids)
    
    # def action_view_projects(self):
    #     """View all projects for this opportunity"""
    #     self.ensure_one()
    #     action = self.env["ir.actions.actions"]._for_xml_id("project.open_view_project_all")
    #     action['domain'] = [('opportunity_id', '=', self.id)]
    #     action['context'] = {
    #         'default_opportunity_id': self.id,
    #         'default_partner_id': self.partner_id.id,
    #         'default_name': self.name,
    #     }
    #     return action
    
    # def action_create_project(self):
    #     """Create project from opportunity"""
    #     self.ensure_one()
        
    #     # Check if there's an approved RAB
    #     approved_rab = self.rab_ids.filtered(lambda r: r.state == 'approved')
        
    #     project_vals = {
    #         'name': self.name,
    #         'partner_id': self.partner_id.id,
    #         'opportunity_id': self.id,
    #     }
        
    #     # If there's an approved RAB, use its data
    #     if approved_rab:
    #         rab = approved_rab[0]  # Take first approved RAB
    #         project_vals.update({
    #             'name': f"{self.name} - {rab.name}",
    #             # You can add more fields from RAB if needed
    #         })
        
    #     project = self.env['project.project'].create(project_vals)
        
    #     # Update RABs with the new project
    #     if approved_rab:
    #         approved_rab.write({'project_id': project.id})
        
    #     # Return action to open the project
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'project.project',
    #         'res_id': project.id,
    #         'view_mode': 'form',
    #         'target': 'current',
    #     }

    
    @api.depends('rab_ids')
    def _compute_rab_count(self):
        for lead in self:
            lead.rab_count = len(lead.rab_ids)
    
    @api.depends('rab_ids', 'rab_ids.state', 'rab_ids.total_amount')
    def _compute_rab_amount(self):
        for lead in self:
            all_rabs = lead.rab_ids
            approved_rabs = all_rabs.filtered(lambda r: r.state == 'approved')
            
            lead.total_rab_amount = sum(all_rabs.mapped('total_amount'))
            lead.approved_rab_amount = sum(approved_rabs.mapped('total_amount'))
            lead.has_approved_rab = bool(approved_rabs)
            
            # Update expected revenue if has approved RAB
            if lead.has_approved_rab and not lead.expected_revenue:
                lead.expected_revenue = lead.approved_rab_amount
    
    def action_view_rab(self):
        """Open RAB list view for this opportunity"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("ks_kokai.action_project_rab")
        action['domain'] = [('opportunity_id', '=', self.id)]
        action['context'] = {
            'default_opportunity_id': self.id,
            'default_customer_id': self.partner_id.id,
            'default_project_name': self.name,
        }
        return action
    
    def action_create_rab(self):
        """Create new RAB from opportunity"""
        self.ensure_one()
        
        # Get or create project
        # project = self._get_or_create_project()
        
        default_context = {
            'default_opportunity_id': self.id,
            'default_customer_id': self.partner_id.id if self.partner_id else False,
            'default_partner_id': self.partner_id.id if self.partner_id else False,
            'default_project': self.name,  # Use opportunity name as project name
            'active_model': self._name,
            'active_id': self.id,
            # 'active_field': 'finished_goods',  # field yang akan diupdate                
        }

        return {
            'type': 'ir.actions.act_window',
            'name': _('New RAB - %s') % self.name,
            'res_model': 'kokai.rab',
            'view_mode': 'form',
            'context': default_context,
            'target': 'current',
        }

    
    # def _get_or_create_project(self):
    #     """Get existing project or prepare data for new project"""
    #     self.ensure_one()
        
    #     # Check if project already exists
    #     project = self.env['project.project'].search([
    #         ('opportunity_id', '=', self.id)
    #     ], limit=1)
        
    #     if not project and self.partner_id:
    #         # Prepare project data
    #         project_vals = {
    #             'name': self.name,
    #             'partner_id': self.partner_id.id,
    #             'opportunity_id': self.id,
    #         }
    #         # You might want to create project here or let user create manually
    #         # project = self.env['project.project'].create(project_vals)
        
    #     return project
    
    @api.model
    def create(self, vals):
        """Override to set RAB numbering prefix based on opportunity"""
        lead = super(CrmLead, self).create(vals)
        # Additional logic if needed
        return lead
    
    def write(self, vals):
        """Update related RABs when opportunity changes"""
        res = super(CrmLead, self).write(vals)
        
        # Update customer in related RABs if partner changed
        if 'partner_id' in vals and self.rab_ids:
            self.rab_ids.filtered(lambda r: r.state == 'draft').write({
                'customer_id': vals['partner_id']
            })
        
        return res
    
    def action_approve_quotations(self):
        pass
    
    def action_generate_quotation(self):
        pass