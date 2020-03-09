Name:           zuul
Version:        3.19.0
Release:        1%{?dist}
Summary:        Trunk Gating System

License:        ASL 2.0
URL:            https://zuul-ci.org
Source0:        %pypi_source

Source2:        zuul-scheduler.service
Source3:        zuul-merger.service
Source4:        zuul-executor.service
Source5:        zuul-web.service
Source6:        zuul-fingergw.service
Source7:        README.fedora
Source8:        zuul.conf
Source9:        logging.conf

Patch01:        0001-Remove-another-shebang-and-remove-useless-exec-bits.patch
Patch02:        0001-requirements-add-explicit-reference-to-dateutil.patch

BuildArch:      noarch


#Error:
# Problem: conflicting requests

# https://src.fedoraproject.org/rpms/python-virtualenv/pull-request/20
#  - nothing provides ((python3.8dist(virtualenv) < 20 or python3.8dist(virtualenv) > 20) with (python3.8dist(virtualenv) < 20.0.1 or python3.8dist(virtualenv) > 20.0.1) with python3.8dist(virtualenv) > 20) needed by zuul-3.19.0-1.fc33.noarch

# https://github.com/cherrypy/cheroot/issues/263 # the zuul cap reason
# The proposed fix https://github.com/cherrypy/cheroot/pull/277
# https://bugzilla.redhat.com/show_bug.cgi?id=1834207
#  - nothing provides python3.8dist(cheroot) < 8.1 needed by zuul-3.19.0-1.fc33.noarch

#  - nothing provides python3.8dist(cherrypy) = 18.3 needed by zuul-3.19.0-1.fc33.noarch


BuildRequires:  python3-devel
BuildRequires:  python3-pbr
BuildRequires:  python3-setuptools
BuildRequires:  python3-zuul-sphinx
BuildRequires:  python3-snowballstemmer
BuildRequires:  python3-fixtures
BuildRequires:  python3-sphinx-autodoc-typehints
BuildRequires:  python3-sphinxcontrib-blockdiag
BuildRequires:  python3-sphinxcontrib-programoutput
BuildRequires:  python3-sphinxcontrib-openapi
BuildRequires:  python3-reno
BuildRequires:  python3-CacheControl
BuildRequires:  python3-jwt
BuildRequires:  python3-github3py
BuildRequires:  python3-pyyaml
BuildRequires:  python3-paramiko
BuildRequires:  python3-GitPython
BuildRequires:  python3-daemon
BuildRequires:  python3-extras
BuildRequires:  python3-statsd
BuildRequires:  python3-voluptuous
BuildRequires:  python3-gear
BuildRequires:  python3-APScheduler
BuildRequires:  python3-prettytable
BuildRequires:  python3-babel
BuildRequires:  python3-kazoo
BuildRequires:  python3-sqlalchemy
BuildRequires:  python3-alembic
BuildRequires:  python3-cryptography
BuildRequires:  python3-cherrypy
BuildRequires:  python3-ws4py
BuildRequires:  python3-routes
BuildRequires:  python3-netaddr
BuildRequires:  python3-paho-mqtt
BuildRequires:  python3-psutil
BuildRequires:  python3-fb-re2
BuildRequires:  python3-cachetools
BuildRequires:  python3-jsonpath-rw
BuildRequires:  python3-dateutil
BuildRequires:  python3-iso8601
BuildRequires:  python3-PyMySQL
BuildRequires:  python3-psycopg2
BuildRequires:  python3-pathspec
# BuildRequires:  python3-graphene
BuildRequires:  systemd
BuildRequires:  ansible


%description
Zuul is a program that drives continuous integration, delivery,
and deployment systems with a focus on project gating and
interrelated projects.


%package webui
Summary: The Zuul web interface

%description webui
This package provides the Zuul web interface source code.
Please refers to README.fedora for build and deployment instruction.

%package scheduler
Summary: The Zuul scheduler service
Requires: %{name} = %{?epoch:%{epoch}:}%{version}-%{release}

%description scheduler
The main Zuul process. Handles receiving events, executing jobs,
collecting results and posting reports. Coordinates the work of
the other components. It also provides a gearman daemon which
the other components use for coordination.


%package merger
Summary: The Zuul merger service
Requires: %{name} = %{?epoch:%{epoch}:}%{version}-%{release}

%description merger
Scale-out component that performs git merge operations.
Zuul performs a large number of git operations in the course of
its work. Adding merger processes can help speed Zuul’s processing.
This component is optional (zero or more of these can be run).


%package web
Requires: %{name} = %{?epoch:%{epoch}:}%{version}-%{release}
Summary: The Zuul web service

%description web
A web server that receives “web-hook” events from external providers,
supplies a web dashboard, and provides web-socket access to live
streaming of logs.


%package executor
Summary: The Zuul executor service
Requires: %{name} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires: git-core
Requires: bubblewrap
# zuul-manage-ansible requires them to create ansible virtualenvs
## Requires: python3-virtualenv
Requires: gcc
Requires: python3-devel

%description executor
Scale-out component for executing jobs. At least one of these is
required. Depending on system configuration, you can expect a single
executor to handle up to about 100 simultaneous jobs. Can handle
the functions of a merger if dedicated mergers are not provided.
One or more of these must be run.


%package fingergw
Summary: Executor finger gateway service
Requires: %{name} = %{?epoch:%{epoch}:}%{version}-%{release}

%description fingergw
A gateway which provides finger protocol access to live streaming of logs.

%package migrate
Summary: Migrate zuul v2 and Jenkins Job Builder to Zuul v3
Requires: %{name} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires: bubblewrap

%description migrate
Migrate zuul v2 and Jenkins Job Builder to Zuul v3

%package doc
Summary: Zuul documentation

%description doc
The Zuul HTML documentation


%prep
%autosetup -n zuul-%{version} -p1
sed -i '/^importlib-resources.*/d' requirements.txt
# remove extra uneeded shebangs in zuul_return
# archive on pypi do not preserve links
# could be removed at next release
find zuul/ansible/ -type f -name "zuul_return.py" \
    -exec sed -i '/\/usr\/bin\/python/d' {} \;

# Inject package version
cat << EOF > zuul/version.py
is_release = True
release_string = "%{version}-%{release}"
class version_info:
    def release_string():
        return release_string
EOF
# Fix non compliant shebangs
/usr/bin/pathfix.py -i %{python3} -p -n -k zuul/ansible
install -m 0644 %{SOURCE7} README.fedora
# Fix wrong-file-end-of-line-encoding
sed -i 's/\r$//' LICENSE

%build
%py3_build

# Create fake zuul clients suitable for sphinx programoutput
cp zuul/cmd/client.py build/zuul
sed -i '1i \#!/usr/bin/env python3' build/zuul
chmod +x build/zuul
cp zuul/cmd/manage_ansible.py build/zuul-manage-ansible
sed -i '1i \#!/usr/bin/env python3' build/zuul-manage-ansible
chmod +x build/zuul-manage-ansible
# Generate documentation (without release note because source doesn't have git log)
sed -e 's/^ *releasenotes$//' -i doc/source/reference/index.rst
rm doc/source/reference/releasenotes.rst
PYTHONPATH=../../build/lib PATH=$PATH:$(pwd)/build PBR_VERSION=%{version} SPHINX_DEBUG=1 sphinx-build-3 \
    -b html doc/source build/html
# Remove empty stub files
find build -type f -name "*.pyi" -size 0 -delete
# rm doc build leftovers
rm -Rf build/html/.buildinfo build/html/.doctrees

%install
install -p -d -m 0755 %{buildroot}/%{_datadir}/zuul-ui
mv web/* %{buildroot}/%{_datadir}/zuul-ui/
%py3_install
rm -Rf %{buildroot}%{python3_sitelib}/zuul/web/static
install -p -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/zuul-scheduler.service
install -p -D -m 0644 %{SOURCE3} %{buildroot}%{_unitdir}/zuul-merger.service
install -p -D -m 0644 %{SOURCE4} %{buildroot}%{_unitdir}/zuul-executor.service
install -p -D -m 0644 %{SOURCE5} %{buildroot}%{_unitdir}/zuul-web.service
install -p -D -m 0644 %{SOURCE6} %{buildroot}%{_unitdir}/zuul-fingergw.service
install -p -D -m 0640 %{SOURCE8} %{buildroot}%{_sysconfdir}/zuul/zuul.conf
install -p -D -m 0640 %{SOURCE9} %{buildroot}%{_sysconfdir}/zuul/logging.conf
install -p -d -m 0700 %{buildroot}%{_sharedstatedir}/zuul
install -p -d -m 0700 %{buildroot}%{_localstatedir}/log/zuul

# Prepare lib directory
install -p -d -m 0700 %{buildroot}%{_sharedstatedir}/zuul/.ssh
install -p -d -m 0755 %{buildroot}%{_sharedstatedir}/zuul/ansible
install -p -d -m 0755 %{buildroot}%{_sharedstatedir}/zuul/executor
install -p -d -m 0755 %{buildroot}%{_sharedstatedir}/zuul/git
install -p -d -m 0700 %{buildroot}%{_sharedstatedir}/zuul/keys


%pre
getent group zuul >/dev/null || groupadd -r zuul
if ! getent passwd zuul >/dev/null; then
  useradd -r -g zuul -G zuul -d %{_sharedstatedir}/zuul -s /sbin/nologin -c "Zuul Daemon" zuul
fi
exit 0


%post scheduler
%systemd_post zuul-scheduler.service
%post merger
%systemd_post zuul-merger.service
%post web
%systemd_post zuul-web.service
%post executor
%systemd_post zuul-executor.service
%post fingergw
%systemd_post zuul-fingergw.service


%preun scheduler
%systemd_preun zuul-scheduler.service
%preun merger
%systemd_preun zuul-merger.service
%preun web
%systemd_preun zuul-web.service
%preun executor
%systemd_preun zuul-executor.service
%preun fingergw
%systemd_preun zuul-fingergw.service


%files
%license LICENSE
%config(noreplace) %attr(0640,zuul,zuul) %{_sysconfdir}/zuul/zuul.conf
%config(noreplace) %attr(0644,zuul,zuul) %{_sysconfdir}/zuul/logging.conf
%dir %attr(0755,zuul,zuul) %{_sharedstatedir}/zuul
%dir %attr(0755,zuul,zuul) %{_sharedstatedir}/zuul/.ssh
%dir %attr(0755,zuul,zuul) %{_sharedstatedir}/zuul/ansible
%dir %attr(0755,zuul,zuul) %{_sharedstatedir}/zuul/keys
%dir %attr(0755,zuul,zuul) %{_localstatedir}/log/zuul
%{python3_sitelib}/zuul
%{python3_sitelib}/zuul-*.egg-info/
%{_bindir}/zuul
%{_bindir}/zuul-bwrap

%files webui
%license LICENSE
%{_datadir}/zuul-ui

%files scheduler
%license LICENSE
%{_bindir}/zuul-scheduler
%{_unitdir}/zuul-scheduler.service

%files merger
%license LICENSE
%{_bindir}/zuul-merger
%{_unitdir}/zuul-merger.service

%files web
%license LICENSE
%{_bindir}/zuul-web
%{_unitdir}/zuul-web.service

%files executor
%license LICENSE
%{_bindir}/zuul-executor
%{_bindir}/zuul-manage-ansible
%{_unitdir}/zuul-executor.service
%dir %attr(0755,zuul,zuul) %{_sharedstatedir}/zuul/ansible
%dir %attr(0755,zuul,zuul) %{_sharedstatedir}/zuul/executor

%files fingergw
%license LICENSE
%{_bindir}/zuul-fingergw
%{_unitdir}/zuul-fingergw.service

%files migrate
%license LICENSE
%{_bindir}/zuul-migrate

%files doc
%license LICENSE
%doc build/html README.fedora


%changelog
* Wed Mar 11 2020 Fabien Boucher <fboucher@redhat.com> - 3.19.0-1
- Bump to 3.19.0
- Fedora rawhide compat

* Tue Mar  3 2020 Tristan Cacqueray <tdecacqu@redhat.com> - 3.18.0-1
- Bump to 3.18.0
- Use -f argument for services
- Use smart-reconfigure command for scheduler reload

* Wed Feb 26 2020 Tristan Cacqueray <tdecacqu@redhat.com> - 3.13.0-2
- Add security fix

* Tue Dec 10 2019 Fabien Boucher <fboucher@redhat.com> - 3.13.0-1
- Bump to 3.13.0

* Tue Oct 22 2019 Fabien Boucher <fboucher@redhat.com> - 3.11.1-1
- Bump to 3.11.1

* Mon Sep 23 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.10.2-2
- Remove SCL leftovers

* Tue Sep 17 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.10.2-1
- Add synchronize rsh security fix

* Thu Aug 15 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.10.1-1
- Bump to 3.10.1

* Mon May 20 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.8.1-3
- Add merger optimization

* Tue May 14 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.8.1-2
- Remove a couple of un-needed patches

* Wed May  8 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.8.1-1
- Bump to 3.8.1
- Remove React service worker

* Wed Apr 17 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.8.0-1
- Bump to 3.8.0

* Mon Mar 25 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.7.1-1
- Bump to 3.7.1

* Mon Mar 18 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.7.0-1
- Bump to 3.7.0

* Mon Feb 11 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.6.0-1
- Bump to 3.6.0

* Fri Feb  8 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.5.0-2
- Cherry-pick github fix
- Fix config endpoint

* Wed Jan 23 2019 Javier Peña <jpena@redhat.com> - 3.5.0-1
- Bump to 3.5.0

* Wed Jan  2 2019 Tristan Cacqueray <tdecacqu@redhat.com> - 3.4.0-1
- Bump to 3.4.0

* Thu Nov 29 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.3.1-1
- Update the openshift resources patches
- Use package version in the zuul.version module

* Tue Nov  6 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.3.0-1
- Bump to 3.3.0

* Mon Sep 24 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.2.0-6
- Add react web interface

* Wed Sep 19 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.2.0-5
- Bump to latest master

* Thu Aug  9 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.2.0-4
- Add timer trigger fix

* Mon Aug  6 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.2.0-3
- Add missing canonical name in scheduler status

* Sat Aug  4 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.2.0-2
- Add node age to webpage

* Mon Jul 30 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.2.0-1
- Bump version

* Wed Jul 18 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.1.0-5
- Bump to last master for ui fix

* Mon Jul  2 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.1.0-4
- Bump to 3.1.1 tech preview

* Fri Jun 22 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.1.0-3
- Add resource connection type patch
- Add patch to get the zuul-scheduler -t validation option
- Add /etc/localtime patch

* Thu Jun 21 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.1.0-2
- Fix tenant status page reload issue
- Add glyphicon status balls

* Fri Jun 15 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.1.0-1
- Bump version to 3.1.0
- Add angular6 patch

* Mon May 28 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.2-2
- Bump ansible patch to 2.5 version

* Fri Apr 13 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.2-1
- Update version to 3.0.2 release
- Update the MQTT driver patch

* Fri Apr 13 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.1-1
- Update version to 3.0.1 release
- Add patch to fix tag reporter
- Update the MQTT driver patch

* Thu Mar 29 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-26
- Update version to 3.0.0 release

* Tue Mar 20 2018 Fabien Boucher <fboucher@redhat.com> - 3.0.0-25
- Bump version for security fixes
- Add patches for supporting zuul to start with a broken config

* Fri Mar 16 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-24
- Bump version for security fixes
- Add new Nodepool dashboards

* Thu Mar 15 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-23
- Bump version

* Tue Mar 13 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-22
- Bump version

* Thu Feb 22 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-21
- Add missing ansible-2.4 fix

* Wed Feb 21 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-20
- Bump version
- Add branch-column patch
- Fix dynamic config loader

* Mon Feb 19 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-19
- Bump version and switch to ansible 2.4 requirement

* Wed Feb 07 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-18
- Bump version
- Add pipelines.json endpoint

* Wed Jan 31 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-17
- Bump version
- Add external webui built with npm

* Mon Jan 22 2018 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-16
- Bump version
- Add config-loader optimization patch
- Add job page description patch
- Add dynamic config load
- Remove with_restart in systemd unit
- Add doc sub package

* Wed Dec 27 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-15
- Bump version
- Add jmespath to the executor requirements
- Add fingergw sub-package
- Add zookeeper retry logic patch

* Tue Dec 05 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-14
- Bump version

* Wed Nov 29 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-13
- Bump version
- Add MQTT driver patch
- Add log_stream options patch

* Fri Nov 17 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-12
- Force ssh known_host to be in scl user home

* Mon Nov  6 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-11
- Bump version and slightly update the patches

* Wed Nov  1 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-10
- Bump version and remove merged patches

* Wed Sep 27 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-9
- Add newrev patch

* Thu Sep 14 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-8
- Add zuul-web interfaces

* Tue Sep 05 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-7
- Add scheduler StartPost command to wait for gearman server.

* Fri Aug 25 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-6
- Fix zuul-web static file missing from python module
- Fix bwrap usage (LD_LIBRARY_PATH is removed by setuid)
- Bump version

* Tue Jul 25 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-5
- Bump version and fix executor reload

* Wed Jul 12 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-4
- Bump version and add zuul-web package

* Thu Jul  6 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-3
- Remove demonization from service file

* Thu Jun 29 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-2
- Fix service reload

* Mon Jun 19 2017 Tristan Cacqueray <tdecacqu@redhat.com> - 3.0.0-1
- Initial packaging
