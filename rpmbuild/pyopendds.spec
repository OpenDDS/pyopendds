Name:           dragonfly-logger
Version:        2.0
Release:        1
Summary:        python binding for OpenDDS
Group:          net
License:        GPL
URL:            http://github.com/Upnext-DragonFly
Vendor:         Upnext
Source:         packagesource.tar.gz
Prefix:         %{_prefix}
Packager:       Dragonfly
BuildRoot:      %{_tmppath}/%{name}-%{version}
BuildRequires:  opendds-devel >= 3.20-1
BuildRequires:  python3-devel
Requires:       opendds >= 3.20-1

%description
python binding for OpenDDS

%files
%{python3_sitelib}/pyopendds/


