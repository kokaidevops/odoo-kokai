from odoo import _, api, fields, models

class HRDepartment(models.Model):
    _inherit = 'hr.department'

    user_ids = fields.One2many('res.users', 'department_id', string='Users')

    def action_show_users(self):
        self.ensure_one()
        if len(self.user_ids) == 0:
            return

        action = self.env.ref('base.action_res_users').sudo().read()[0]
        action['domain'] = [('id', 'in', self.user_ids.ids)]
        return action


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # def _sync_user(self, user, employee_has_image=False):
    #     res = super()._sync_user(user, employee_has_image)
    #     res['department_id'] = user.department_id.id
    #     return res