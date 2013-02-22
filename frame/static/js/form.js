define(['jquery'], function($) {

	var form = {};

	form.Validator = function(structure) {
		this.structure = structure;
	};


	form.Validator.prototype = {
		validate: function(el) {
			var validator = this;
			
			el.submit(function(e) {
				e.preventDefault();
				
				var passwordVerifyFields = [];
				
				$.each(el.find(".frame-form-password-verify input"), function() {
					passwordVerifyFields.push($(this).attr('name'));
				});
				
				var formData = validator.serialize($(this));
				
				$.each(passwordVerifyFields, function(k, v) {
					delete(formData[v]);
				});
				
			});
		},
		
		serialize: function(el) {
			var result = {};
			
			$.each(el.serializeArray(), function(k, v) {
				result[v.name] = v.value;
			});
			
			return result;
		}
	};

	return form;
});