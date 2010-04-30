_github = 'http://github.com/spearce/'
_urls = {
  '/': '/',
}

def redirect(name):
  if name not in _urls:
    return None

  d = _urls[name]

  if d is None:
    return None

  if d.startswith('http:') or d.startswith('https:'):
    return d

  if d.startswith('/'):
    return _github + d[1:]

  return None
