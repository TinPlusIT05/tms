## Introduction

This module has been created to simplify the implementation of public API,
commonly used by third party company (parnter, customer,...).

It provide some benefits:
- basic helpers to read/create/update/delete object
- 2 log level
  - at the `trobz.api` model level with the `` method.
  - at the request level, with the full XML-RPC HTTP request/response log, in files.
- simplify permission management, just need CRUD permission on `trobz.api` model, that's it.


## __trobz.api__ description


```python
class trobz_api(osv.osv_memory):
    _name = "trobz.api"
    _description = "Trobz API"

    def log_api_call(self,cr,origin_uid,model,action,vals,domain,message,resource_id,status):

    def common_create_update(self, cr, origin_uid,action, obj_name, dict_vals, domain):
        '''
        - obj_name: name of object in OpenERP. Ex: res.partner
        - domain: domain used to search for unique record. Ex: [('name', '=', name)]
        - dict_vals: values of the record need to be created  updated. Ex: {'name': 'name abc', 'reference': '#123' ...}
        '''

    def common_delete(self, cr, origin_uid,action, obj_name, domain):
        '''
        - obj_name: name of object in OpenERP. Ex: res.partner
        - domain: domain used to search for unique record. Ex: [('name', '=', name)]
        '''
```

## create a public API

```python
from openerp import SUPERUSER_ID as SUID

class my_project_api(osv.osv_memory):
    _inherit = "trobz.api"


    def order_pizza(self, cr, origin_uid, data):
        """
        A customer want a pizza !
        """

        pizza_model = self.pool.get('pizza')
        customer_model = self.pool.get('customer')

        # use the SUPERUSER_ID to by-pass security rules
        #   if origin_uid has the permission to call this method, it implicitly mean
        #   that he has the permission to do all these internal stuff...
        pizza_id = pizza_model.search(cr, SUID, [('name', '=', data.get('pizza_name'))])
        if not pizza_id:
            raise Exception("We don't sell %s pizza !" % data.get('pizza_name'))


        order_id = customer_model.order_pizza(cr, SUID, pizza_id)
        message ='wait, you will get your pizza soon !' if order_id else 'sorry, you have to order something else...'

        # add an api log entry
        self.log_api_call(cr, origin_uid, 'pizza.order', 'order_pizza', data, None, message, None, 'pass')

        return message
```

## log HTTP Request/Response at XML-RPC level

Log are automatically handled at a low level based on an `openerp-server.config` custom configuration

```
# specify XML-RPC model you want to log
log_xmlrpc_models=trobz.api,res.users

# path where logs will be stored
log_xmlrpc_path=/path/to/xmlrpc/log
```

The logger will create 1 folder by day, and will generate 1 file by XML-RPC call, with the full Request/Response envelope.

The log file naming convention is: `<timestamp>_<method>_<action>_<model>.log`


for example, in `/path/to/xmlrpc/log/2014-07-11/1405078811731_search_execute_res.users.log`:
```
Request received at 2014-07-11 11-40-11 from IP 127.0.0.1 on path /xmlrpc/object
method: execute
action: search
user id: 1
model: res.users
parameters: [['id', '=', 1]]

--------------- REQUEST -------------
<?xml version='1.0'?>
<methodCall>
<methodName>execute</methodName>
<params>
<param>
<value><string>community70_test</string></value>
</param>
<param>
<value><int>1</int></value>
</param>
<param>
<value><string>admin</string></value>
</param>
<param>
<value><string>res.users</string></value>
</param>
<param>
<value><string>search</string></value>
</param>
<param>
<value><array><data>
<value><array><data>
<value><string>id</string></value>
<value><string>=</string></value>
<value><int>1</int></value>
</data></array></value>
</data></array></value>
</param>
</params>
</methodCall>


--------------- RESPONSE -------------
<?xml version='1.0'?>
<methodResponse>
<params>
<param>
<value><array><data>
<value><int>1</int></value>
</data></array></value>
</param>
</params>
</methodResponse>
```