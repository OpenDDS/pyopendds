Name:           python3-opendds
Version:        3.20.0
Release:        2%{?dist}
Summary:        Python3 wrapper module for OpenDDS

License:        MIT
URL:            https://github.com/Sdpierret/pyopendds/
Source:         packagesource.tar.gz

BuildArch:	x86_64
BuildRequires:  python3-devel

%global _description %{expand:
PyOpenDDS is a framework for using OpenDDS from Python.
 It has the goal of providing the standard full DDS API in OpenDDS in a Pythonic form.}

%description %_description

%package -n pyopendds
Summary:        %{summary}

%description -n pyopendds %_description

%prep
%autosetup -p1 -n pyopendds

%build
%py3_build

%install
%py3_install

%check
%{python3} setup.py test

%files -n pyopendds
%{python3_sitelib}/%{srcname}-*.egg-info/
%{python3_sitelib}/%{srcname}/

# %doc README.md

%changelog
