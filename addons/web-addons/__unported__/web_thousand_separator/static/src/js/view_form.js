/**
 * Created by: Trobz - www.trobz.com
 * Date: 21/04/14
 * Time: 5:51 PM
 */


openerp.web_thousand_separator = function (instance) {
	instance.web.form.FieldFloat.include({
	    events: {
	        
	        'change input': 'store_dom_value',
	        'keyup': 'set_thousand_separator',
	    },
	    
	    set_thousand_separator: function(e)
	    {
	    	if (!this.widget)
	    	{
		    	var keyCode = (e.keyCode ? e.keyCode : e.which);
			    if ((keyCode > 47 && keyCode < 58 ) || (keyCode > 95 && keyCode < 106 )) 
			    {
			    	var pos = this.$el.find('input').caret(),
			    		vl = this.$el.find('input').val();
			    		
			    	if (vl)
			    	{
			    		var l10n = _t.database.parameters,
			    			ts_c = this.count_exist(vl, l10n.thousands_sep);
			    			
			    		if (l10n.thousands_sep)
			    			vl = this.replace_all(vl, l10n.thousands_sep, '');
			    			
			    		if (l10n.decimal_point)
			    		{
			    			var nb_arr = vl.split(l10n.decimal_point),
			    				nb = (this.format_value(parseInt(nb_arr[0]), '')).split(l10n.decimal_point)[0];
			    			if (nb_arr.length > 1)
			    				nb += l10n.decimal_point + nb_arr[1];
			    			
			    			if (this.count_exist(nb, l10n.thousands_sep) > ts_c)
			    				pos++;
			    				
			    			this.$el.find('input').val(nb);
			    			this.$el.find('input').caret(pos);
			    			
			    		}
			    	}
			    }
			}
			this.store_dom_value();		  
	    },
	    
	    replace_all: function(vl, find, repl)
	    {
	    	if (!vl)
	    		return vl;
	    	var t = vl;
	    	i = 0
	    	while(t.indexOf(find) >= 0 && i < 100)
	    	{
	    		i++;
	    		t = t.replace(find, repl);
	    	}
	    	return t;
	    },
	    
	    count_exist: function(vl, find)
	    {
	    	if (!vl)
	    		return vl;
	    	var t = vl;
	    	i = 0
	    	while(t.indexOf(find) >= 0 && i < 100)
	    	{
	    		i++;
	    		t = t.replace(find, '');
	    	}
	    	return i;
	    }
	});
}




