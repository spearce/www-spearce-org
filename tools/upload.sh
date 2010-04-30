#!/bin/sh

email="$1"
pass="$2"
path="$3"
file="$4"
host="www.spearce.org"

echo >&2 "PUT http://$host$path"
u=$(curl "http://$host/admin/upload_url?user_email=$email&password=$pass")
if [ -z "$u" ]
then
  echo >&2 "fatal: Cannot get upload URL"
  exit 1
fi

curl -q -s \
  -F "path=$path" \
  -F "file=@$file" \
  "$u"
exit $?
