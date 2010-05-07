import logging
import datetime
import urllib2

from google.appengine.api import memcache
from google.appengine.api.users import create_login_url
from google.appengine.api.users import get_current_user
from google.appengine.api.users import is_current_user_admin

from google.appengine.ext import blobstore
from google.appengine.ext import webapp

from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

from model import UploadedFile
from model import UserInfo

import urls_git
import urls_www

_hosts = {
  'git.spearce.org': urls_git.redirect,
  'www.spearce.org': urls_www.redirect,
}

def get_user_info():
  u = get_current_user()
  if u is None:
    return None
  else:
    return UserInfo.get_or_insert(key_name='user:%s' % u.email())

def _CreateApplication():
  return webapp.WSGIApplication([
    (r'^/admin/upload$',     UploadForm),
    (r'^/admin/upload_url$', UploadUrlHandler),
    (r'^/admin/store$',      StoreFile),
### (r'^/admin/flush_all$',  FlushAll),
### (r'^/admin/rm_all$',     DeleteAll),

    (r'^(/.*)', RedirectQuery),
  ],
  debug=False)


class RedirectQuery(blobstore_handlers.BlobstoreDownloadHandler):
  def get(self, name):
    h = self.request.host
    name = urllib2.unquote(name)

    # Is this a static redirect in the application code?
    #
    if h in _hosts:
      d = _hosts[h](name)
      if d:
        self.redirect(d)
        return

    # I moved everything off S3.
    #
    if h == 'd.spearce.org':
      h = 'www.spearce.org'

    # This might be an UploadedFile
    #
    f = memcache.get(h + name)
    if f == '':
      self.response.set_status(404)
      self.response.out.write('404 Not Found')
      return

    if f is None:
      f = UploadedFile.get_by_key_name(h + name)
      if f is None:
        memcache.set(h + name, '', time = 24 * 3600)
        self.response.set_status(404)
        self.response.out.write('404 Not Found')
        return

      memcache.set(h + name, f)

    last_mod = f.modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
    expires = f.modified + datetime.timedelta(days=2)

    self.response.headers['Content-Type'] = str(f.guessed_type)
    self.response.headers['Last-Modified'] = last_mod
    self.response.headers['Cache-Control'] = "public, max-age=172800"
    self.response.headers['Expires'] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")

    if self.request.headers.has_key('If-Modified-Since'):
      ims = self.request.headers.get('If-Modified-Since')
      if ims == last_modified_string:
        self.error(304)
        return
      modsince = datetime.datetime.strptime(ims, "%a, %d %b %Y %H:%M:%S %Z")
      if modsince >= f.modified:
        self.error(304)
        return

    self.send_blob(f.blob.key(), str(f.guessed_type))


class DeleteAll(webapp.RequestHandler):
  def get(self):
    if is_current_user_admin():
      for b in blobstore.BlobInfo.all():
        b.delete()

class FlushAll(webapp.RequestHandler):
  def get(self):
    if is_current_user_admin():
      self.response.headers['Content-Type'] = 'text/plain'
      r = self.response.out
      r.write('%r\n' % memcache.get_stats())
      memcache.flush_all()
      r.write('FLUSHED\n')
    else:
      self.redirect(create_login_url('/admin/flush_all'))

class UploadForm(webapp.RequestHandler):
  def get(self):
    if not is_current_user_admin():
      self.redirect(create_login_url('/admin/upload'))
      return

    get_user_info()
    upload_url = blobstore.create_upload_url('/admin/store')
    self.response.out.write("""
<html><body>
<form action="%s" method="POST" enctype="multipart/form-data">
<table border="1">
<tr>
  <th>Path:</th>
  <td><input type="text" name="path" size="100"></td>
</tr>
<tr>
  <th>Content-Type:</th>
  <td><input type="text" name="content_type" size="50"></td>
</tr>
<tr>
  <th>File:</th>
  <td><input type="file" name="blob"></td>
</tr>
</table>
<input type="submit" value="Upload">
</form>
</body></html>
""" % upload_url)

class StoreFile(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    upload = list(self.get_uploads())[0]
    host = self.request.host
    name = self.request.get('path')
    content_type = self.request.get('content_type')

    o = UploadedFile.get_by_key_name(host + name)
    if o:
      o = o.blob.key()

    f = UploadedFile(key_name = host + name,
                     content_type = content_type,
                     blob = upload.key(),
                     modified = datetime.datetime.now())
    f.put()
    memcache.set(f.key().name(), f)

    if o and o != upload.key():
      b = blobstore.BlobInfo.get(o)
      if b:
        b.delete()
    self.redirect('/admin/upload')

class UploadUrlHandler(webapp.RequestHandler):
  def get(self):
    effective_user = None

    claimed_email = self.request.get('user_email')
    if claimed_email:
      claimed_user = UserInfo.get_by_key_name('user:%s' % claimed_email)
      if claimed_user and \
         claimed_user.upload_password and \
         claimed_user.upload_password == self.request.get('password'):
        effective_user = claimed_user

    if effective_user:
      self.response.headers['Content-Type'] = 'text/plain'
      upload_url = blobstore.create_upload_url('/admin/store')
      self.response.out.write(upload_url)
    else:
      self.error(403)


def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  application = _CreateApplication()
  main()
