#!/usr/bin/env python
def try_exec(func, *args, **kwargs):
	ret = None
	try:
		ret = func(*args, **kwargs)
	except Exception, e:
		raise e
	else:
		print '%s passed'%func
	return ret
