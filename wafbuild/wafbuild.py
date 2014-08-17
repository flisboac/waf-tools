#!/usr/bin/env python

# The MIT License (MIT)
# 
# Copyright (c) 2014 Flávio Lisbôa <flisboa.costa@gmail.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


version = "0.1.0"
version_info = (0, 1, 0, "", 0)

"""All target names that are to be consired special for build declarations.
   These are not valid target names, and will be ignored."""
_special_target_names = set(('all',))

"""All build names that are considered special.
   These are not valid build names, and will be ignored.."""
_special_build_names = set(('all', 'default'))

"""The default build name to use, if none is declared."""
_fallback_default_build_name = "release"

"""Set of all operator symbols to be used on target values' declarations."""
_target_operation_symbols = set('<+')

"""Evaluation string separator."""
_target_evalstring_separator = " "


def options(ctx):
	default_build = _get_declared_default_build_name(ctx, _fallback_default_build_name)
	ctx.add_option('-B', '--build', action='store', default="",
		help='Specifies which build type to run. Default: %s' % default_build)
	target = _get_all_all_target(ctx, is_before_configure = True)
	tools = _get_tools(ctx, {'all': target})
	for tool in tools:
		ctx.load(tool['tool'], **tool)


def list_builds(ctx):
	builds = _get_builds(ctx, include_all = False)

	print("Default build type:")
	print("\t%s%s" % (_get_current_build_name(ctx), _get_declared_default_build_name(ctx, '') and " " or " (implicit defaults)" ))

	print("Available build types and targets:")
	for build in builds:
		targets = _get_build_targets(ctx, buildname = build, include_all = False, is_before_configure = True)
		targets_list = targets.keys()
		print( "\t%s: %s" % (build, ", ".join(targets_list)) )



def configure(ctx):
	from pprint import pprint
	# Sets the build name
	ctx.env.build = _get_current_build_name(ctx)

	# Gets the build targets, ignoring expression evaluation
	targets = _get_build_targets(ctx, include_all = False, is_before_configure = True)
	tools = _get_tools(ctx, targets)
	for tool in tools:
		ctx.load(tool['tool'])

	pprint(ctx.env.table)
	# Reloads targets, now with expression evaluation, to make sure all tools were loaded.
	targets = _get_build_targets(ctx, include_all = False)
	checks = _get_checks(ctx, targets)
	programs = _get_programs(ctx, targets)
	for check in checks:
		ctx.check(**check)
	for program in programs:
		ctx.find_program(**program)


def build(ctx):
	targets = _get_build_targets(ctx)
	for targetname in targets:
		if targetname:
			ctx(**targets[targetname])


def _get_list(ctx, targets, key, defaultkey):
	values = {}

	for targetname in targets:
		target = targets[targetname]
		valuelist = target.get(key, [])

		if type(valuelist) is list or type(valuelist) is tuple:
			for value in valuelist:
				if type(value) is dict:
					values[value[defaultkey]] = value

				else:
					values[value] = {defaultkey: value}

		else:
			values[valuelist] = {defaultkey: valuelist}

	return list(values.values())


def _get_tools(ctx, targets):
	return _get_list(ctx, targets, 'load', defaultkey = 'tool')


def _get_checks(ctx, targets):
	return _get_list(ctx, targets, 'check', defaultkey = 'lib')


def _get_programs(ctx, targets):
	return _get_list(ctx, targets, 'find_program', defaultkey = 'filename')


def _get_all_all_target(ctx, is_before_configure = False):
	allbuilds = _get_builds(ctx, include_all = True)
	allbuild = allbuilds.get('all', {})
	allalltarget = allbuild.get('all', {})
	target = _merge_build_data(ctx, {}, allalltarget, is_before_configure = is_before_configure)
	return target


def _get_declared_default_build_name(ctx, alternative = None):
	from waflib import Context
	allbuilds = _get_builds(ctx, include_all = True)
	if alternative is not None:
		return allbuilds.get('default', alternative)
	else:
		return allbuilds['default']


def _get_current_build_name(ctx, alternative = _fallback_default_build_name):
	buildname = None
	try:
		buildname = ctx.env.build
	except:
		pass

	if not buildname:
		try:
			buildname = ctx.options.build
		except:
			pass

	if not buildname:
		buildname = _get_declared_default_build_name(ctx, alternative = alternative)

	return buildname


def _get_builds(ctx, include_all = False, default_env = None):
	from waflib import Context
	from copy import copy, deepcopy

	try:
		builds = Context.g_module.BUILDS
	except:
		if default_env is None:
			raise Exception("No build types available. Please re-check your wscript and define the BUILDS table.")
		builds = default_env

	env = copy(builds)
	if not include_all:
		for special_name in _special_build_names:
			if special_name in env:
				del env[special_name]

	return env


def _get_build_targets(ctx, buildname = None, include_all = False, is_before_configure = False):
	from waflib import Context
	from copy import copy
	from pprint import pprint

	allbuilds = _get_builds(ctx, include_all = True)
	all_build = allbuilds.get("all", {})

	if not buildname:
		buildname = _get_current_build_name(ctx)

	# It's mandatory to have the build declared.
	try:
		build = allbuilds[buildname]
	except:
		raise Exception("Build '" + buildname + "' is not declared.")

	targetnames = set()
	targets = {}

	for targetname in all_build:
		#if include_all or targetname not in _special_target_names:
			targetnames.add(targetname)

	for targetname in build:
		#if include_all or targetname not in _special_target_names:
			targetnames.add(targetname)

	for targetname in targetnames:
		if include_all or targetname not in _special_target_names:
			targets[targetname] = _get_build_target(ctx, targetname, buildname = buildname, is_before_configure = is_before_configure)

	return targets


def _get_build_target(ctx, targetname, buildname = None, is_before_configure = False, default_build_env = {}):
	from copy import copy
	from waflib import Context
	from pprint import pprint

	if not buildname:
		buildname = _get_current_build_name(ctx)

	allbuilds = _get_builds(ctx, include_all = True)
	allbuild = allbuilds.get('all', {})
	build = allbuilds.get(buildname, default_build_env)
	if build is None:
		raise Exception("Build name '%s' not declared." % buildname)

	# Get all targets involved in the chosen build
	all_all_target = allbuild.get('all', {})           # all.all
	all_target_target = allbuild.get(targetname, None) # all.target

	if buildname != 'all':
		build_all_target = build.get('all', {})            # build.all
		build_target = build.get(targetname, None)         # build.target
	else:
		build_all_target = {}
		build_target = {}

	# Warn if the target wasn't declared.
	if build_target is None and all_target_target is None:
		raise Exception("No target '" + targetname + "' for build '" + buildname + "'.")
	else:
		build_target = build_target or {}
		all_target_target = all_target_target or {}

	data = _merge_build_data(ctx, {}, all_all_target, is_before_configure = is_before_configure)
	_merge_build_data(ctx, data, all_target_target, is_before_configure = is_before_configure)
	_merge_build_data(ctx, data, build_all_target, is_before_configure = is_before_configure)
	_merge_build_data(ctx, data, build_target, is_before_configure = is_before_configure)

	if 'target' not in data:
		data['target'] = targetname

	return data
	

def _merge_build_data(ctx, to, frm, is_before_configure = False):
	from copy import copy
	from pprint import pprint

	for key in frm:
		oper = None
		name = key.strip()
		expr = ""

		# Checks operation
		for s in _target_operation_symbols:
			if name[0] == s:
				oper = s
				name = name[1:]
				break

		# Checks conditional expression
		separator_index = name.find(_target_evalstring_separator)
		if separator_index >= 0:
			expr = name[(separator_index + len(_target_evalstring_separator)):]
			name = name[0:separator_index].strip()

			if hasattr(ctx, 'env'): # Avoids OptionContext
				if not is_before_configure: # Used when waf is still loading tools
					_sanitize_expr(ctx, expr)
					try:
						result = eval(expr, {}, copy(ctx.env.table))

					except:
						raise Exception("Error evaluating expression '%s' for target key '%s', check your wscript file." % (expr, key))

					if not result:
						continue

		# Executes operation
		if name not in to:
			to[name] = frm[key]

		elif oper == '<': # Extend
			# Append
			value = to[name]
			if hasattr(value, 'append'):
				value.append(frm[key])
			else:
				to[name] = value << frm[key]

		elif oper == '+':
			# Extend/Append
			value = to[name]
			if hasattr(value, 'extend'):
				value.extend(frm[key])
			else:
				to[name] = value + frm[key]

		else:
			# Store (no specialized operation specified)
			to[name] = frm[key]

	return to


def _sanitize_expr(ctx, expr):
	pass
	# TODO implementation