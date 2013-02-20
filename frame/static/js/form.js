define(['jquery'], function($) {

	var form = {};

	form.Validator = function(structure) {
		this.structure = structure;
	};


	form.Validator.prototype = {
		validate: function(el) {
			$.each(this.structure, function(k, v) {
				console.log(k, v);
			});
		}
	};

	return form;
});
