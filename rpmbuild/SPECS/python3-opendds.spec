%global srcname pyopendds
%global debug_package ${nil}

%define __python3 /usr/bin/python3.8

Name:           python3-opendds
Version:        3.20.4
Release:        0%{?dist}
Summary:        Setuptools extension to build and package CMake projects

License:        MIT
URL:            https://github.com/diegoferigo/%{srcname}
Source:         packagesource.tar.gz

BuildArch:	x86_64
BuildRequires:  python38-devel, python38-setuptools, cmake, python3-cmake-build-extension
BuildRequires:  opendds-devel, python38-jinja2, python38-wheel

Requires: python38-jinja2, python38-wheel

%global _description %{expand:
Setuptools extension to build and package CMake projects.}

%description %_description

%prep
%setup -n %{srcname}

%build
#pushd %{py3dir}
pushd %{_builddir}/%{srcname}
%{__python3} setup.py build
popd

%install
#pushd %{py3dir}
pushd %{_builddir}/%{srcname}
%{__python3} setup.py install --root %{buildroot}
popd

#%check
#%{__python3} setup.py test

%files
%{python3_sitearch}/*
%{_bindir}/itl2py
%{_bindir}/pyidl


%doc README.md

%changelog
