# www-spearce-org
#
# Define DATASTORE to the location where 'make serve' should store its
# runtime data files; by default this is /tmp/dev_appserver.datastore.
#
# Define REMOTE=1 to enable remote hosts to connect to the development
# web server started by 'make serve'.  This may be a security risk.
#
# Define EMAIL=1 to enable sending email messages during 'make serve'.
# This may spam invalid addresses, so it is off by default.
#
# Define APPID to the unique Google App Engine application instance
# 'make update' will upload the application files to.
#
# Define DEV_APPSERVER to the location of dev_appserver.py from the
# Google App Engine SDK download.
#
# Define APPCFG to the location of appcfg.py from the Google App
# Engine SDK download.
#

ifeq ($(shell uname),Darwin)
	DEV_APPSERVER := python2.5 /usr/local/bin/dev_appserver.py
else
	DEV_APPSERVER := dev_appserver.py
endif

APPID   = www-spearce-org
APPCFG  = appcfg.py
CPIO    = cpio -pd

-include config.mak

ifdef DATASTORE
	WEB_ARG += --datastore_path=$(DATASTORE)
endif
ifeq (1,$(REMOTE))
	WEB_ARG += --address 0.0.0.0
endif
ifeq (1,$(EMAIL))
	WEB_ARG += --enable_sendmail
endif

R_WEB      := release/web

WEB_INCLUDE := $(strip \
	app.yaml \
	index.yaml \
	model.py \
	redirect.py \
	static \
	urls_git.py \
	urls_www.py \
)

## Top level targets
##

all: web
release: release-web

clean:
	@rm -rf release *.pyc

## Web application
##

web:

serve: web
	$(DEV_APPSERVER) $(WEB_ARG) .

release-web: web
	@echo Building www-spearce-org `./GIT-VERSION-GEN`  for $(APPID):
	@rm -rf $(R_WEB)
	@mkdir -p $(R_WEB)
	@echo "  Copying loose files" && \
	 find $(WEB_INCLUDE) -print | $(CPIO) $(abspath $(R_WEB))
	@./GIT-VERSION-GEN >$(R_WEB)/static/application_version
	@perl -pi -e 's/(application:).*/$$1 $(APPID)/' $(R_WEB)/app.yaml
	@echo $(R_WEB) built for $(APPID).

update: release-web
	$(APPCFG) update $(R_WEB)

version:
	@printf '%s = ' '$(APPID)'
	@curl http://$(APPID).appspot.com/application_version
