def escape_html(html):
	html_map = {
		'&': '&amp;',
		'<': '&lt;',
		'>': '&gt;',
	}

	return ''.join(html_map.get(c, c) for c in html)
