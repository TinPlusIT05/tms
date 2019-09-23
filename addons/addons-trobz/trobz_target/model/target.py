# -*- coding: utf-8 -*-


from openerp import fields, models, api
from openerp.exceptions import Warning


class trobz_target(models.Model):
    _name = "target"
    _description = "Target"

    def _generate_order_by(self, order_spec, query):
        my_order =  """
            CAST((
                SELECT name FROM target_type tt
                WHERE tt.id = target.target_type_id
            ) AS VARCHAR) ASC
        """
    
        if order_spec:
            return super(trobz_target, self)._generate_order_by(order_spec, query)
        return " ORDER BY {0}".format(my_order)
    
    
    # Columns
    target_type_id = fields.Many2one(string="Target Type",
                                     comodel_name="target.type",
                                     required=True)
    start_day = fields.Date(string="Date Start",
                            required=True)
    end_day = fields.Date(string="Date End")
    value = fields.Float(string="Value")
    note = fields.Text(string="Note")
    description = fields.Text(string="Description",
                              related="target_type_id.description",
                              readonly=True)

    @api.model
    def create(self, vals):
        '''
        Create a new record of target. 
        Get the start day, end day of those target which are compared with the new ticket
        If the start day or end day in the day of those target (from start to end), Alert the message.
        '''
        start_day = vals['start_day']
        end_day = vals.get('end_day',False)
        type_id = vals['target_type_id']
        
        target_objs = self.search([('target_type_id','=',type_id)])
        if target_objs:
            for target_obj in target_objs:
                if not target_obj.end_day and start_day > target_obj.start_day:
                    raise Warning('Error!','A target of this type is already existed.')
                elif not end_day and start_day < target_obj.start_day or (start_day > target_obj.start_day and start_day < target_obj.end_day):
                    raise Warning('Error!','A target of this type is already existed.')
                elif (start_day >= target_obj.start_day and start_day <= target_obj.end_day) or (end_day >= target_obj.start_day and end_day <= target_obj.end_day):
                    raise Warning('Error!','A target of this type is already existed.')
                elif end_day and start_day > end_day:
                    raise Warning('Error!','Target: The start day must be less than the end day')
        return super(trobz_target,self).create(vals)

    @api.multi
    def write(self, vals):
        for target_obj in self:
            start_day = vals.get('start_day',target_obj.start_day)
            end_day = vals.get('end_day',target_obj.end_day)
            target_objs = self.search([('target_type_id','=',target_obj.target_type_id.id),('id','not in',self._ids)])
            if target_objs:
                for target_obj in target_objs:
                    if not target_obj.end_day and start_day > target_obj.start_day:
                        raise Warning('Error!','A target of this type is already existed.')
                    elif not end_day and start_day < target_obj.start_day or (start_day > target_obj.start_day and start_day < target_obj.end_day):
                        raise Warning('Error!','A target of this type is already existed.')
                    elif (start_day >= target_obj.start_day and start_day <= target_obj.end_day) or (end_day >= target_obj.start_day and end_day <= target_obj.end_day):
                        raise Warning('Error!','A target of this type is already existed.')
                    elif end_day and start_day > end_day:
                        raise Warning('Error!','Target: The start day must be less than the end day')
       
        return super(trobz_target, self).write(vals)
trobz_target()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


