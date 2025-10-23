from odoo import _, api, fields, models


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    processing_time = fields.Float('Processing Time', default=1)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    assign_multiple_user_ids = fields.Many2many('res.users', help='Select the other users that you want to schedule the activity')
    batch = fields.Char('Batch')
    handle_by = fields.Selection([
        ('all', 'All'),
        ('just_one', 'Just One'),
    ], string='Handle By', required=True, default='all')
    start_date = fields.Date('Start Date', default=fields.Date.today())

    @api.model_create_multi
    def create(self, vals_list):
        """While we assign an activity to multiple users,
        it will create a new record corresponding to the assigned users"""
        batch = self.env['ir.sequence'].next_by_code('assignment.activity')
        res = super(MailActivity, self).create(vals_list)
        res.write({ 'batch': batch })
        record = res.assign_multiple_user_ids
        for rec in record:
            self.create({
                'res_model_id': res.res_model_id[0].id,
                'res_id': res.res_id,
                'activity_type_id': res.activity_type_id[0].id,
                'date_deadline': res.date_deadline,
                'user_id': rec.id,
                'summary': res.summary,
                'batch': batch,
                'handle_by': res.handle_by,
            })
        return res

    @api.onchange('user_id')
    def _onchange_user_id(self):
        """This function used to get the domain of assign_multiple_user_ids """
        res = {'domain': { 'assign_multiple_user_ids': [('id', '!=', self.user_id.id)] }}
        return res

    def action_done(self):
        res = super(MailActivity, self).action_done()
        if self.handle_by == 'just_one':
            query = f"DELETE FROM mail_activity WHERE batch={self.batch} AND res_id={self.res_id.id} AND res_model_id={self.res_model_id.id} AND NOT id={self._origin.id}"
            self.env.cr.execute(query)
        return res