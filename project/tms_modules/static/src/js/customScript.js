(function () {
    'use strict';
    $(document).ready(function() {	
    	
    	// BIND new events (show and hide changelog) for body
    	$('body').on('hideRecord', function(e) {
    		$('tr.record_hidden').addClass('tms_hidden');
    	});
    	
    	$('body').on('showAll', function(e) {
    		$('tr.record_hidden').removeClass('tms_hidden');
    	});

	});
})();