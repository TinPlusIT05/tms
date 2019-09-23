# -*- encoding: utf-8 -*-
##############################################################################

from openerp.osv import osv
from openerp import SUPERUSER_ID

class trobz_api(osv.osv_memory):
    _name = "trobz.api"
    _description = "Trobz API"    
    
    
    def _check_keys(self, vals,fields_def):
        message = ''
        for field in fields_def:
            if field not in vals:
                message += 'ERROR: The field %s was not found in the input values. ' % (field)
        for val_key in vals:
            if val_key not in fields_def:
                message += 'ERROR: The value key %s is not recognized. ' % (val_key)    
        if message:
            message += 'INFO: list of possible keys: "%s"' % (fields_def.keys())
            
        return message
    
    def _check_mandatory_vals(self,cr,fields_def,vals):
        message = '' 
        for field in fields_def,:
            if field.get('mandatory',False) and not vals[field]:
                message += 'ERROR: Field %s required. ' % field
        return message
    
    def _check_exist_vals(self,cr,model,key_name,key_value):
        '''
            WARNING: This method checks if a record exists only if the key_value is set.
            The objective being to have an appropriate message.
        '''
        result=None
        message=None
        if key_value:
            model_obj = self.pool.get(model)
            record_ids = model_obj.search(cr, SUPERUSER_ID,[(key_name,'=',key_value)])
            if record_ids:
                result= record_ids[0]
            else:
                message='ERROR: Object %s with the key %s set to %s does not match an existing record. ' % (model,key_name,key_value)
        return result, message
    
    def _check_set_relation_vals(self,cr,fields_def,vals):
        message = '' 
        for field in fields_def:
            result = None
            if vals[field]:
                relation_model = fields_def[field].get('relation_model',False)
                if relation_model:
                    result,new_message = self._check_exist_vals(cr,relation_model,fields_def[field]['relation_key'],vals[field])
                    if new_message:
                        message += new_message
                    vals[fields_def[field]['relation_field']]=result
        return vals, message

    
    def log_api_call(self,cr,origin_uid,model,action,vals,domain,message,resource_id,status='fail'):
        vals_log={
                  'uid':origin_uid,
                  'model':model,
                  'action':action,
                  'vals': vals,
                  'domain': domain,
                  'message': message,
                  'resource_id':resource_id,
                  'status': status
                  }
        self.pool.get('trobz.api.log').create(cr,SUPERUSER_ID,vals_log)
    
    
    # COMMON
    def common_create_update(self, cr, origin_uid,action, obj_name, dict_vals, domain): 
        '''
        - obj_name: name of object in OpenERP. Ex: res.partner
        - domain: domain used to seach for unique record. Ex: [('name', '=', name)]
        - dict_vals: values of the record need to be created  updated. Ex: {'name': 'name abc', 'reference': '#123' ...}
        '''
        result = None
        obj_ids = self.pool.get(obj_name).search(cr, SUPERUSER_ID, domain)
        message=None
        if obj_ids:
            self.pool.get(obj_name).write(cr, SUPERUSER_ID, obj_ids, dict_vals)
            result = obj_ids[0]
            message='update'
        else:
            result = self.pool.get(obj_name).create(cr, SUPERUSER_ID, dict_vals)
            message='create'
            
        self.log_api_call(cr, origin_uid, obj_name,action, dict_vals, domain, message, result,'pass')
        return result
    
    def common_delete(self, cr, origin_uid,action, obj_name, domain):
        '''
        - obj_name: name of object in OpenERP. Ex: res.partner
        - domain: domain used to seach for unique record. Ex: [('name', '=', name)]
        '''
        object_ids = self.pool.get(obj_name).search(cr, SUPERUSER_ID, domain)
        result = False
        if object_ids:
            result = self.pool.get(obj_name).unlink(cr, SUPERUSER_ID, object_ids)
            mess = 'Delete %s with' % (obj_name)
            for item in domain:
                mess += " %s = %s," % (item[0], item[2])
            print mess
        else:
            mess = 'Cannot find %s with' % (obj_name)
            for item in domain:
                mess += " %s = %s," % (item[0], item[2])
            print mess
        
        self.log_api_call(cr, origin_uid, obj_name, action, {}, domain, mess, None,'pass')
        return mess, result
    
trobz_api()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





