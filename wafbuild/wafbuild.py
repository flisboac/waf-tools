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



def options(ctx):
	ctx.add_option('-B', '--build', action='store', default="release",
		help='Specifies which build to run.')
	ctx.add_option('--list-builds', action='store_true',
		help='Lists all available builds and their targets (NOT IMPLEMENTED YET).')
	target = _get_all_all_target(ctx)
	tools = _get_tools(ctx, {'all': target})
	checks = _get_checks(ctx, {'all': target})
	for tool in tools:
		ctx.load(tool['tool'], **tool)


def configure(ctx):
	targets = _get_build_targets(ctx, include_all = False)
	tools = _get_tools(ctx, targets)
	checks = _get_checks(ctx, targets)
	programs = _get_programs(ctx, targets)
	for tool in tools:
		ctx.load(tool['tool'])
	for check in checks:
		ctx.check(**check)
	for program in programs:
		ctx.find_program(**program)
	ctx.env.build = ctx.options.build


def build(ctx):
	targets = _get_build_targets(ctx)
	for targetname in targets:
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
					#values.append(value)
				else:
					values[value] = {defaultkey: value}
					#values.append({defaultkey: value})
		else:
			values[valuelist] = {defaultkey: valuelist}
			#values.append({defaultkey: valuelist})
	return list(values.values())


def _get_tools(ctx, targets):
	return _get_list(ctx, targets, 'load', defaultkey = 'tool')


def _get_checks(ctx, targets):
	return _get_list(ctx, targets, 'check', defaultkey = 'lib')


def _get_programs(ctx, targets):
	return _get_list(ctx, targets, 'find_program', defaultkey = 'filename')


def _get_all_all_target(ctx):
	targets = _get_build_targets(ctx, 'all', include_all = True)
	all_target = targets['all'] or {}
	return all_target


def _get_build_targets(ctx, buildname = None, include_all = False):
	from waflib import Context
	if not buildname:
		try:
			buildname = ctx.env.build
			if not buildname: buildname = ctx.options.build
		except:
			buildname = ctx.options.build

	try:
		builds = Context.g_module.BUILDS
	except:
		builds = {}

	allbuilddata = builds.get('all', {})

	# It's mandatory to have the build declared.
	try:
		targetbuilddata = builds[buildname]
	except:
		raise Exception("Build '" + buildname + "' is not declared.")

	targetnames = set()
	targets = {}
	for targetname in allbuilddata: targetnames.add(targetname)
	for targetname in targetbuilddata: targetnames.add(targetname)
	for targetname in targetnames:
		if include_all or targetname != 'all':
			targets[targetname] = _get_build_target(ctx, targetname, buildname)
	return targets


def _get_build_target(ctx, targetname, buildname = None):
	from copy import copy
	from waflib import Context
	if not buildname:
		try:
			buildname = ctx.env.build
			if not buildname: buildname = ctx.options.build
		except:
			buildname = ctx.options.build

	try:
		builds = Context.g_module.BUILDS
	except:
		raise Exception("BUILDS dictionary is not declared.")

	allbuilddata = builds.get('all', {})
	allalldata = allbuilddata.get('all', {})
	alldata = allbuilddata.get(targetname, {})

	# It's mandatory to have the build declared.
	targetbuilddata = builds.get(buildname, {})
	targetalldata = targetbuilddata.get('all', {})
	targetdata = targetbuilddata.get(targetname, {})

	#if not allbuilddata and not targetbuilddata:
	#	raise Exception("Build '" + buildname + "' is not declared.")

	data = copy(allalldata)
	for key in alldata: data[key] = alldata[key]
	for key in targetalldata: data[key] = targetalldata[key]
	for key in targetdata: data[key] = targetdata[key]

	if not data:
		raise Exception("No target '" + targetname + "' for build '" + buildname + "'.")
	else:
		if 'target' not in data:
			data['target'] = targetname
	
	return data
	
