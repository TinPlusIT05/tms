from openerp import http
from openerp.http import request
from openerp.tools import config

from openerp.addons.web.controllers.main import Session
from openerp.addons.web.controllers.main import Database
from openerp.addons.web.controllers.main import module_boot


class Session(Session):

    @http.route('/web/session/get_session_info', type='json', auth="none")
    def get_session_info(self):
        result = super(Session, self).get_session_info()
        result["is_production_instance"] = config.get(
            "is_production_instance", False
        )
        return result