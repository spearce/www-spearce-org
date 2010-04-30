import mimetypes

from google.appengine.ext import blobstore
from google.appengine.ext import db

class UploadedFile(db.Model):
  blob = blobstore.BlobReferenceProperty(required=True)
  content_type = db.StringProperty()
  modified = db.DateTimeProperty()

  @property
  def filename(self):
    n = self.key().name()
    return n[n.rindex('/') + 1:]

  @property
  def guessed_type(self):
    if self.content_type == 'application/octet-stream' \
       or not self.content_type:
      mime_type, unused_parameters = mimetypes.guess_type(self.filename)
      return mime_type or 'text/plain'
    else:
      return self.content_type or 'text/plain'

  def delete(self):
    super(UploadedFile, self).delete()
    self.blob.delete()

class UserInfo(db.Model):
  user = db.UserProperty(auto_current_user_add=True)
  upload_password = db.StringProperty()

