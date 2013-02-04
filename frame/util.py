from cgi import parse_qs


def parse_query_string(string):
	data = parse_qs(string)
	for key, value in data.items():
		if len(value) == 1:
			data[key] = value[0]

	return data
