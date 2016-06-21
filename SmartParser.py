# -*- coding: gb2312 -*-
# SmartParser 2.2
#   - Added matchMaxDepth feature, separated match recursive and non-recursive methods, added debug control, added correctness test infrastructure, added basic test coverage
#   - Added ability to dump settings, init with an empty element
from collections import defaultdict
import bs4
import inspect
import os
import sys
import urllib2

class SmartParser(object):
	MATCHTOLERANCE = {'matchAll': 0, 'matchMissingChild': 1, 'matchRedundantChild': 2}
	MATCHTYPE = {'strict': 0, 'loose': 1}

	def __init__(self, element = None):
		''' accepts an html snippet that defines the target element '''
		if element != None and not isinstance(element, bs4.element.Tag):
			raise Exception('Unsupported target element type: {0}'.format(type(element)))
		self.element = element

		# @matchType:
		# strict = match both tag and attribute
		# loose = match tag only
		self.matchType = SmartParser.MATCHTYPE['loose']
		# @matchMaxDepth: the maximum depth when matching two elements; element root's depth is 0
		self.matchMaxDepth = float('inf')
		# @matchTolerance:
		# matchAll = consider it a match only if all children match
		# matchMissingChild = consider it still a match if some children in the exemplar element are missing in the candidate
		# matchRedundantChild = consider it still a match if some children in the candidate are missing in the exemplar element
		self.matchTolerance = SmartParser.MATCHTOLERANCE['matchAll']
		# TODO: @matchInsideElement: only search for matches among the descendent of a given element; search all elements if set to None
		self.matchInsideElement = None
		# @debug settings
		self.debug, self.debugPause, self.debugVerbose = False, True, False

		return

	def Parse(self, html):
		''' accepts an html, returns all pattern-matching elements '''
		self.Debug('In function Parse():')
		if not isinstance(self.element, bs4.element.Tag):
			raise Exception('Target element has not been set.')

		# get outermost element name and element attributes
		eleTag, eleAttrs = self.element.name, self.element.attrs
		self.Debug('element name: {0} \t attrs: {1}'.format(eleTag, eleAttrs))

		# get all matching candidates in the html
		if self.matchType == SmartParser.MATCHTYPE['strict']:
			candidates = html.find_all(eleTag, attrs = eleAttrs)
		else:
			candidates = html.find_all(eleTag)
		self.Debug('Number of candidates: {0}'.format(len(candidates)))
		for i in candidates:
			self.DebugVerbose(i.prettify().encode('utf-8'))

		# for each candidate, further check if its structure matches our element
		matches = []
		for candidate in candidates:
			if self.IsMatchRecursive(candidate, element, 0):
				matches.append(candidate)
		self.Debug('Number of matches: {0}'.format(len(matches)))
		for i in matches:
			self.DebugVerbose(i.prettify().encode('utf-8'))

		return matches

	def IsMatchRecursive(self, element1, element2, depth):
		''' determine if two elements have the same structure '''
		if depth > self.matchMaxDepth: # exceeds max depth
			return True

		if not self.IsMatchNonRecursive(element1, element2): # name or attrs differ
			return False

		if depth == self.matchMaxDepth: # reaches max depth
			return True

		child1, child2 = element1.findChild(), element2.findChild()
		while child1 and child2: # compare all children elements
			if not self.IsMatchRecursive(child1, child2, depth + 1):
				return False
			child1, child2 = child1.findNextSibling(), child2.findNextSibling()

		if self.matchTolerance != SmartParser.MATCHTOLERANCE['matchMissingChild'] and child1 != None or child2 != None: # number of children differ
			self.DebugVerbose('Number of children differ: {0}\n{1}'.format(element1.prettify().encode('utf-8'), element2.prettify().encode('utf-8')))
			return False

		return True

	def IsMatchNonRecursive(self, element1, element2):
		''' determine if two elements match regardless of their children '''
		if element1 is None or element2 is None:
			self.DebugVerbose('Elements differ: {0}\n{1}'.format(element1, element2))
			return False

		if self.matchType == SmartParser.MATCHTYPE['loose']:
			if element1.name != element2.name:
				self.DebugVerbose('Element names differ: {0}\n{1}'.format(element1.name, element2.name))
				return False
		elif self.matchType == SmartParser.MATCHTYPE['strict']:
			if element1.name != element2.name or element1.attrs != element2.attrs:
				self.DebugVerbose('ELement names or attrs differ: {0} {1}\n{2} {3}'.format(element1.name, element1.attrs, element2.name, element2.attrs))
				return False
		else:
			raise Exception('Unsupported matchType: {0}'.format(self.matchType))
		return True

	def Debug(self, msg):
		if self.debug or self.debugVerbose:
			print msg
			if self.debugPause:
				raw_input()

	def DebugVerbose(self, msg):
		if self.debugVerbose:
			print msg
			if self.debugPause:
				raw_input()

	def Settings(self):
		''' return all settings of current SmartParser instance '''
		attrs = [attr for attr in vars(self).items() if not callable(attr) and not inspect.ismethod(attr)]
		self.Debug('\n'.join('{0} = {1}'.format(pair[0], pair[1]) for pair in attrs))
		return attrs


if __name__ == '__main__':
	tmpTest = False
	oneTimeTest = False

	if tmpTest:
		pass

	elif oneTimeTest:
		# load element and html from files
		# BeautifulSoup will take a snippet as an html and encapsulate it with "document",
		# therefore we need to get the actual content to pass in the SmartParser
		element = bs4.BeautifulSoup(open('test\\element5.html', 'r').read(), 'html.parser').findChild()
		url = 'https://leetcode.com/problemset/algorithms/'
		rawHtml = urllib2.urlopen(url).read()
		html = bs4.BeautifulSoup(rawHtml,  'html.parser')
		smartParser = SmartParser(element)
		smartParser.matchMaxDepth = 1
		print 'Exemplar:'
		print element.prettify().encode('utf-8')
		raw_input()

		# get all target content
		matches = smartParser.Parse(html)

		print 'Number of items found: {0}'.format(len(matches))
		raw_input()
		for i in matches:
			print i.prettify().encode('utf-8')
			raw_input()

	else:
		# correctness tests
		testPath = os.path.abspath('test')
		print 'Loading tests from {0}...'.format(testPath)
		fid = open(os.path.join(testPath, 'definition.txt'), 'r')
		testCount, passCount, failCount, skipCount = 0, 0, 0, 0
		temp = SmartParser(bs4.BeautifulSoup('<html></html>', 'html.parser'))

		# loop through tests
		for i, line in enumerate(fid):
			if i == 0:
				assert(line.strip() == '[TESTS]')
				continue
			reqs = line.strip().split(';')
			name, desc, input, vars, _assert = '', '', defaultdict(str), defaultdict(str), False

			# remove old standard file, if exists
			try:
				os.remove(os.path.join(testPath, name + '_standard.html'))
			except OSError:
				pass

			# loop through arguments
			for req in reqs:
				key, value = map(lambda x: x.lstrip().rstrip(), req.split('=', 1))
				if key == 'name':
					name = value
				elif key == 'desc':
					desc = value
				elif key == 'assert':
					_assert = map(lambda x: x.lstrip().rstrip(), value.split('==', 1))
				elif key == 'element' or key == 'html':
					input[key] = value
				elif key in dir(temp):
					vars[key] = value
			
			# load exemplar element
			element = bs4.BeautifulSoup(open(os.path.join(testPath, name + '_element.html'), 'r').read(), 'html.parser')
			exec('element = element{0}'.format(input['element']))

			# load html
			html = bs4.BeautifulSoup(open(os.path.join(testPath, name + '_html.html'), 'r').read(), 'html.parser')
			exec('html = html{0}'.format(input['html']))

			# create object
			smartParser = SmartParser(element)

			# set object parameters
			for key in vars.keys():
				exec('smartParser.{0} = int(vars["{1}"])'.format(key, key))

			# parse
			matches = smartParser.Parse(html)

			# dump
			fid = open(os.path.join(testPath, name + '_standard.html'), 'w')
			for match in matches:
				fid.write(match.prettify().encode('utf-8') + '\n')
			fid.close()

			# assert
			exec('result = {0}; expect = int({1})'.format(_assert[0], _assert[1]))
			sys.stdout.write('correctness.test.{0}'.format(name).ljust(40, '.'))
			if result != expect:
				print 'fail'
				print '\tresult: {0}  expected: {1}'.format(result, expect)
				failCount += 1
			else:
				print 'pass'
				passCount += 1

			testCount += 1
		fid.close()

		# correctness test summary
		print ''
		print '----------------------------------------------------'
		print 'Tests executed:  {0}'.format(testCount)
		print 'Tests passed:    {0}'.format(passCount)
		print 'Tests failed:    {0}'.format(failCount)
		print 'Tests skipped:   {0}'.format(skipCount)
		print 'Percent passing: {0:.2f}%'.format(float(passCount) / float(testCount - skipCount) * 100)
		print '----------------------------------------------------'
