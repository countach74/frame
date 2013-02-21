define(['jquery'], function($) {

	var form = {};

	form.Validator = function(structure) {
		this.structure = structure;
	};


	form.Validator.prototype = {
		validate: function(el) {
			console.log(el);
			$.each(this.structure, function(k, v) {
				
			});
		}
	};

	return form;
});