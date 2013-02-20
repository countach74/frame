{
	{%- for key, value in model.structure.items() -%}
		"{{key}}": "{{value}}",
	{%- endfor -%}
}
