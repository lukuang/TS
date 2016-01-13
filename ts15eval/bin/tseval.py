#!/usr/bin/python
from __future__ import division
import argparse, sys, os, re, bisect
from math import exp, pi, atan
import itertools
import numpy as np
mpl = None
plt = None

# Expects >=4 files: Nuggets File, Updates File, Match File, Run File(s)

# Nuggets File:
# Query_ID Nugget_ID Nugget_Timestamp Nugget_Importance Nugget_Length (...)
# Where (...) can be extra information, including the nugget text

# Runs File:
# Query_ID Team_ID Run_ID Document_ID Sentence_ID Decision_Timestamp Confidence_Value

# Updates Sample File:
# Query_ID Update_ID Document_ID Sentence_ID Update_Length (Update_Text)

# Matches File:
# Query_ID Update_ID Nugget_ID Update_Start Update_End


# PARAMETERS

latency_base = 0.95
latency_step = 3600 * 6
#latency_variant = True
latency_variant = False

max_impt = 3
sorter = "hmean" # Harmonic Mean

# END PARAMETERS

debug = False
conf = {}
events = {}
dup_map = {}

redstart = '\033[1;31m'
grstart = '\033[1;34m'
colorend = '\033[0;0m'

np.seterr(divide='raise', invalid='ignore')


def make_updid(did, sid):
	return '%s-%s' % (did, sid)

def make_runid(tid, rid):
	return '%s-%s' % (tid, rid)

class MatchArray(object):
	def __init__(self, text, byword=True):
		self.byword = byword
		self.text = text
		if byword:
			self.arr = [0] * (text.count(" ") + 1)
		else:
			self.arr = [0] * len(text)
	def update(self, start, end):
		start = max(0, self.text.rfind(" ", 0, start + 1))
		end = self.text.find(" ", end, len(self.text))
		if end == -1:
			end = len(self.text)
		if self.byword:
			start = self.text.count(" ", 0, start)
			end = self.text.count(" ", 0, end)
			if start == -1:
				start = 0
			if end == -1:
				end = 1
		for ind in range(start, end):
			self.arr[ind] = 1
		return end - start + 1
	def count(self):
		return sum(self.arr)
	def __len__(self):
		return len(self.arr)

class Scores(dict):
	def __init__(self, qid, idealegains, nuggets, nuggtots, upds=None):
		self.qid = qid
		self.iegains = idealegains
		self.iegain = idealegains[-1]
		self.nuggets = nuggets
		self.nuggtots = nuggtots
		self.upds = upds

	def calculate(self, upds=None, fn=None, scnt=None):
		self.iegain = self.iegains[min(len(self.iegains),len(upds))-1]
		if upds is not None:
			self.upds = upds
		self['nupd'] = len(self.upds)
		if scnt is not None:
			self['nsupd'] = scnt
		else:
			self['nsupd'] = len(self.upds)
		if fn is not None:
			getattr(self, 'fn_' + fn)()
			return self[fn]
		else:
			# Find all score functions and run them
			for fn in sorted(dir(self)):
				if fn.startswith('fn_'):
					getattr(self, fn)()
			#return self.scores

	def scores(self, metrics=None):
		if metrics is not None:
			return [("%s " % x) + ("%d" % y if type(y) == "int" else "%0.4f" % y) for x, y in [(z, self[z]) for z in metrics]]
		else:
			return self.values()

	def gain(self):
		try:
			return self._gain
		except AttributeError:
			self._gain = sum([x["gain"] for x in self.upds])
			return self._gain
	def verbosity(self):
		try:
			return self._verb
		except AttributeError:
			self._verb = sum([x["verbosity"] for x in self.upds])
			return self._verb
	def latgain(self):
		try:
			return self._latgain
		except AttributeError:
			self._latgain = sum([x["latgain"] for x in self.upds])
			return self._latgain
	def nmatch(self):
		try:
			return self._nmatch
		except AttributeError:
			self._nmatch = sum([x["nmatch"] for x in self.upds])
			return self._nmatch
	def latency(self):
		try:
			return self._latency
		except AttributeError:
			self._latency = sum([x["latency"] for x in self.upds])
			return self._latency
	#def confidence(self):
	#	try:
	#		return self._confidence
	#	except AttributeError:
	#		#self._confidence = sum([ x["conf"] for x in self.upds])
	#		confa = [ x["conf"] for x in self.upds]
	#		self._confidence = (min(confa), max(confa), sum(confa))
	#		return self._confidence


	def gainsbyconf(self):
		ideal_recall = self.nuggtots["impt"]
		ideal_expgains = self.iegains
		prgains = []
		prlatgains = []
		prcomps = []
		prlatcomps = []
		prgain = 0
		prlatgain = 0
		prverb = 0
		prconfs = []
		prranks = []
		nupd = 0
		for upd in sorted(self.upds, key=lambda x: x["conf"], reverse=True):
			if "gain" not in upd:
				continue
			if upd["gain"] < 0:
				print >>sys.stderr, "WTH, gain is negative?!?"
				quit()
			prgain += upd["gain"]
			prlatgain += upd["latgain"]
			prverb += upd["verbosity"]
			nupd += 1
			prgains.append(prgain / prverb)
			prlatgains.append(prlatgain / prverb)
			prcomps.append(prgain / ideal_recall)
			prlatcomps.append(prlatgain / ideal_recall)
			prconfs.append(upd["conf"])
			prranks.append(nupd)

		if len(prgains) > len(ideal_expgains):
			padgains = np.pad(ideal_expgains, (0, len(prgains)-len(ideal_expgains)), mode='edge')
		else:
			padgains = ideal_expgains[:len(prgains)]
		prngains = np.divide(prgains, padgains)
		prnlatgains = np.divide(prlatgains, padgains)
		maxgain = 0
		maxlgain = 0
		maxngain = 0
		maxnlgain = 0
		prnhms = [0 if np.isnan(x) else x for x in 2*(prngains * prcomps) / (prngains + prcomps)]
		prnlathms = [0 if np.isnan(x) else x for x in 2*(prnlatgains * prlatcomps) / (prnlatgains + prlatcomps)]
		for gind in reversed(range(len(prgains))):
			if maxgain < prgains[gind]:
				maxgain = prgains[gind]
			if maxlgain < prlatgains[gind]:
				maxlgain = prlatgains[gind]
			if maxngain < prngains[gind]:
				maxngain = prngains[gind]
			if maxnlgain < prnlatgains[gind]:
				maxnlgain = prnlatgains[gind]
			prgains[gind] = maxgain
			prlatgains[gind] = maxlgain
			prngains[gind] = maxngain
			prnlatgains[gind] = maxnlgain
		return {
			"gains": prgains, "latgains": prlatgains,
			"ngains": prngains, "nlatgains": prnlatgains,
			"comps": prcomps, "latcomps": prlatcomps,
			"confs": prconfs,
			"ranks": prranks,
			"nhms": prnhms, "nlathms": prnlathms,
		}

	def gainsbytime(self, start=None, end=None, duration=None, step=None, scale=None):
		ideal_recall = self.nuggtots["impt"]

		if start is None:
			start = events[self.qid]["start"]
		if step is None:
			step = 1
		if end is None:
			if duration is None:
				end = events[self.qid]["end"]
			else:
				end = start + duration
		if scale is None:
			scale = 1

		timea = np.arange(start, end, step*scale)
		updgains = []
		updlatgains = []
		updngains = []
		updnlatgains = []
		updcomps = []
		updlatcomps = []
		updgain = 0
		updlatgain = 0
		updverb = 0
		nugggain = 1
		nugggains, nuggtimes = calc_ideal(self.nuggets, dim="time", reverse=False)
		ngind = 0
		updind = 0
		updates = sorted(self.upds, key=lambda x: x["time"])
		for time in timea:
			while updind < len(updates) and time >= updates[updind]["time"]:
				upd = updates[updind]
				updind += 1
				if "gain" not in upd:
					continue
				updgain += upd["gain"]
				updlatgain += upd["latgain"]
				updverb += upd["verbosity"]
			while ngind < len(nuggtimes) and time >= nuggtimes[ngind]:
				nugggain = nugggains[ngind]
				ngind += 1

			try:
				gain = updgain / updverb
				latgain = updlatgain / updverb
			except ZeroDivisionError:
				gain = 0
				latgain = 0

			try:
				ngain = updgain / updverb / nugggain
				nlatgain = updlatgain / updverb / nugggain
			except ZeroDivisionError:
				ngain = 0
				nlatgain = 0

			try:
				comp = updgain / ideal_recall
				latcomp = updlatgain / ideal_recall
			except ZeroDivisionError:
				comp = 0
				latcomp = 0

			updgains.append(gain)
			updlatgains.append(latgain)
			updngains.append(ngain)
			updnlatgains.append(nlatgain)
			updcomps.append(comp)
			updlatcomps.append(latcomp)

		return {
				"gains": updgains, "latgains": updlatgains,
				"ngains": updngains, "nlatgains": updnlatgains,
				"comps": updcomps, "latcomps": updlatcomps,
				"times": (timea - start) / scale
		}

	def fn_egain(self):
		try:
			self['egain'] = self.gain() / self.verbosity()
		except (ZeroDivisionError, FloatingPointError):
			self['egain'] = 0
		if np.isnan(self['egain']):
			self['egain'] = 0


	def fn_negain(self):
		try:
			egain = self['egain']
		except KeyError:
			self.fn_egain()
			egain = self['egain']
		try:
			self['negain'] = egain / self.iegain
		except (ZeroDivisionError, FloatingPointError):
			self['negain'] = 0
		if np.isnan(self['negain']):
			self['negain'] = 0

	def fn_elatgain(self):
		try:
			self['elatgain'] = self.latgain() / self.verbosity()
		except (ZeroDivisionError, FloatingPointError):
			self['elatgain'] = 0
		if np.isnan(self['elatgain']):
			self['elatgain'] = 0

	def fn_nelatgain(self):
		try:
			elatgain = self['elatgain']
		except KeyError:
			self.fn_elatgain()
			elatgain = self['elatgain']
		try:
			self['nelatgain'] = elatgain / self.iegain
		except (ZeroDivisionError, FloatingPointError):
			self['nelatgain'] = 0
		if np.isnan(self['nelatgain']):
			self['nelatgain'] = 0

	def fn_comp(self):
		try:
			self['comp'] = self.gain() / self.nuggtots["impt"]
		except (ZeroDivisionError, FloatingPointError):
			self['comp'] = 0
		if np.isnan(self['comp']):
			self['comp'] = 0

	def fn_latcomp(self):
		try:
			self['latcomp'] = self.latgain() / self.nuggtots["impt"]
		except (ZeroDivisionError, FloatingPointError):
			self['latcomp'] = 0
		if np.isnan(self['latcomp']):
			self['latcomp'] = 0

	def fn_everb(self):
		try:
			self['everb'] = self.verbosity() / self["nupd"]
		except (ZeroDivisionError, FloatingPointError):
			self['everb'] = 0
		if np.isnan(self['everb']):
			self['everb'] = 0

	def fn_elat(self):
		try:
			#self['elat'] = self.latency() / self["nupd"]
			self['elat'] = self.latency() / self.nmatch()
		except (ZeroDivisionError, FloatingPointError):
			self['elat'] = 0
		if np.isnan(self['elat']):
			self['elat'] = 0

	def fn_econfgain(self):
		try:
			self['econfgain'] = sum([x["gain"] * x["conf"] for x in self.upds]) / (
				self.verbosity())
		except (ZeroDivisionError, FloatingPointError):
			self['econfgain'] = 0
		if np.isnan(self['econfgain']):
			self['econfgain'] = 0

	def fn_neconfgain(self):
		try:
			econfgain = self['econfgain']
		except KeyError:
			self.fn_econfgain()
			econfgain = self['econfgain']
		try:
			self['neconfgain'] = econfgain / self.iegain
		except (ZeroDivisionError, FloatingPointError):
			self['neconfgain'] = 0
		if np.isnan(self['neconfgain']):
			self['neconfgain'] = 0

	def fn_econflatgain(self):
		try:
			self['econflatgain'] = sum([x["latgain"] * x["conf"] for x in self.upds]) / (
				self.verbosity())
		except (ZeroDivisionError, FloatingPointError):
			self['econflatgain'] = 0
		if np.isnan(self['econflatgain']):
			self['econflatgain'] = 0

	def fn_neconflatgain(self):
		try:
			econflatgain = self['econflatgain']
		except KeyError:
			self.fn_econflatgain()
			econflatgain = self['econflatgain']
		try:
			self['neconflatgain'] = econflatgain / self.iegain
		except (ZeroDivisionError, FloatingPointError):
			self['neconflatgain'] = 0
		if np.isnan(self['neconflatgain']):
			self['neconflatgain'] = 0

	def fn_confcomp(self):
		try:
			self['confcomp'] = sum([x["gain"] * x["conf"] for x in self.upds]) / (
				self.nuggtots["impt"])
		except (ZeroDivisionError, FloatingPointError):
			self['confcomp'] = 0
		if np.isnan(self['confcomp']):
			self['confcomp'] = 0

	def fn_conflatcomp(self):
		try:
			self['conflatcomp'] = sum([x["latgain"] * x["conf"] for x in self.upds]) / (
				self.nuggtots["impt"])
		except (ZeroDivisionError, FloatingPointError):
			self['conflatcomp'] = 0
		if np.isnan(self['conflatcomp']):
			self['conflatcomp'] = 0

	def fn_econfverb(self):
		try:
			self['econfverb'] = sum([x["verbosity"] * x["conf"] for x in self.upds]) / self["nupd"]
		except (ZeroDivisionError, FloatingPointError):
			self['econfverb'] = 0
		if np.isnan(self['econfverb']):
			self['econfverb'] = 0

	def fn_econflat(self):
		try:
			self['econflat'] = sum([x["latency"] * x["conf"] for x in self.upds]) / self["nupd"]
		except (ZeroDivisionError, FloatingPointError):
			self['econflat'] = 0
		if np.isnan(self['econflat']):
			self['econflat'] = 0

	def fn_z_hmean(self):
		try:
			self['hmean'] = 2*self['nelatgain'] * self['latcomp'] / (self['nelatgain'] + self['latcomp'])
		except (ZeroDivisionError, FloatingPointError):
			self['hmean'] = 0
		if np.isnan(self['hmean']):
			self['hmean'] = 0

	def fn_z_confhmean(self):
		try:
			self['confhmean'] = 2*self['neconflatgain'] * self['conflatcomp'] / (self['neconflatgain'] + self['conflatcomp'])
		except (ZeroDivisionError, FloatingPointError):
			self['confhmean'] = 0
		if np.isnan(self['confhmean']):
			self['confhmean'] = 0


class Scorer(object):
	def __init__(self, nuggets, nuggtots):
		if latency_variant:
			self.nuggets = nuggets
			self.nuggtots = nuggtots
			self.buckets = FuzzyList(sorted([(x['time'], x) for x in nuggets]))

	def latency_discount(self, t_gold, t):
		#return pow(latency_base, (t - t_gold) / latency_step)
		if latency_variant:
			step = latency_step / self.latency_bucket(t_gold)
		else:
			step = latency_step
		return 1 - (2 * (atan((t - t_gold) / step) / pi))

	def latency_bucket(self, time):
		# TODO: Calculate latency bucket
		return 1


class Run(object):
	def __init__(self, run):
		self.run = run
	def eval(self, fn=None):
		if fn is not None and fn in self.score:
			return self.score[fn]

class Query(object):
	def __init__(self, nuggets, runs, params):
		self.nuggets = nuggets
		self.runs = runs
		self.params = params


def calc_ideal(nuggets, dim="impt", reverse=True):
	iegains = []
	sumgain = 0
	sumverb = 0
	dima = []
	for nugg in sorted(nuggets.values(), key=lambda n: n[dim], reverse=reverse):
		sumgain += norm_impt(nugg)
		sumverb += 1
		iegains.append(sumgain/sumverb)
		dima.append(nugg[dim])
	return iegains, dima

def avggains(scoresa, metrics = ['gains', 'nhms'], cutoffs = [pow(2, x) for x in range(10)]):
	avgs = {}

	if type(metrics) != list:
		metrics = [metrics]

	maxnupd = 0
	for metric in metrics:
		scores = [x[metric] for x in scoresa]
		if not maxnupd:
			maxnupd = max([len(x) for x in scores])
		scores = np.array([np.pad(np.array(x), (0, maxnupd-len(x)), mode='edge') for x in scores])
		avgs[metric] = np.average(scores, axis=0)
	avgs['ranks'] = range(1, maxnupd+1)

	return avgs

	#scores = [x['ngains'] for x in scoresa]
	#indv = [x['indv'] for x in scoresa]
	#maxnupd = max([len(x) for x in scores])
	#maxnupd = max(maxnupd,max(cutoffs))
	#scores = [np.array(x).pad(maxnupd-len(x),mode='edge') for x in scores]
	#avgs = np.average(scores, axis=0)
	#cind = 0
	#for inda,scorea in izip(scores,indv):
	#	for ind,score in izip(inda,scorea):
	#		if ind > cutoffs[cind]:
	#
	#return cutoffs, avgs

def avggainsbyconf(scoresa, metric = 'ngains', cutoffs = [pow(2, x) for x in range(10)]):
	avgs = {}

	scores = [x[metric] for x in scoresa]
	maxnupd = max([len(x) for x in scores])
	maxnupd = max(maxnupd, max(cutoffs))
	scores = [np.array(x).pad(maxnupd-len(x), mode='edge') for x in scores]
	avgs[metric] = np.average(scores, axis=0)
	avgs['ranks'] = cutoffs

	return avgs


metriclst = [
	"nupd",
	"egain",
	"negain",
	"elatgain",
	"nelatgain",
	"comp",
	"latcomp",
	"hmean",
	"everb",
	"elat",
	"econfgain",
	"neconfgain",
	"econflatgain",
	"neconflatgain",
	"confcomp",
	"conflatcomp",
	"confhmean",
	"econfverb",
	"econflat",
	"nsupd",
]

metricnames = {
	"nupd" : "# Updates",
	"egain" : "E[Gain]",
	"negain" : "nE[Gain]",
	"elatgain" : "E[Latency Gain]",
	"nelatgain" : "nE[Latency Gain]",
	"comp" : "Comprehensiveness",
	"latcomp" : "Latency Comp.",
	"hmean" : "HM(nE[LG],Lat. Comp.)",
	"everb" : "E[Verbosity]",
	"elat" : "E[Latency]", 
	"econfgain" : "E[Confidence-Biased Gain]",
	"neconfgain" : "nE[Confidence-Biased Gain]",
	"econflatgain" : "E[Confidence-Biased Latency Gain]",
	"neconflatgain" : "nE[Confidence-Biased Latency Gain]",
	"confcomp" : "Confidence-Biased Comp.",
	"conflatcomp" : "Confidence-Biased Latency Comp.",
	"confhmean" : "Confidence-Biased HM(nE[LG],Lat. Comp.)",
	"econfverb" : "E[Confidence-Biased Verbosity]",
	"econflat" : "E[Confidence-Biased Latency]",
	"nsupd" : "# Sampled Updates",
}

def calc_metric(nuggets, allsamples, allruns, matches, nuggtots, nuggetsh):
	plotsdir = conf.plotsdir
	metrics = metriclst
	print "\t".join(["QueryID", "TeamID", "RunID"] + [metricnames[x] for x in metriclst])

	results = {}
	totals = {}

	for qid, teams in sorted(allruns.items()):
		if qid not in matches or qid not in nuggets:
			continue
		try:
			samples = allsamples[qid]
		except KeyError:
			print >>sys.stderr, "Invalid query id %s found" % qid
			continue
		scorer = Scorer(nuggets[qid], nuggtots[qid])
		nullupd = {"text": "_" * int(nuggtots[qid]["length"]) , "length": nuggtots[qid]["length"], "duplicate": None}
		iegains = np.array(calc_ideal(nuggets[qid])[0])
		for tid, runs in sorted(teams.items()):
			for rid, docs in sorted(runs.items()):
				seen = {}
				runscores = Scores(qid, iegains, nuggets[qid], nuggtots[qid])
				upds = sorted(docs, key=lambda x: x["time"])
				newupds = []
				supdcount = 0
				for upd in upds:
					updid = make_updid(upd["did"], upd["sid"])
					# Skip if not sampled
					if (updid in samples):
						supd = samples[updid]
						supdcount += 1
					elif updid in dup_map and dup_map[updid] in samples:
						supd = samples[dup_map[updid]]
						supdcount += 1
					elif (conf.ignore):
						continue
					else:
						supd = nullupd
						updid = None
					newupds.append(upd)
					# Handle exact duplicates
					if supd["duplicate"] and supd["duplicate"] in samples:
						updid = supd["duplicate"]
						supd = samples[updid]
					gain = 0
					latency_gain = 0
					updlat = 0
					unmatch = 0
					otext = supd["text"]
					matcharr = MatchArray(otext)

					if updid not in seen and updid in matches[qid]:
						for match in matches[qid][updid]:
							try:
								nugg = nuggets[qid][match["nid"]]
							except KeyError, err:
								printd("Match contains invalid nugget QID:%s, NID:%s; %s" % (qid, match["nid"], err))
								continue
							if match["nid"] in seen:
								printd("\tAlready Matched: I%d %s" % (nugg["impt"], nugg["text"]))
								continue
							seen[match["nid"]] = 1
							matchlen = matcharr.update(match["updstart"], match["updend"])
							rel = norm_impt(nugg, match)
							gain += rel
							latency = scorer.latency_discount(nugg["time"], upd["time"])
							latency_gain += rel * latency
							updlat += latency
							unmatch += 1
							printd("\tMatch: I%d R%0.4f NT%0.2f UT%0.2f L%0.4f LEN%d %s" % (nugg["impt"], rel, nugg["time"]/latency_step, upd["time"]/latency_step, latency, matchlen, nugg["text"]))
							if nuggetsh is not None:
								print >> nuggetsh, "%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%s\t%s" % (qid, tid, rid, match["nid"], nugg["time"], upd["time"], matchlen, nugg["impt"],nugg["text"],otext)

					verbosity = verbosity_discount(len(matcharr), matcharr.count(), nuggtots[qid]["length"])
					upd["gain"] = gain
					upd["latgain"] = latency_gain
					upd["nmatch"] = unmatch
					upd["verbosity"] = verbosity
					upd["latency"] = updlat
					seen[updid] = 1
					printd("\tUpdate Score: #M%d G%0.4f LG%0.4f V%0.2f L%0.2f" % (unmatch, gain, latency_gain, verbosity, updlat))

				runscores.calculate(upds=newupds,scnt=supdcount)
				printd(("QID %s\tTID %s\tRID %s\t" % (qid, tid, rid)) + "\t".join(runscores.scores(metrics)))

				# Verbose information
				for nid, nugg in sorted(nuggets[qid].iteritems(), key=lambda x: x[1]["impt"]):
					if nid not in seen:
						printd("%s %0.2f %s" % (nid, norm_impt(nugg), nugg["text"]))

				printd("-----------------------------------------------------\n")
				measures = [runscores[x] for x in metrics]
				ostr = ("%s\t%s\t%s\t" % (qid, tid, rid)) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in measures])
				print ostr
				if qid not in results:
					results[qid] = []
				trid = "%s-%s" % (tid, rid)
				results[qid].append(measures)
				if trid not in totals:
					totals[trid] = { "tid": tid, "rid": rid, "metrics": [measures], "scores": [runscores], "rungains": [], "gainsovert": [] }
				else:
					totals[trid]["metrics"].append(measures)
					totals[trid]["scores"].append(runscores)

				if plotsdir and len(newupds) > 0:
					plotbase = os.path.join(plotsdir, "%s-%s-%s" % (tid, rid, qid))
					idstr = 'Query %s, Team %s, Run %s' % (qid, tid, rid)
					rungains, gainsovert = mk_plots(runscores, plotbase, idstr)
					#rungains = runscores.gainsbyconf()
					#gainsovert = runscores.gainsbytime(step=1/24, scale=3600*24)
					#rungains, gainsovert = mk_plots(rungains, gainsovert, plotbase, idstr)
					totals[trid]["rungains"].append(rungains)
					totals[trid]["gainsovert"].append(gainsovert)



		ravg = np.mean(results[qid], 0)
		rstd = np.std(results[qid], 0)
		rmin = np.amin(results[qid], 0)
		rmax = np.amax(results[qid], 0)
		print ("%s\tAVG\t-\t" % (qid)) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in ravg])
		print ("%s\tSTD\t-\t" % (qid)) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in rstd])
		print ("%s\tMIN\t-\t" % (qid)) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in rmin])
		print ("%s\tMAX\t-\t" % (qid)) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in rmax])


	allavgs = {"sys": [], "avgs": []}
	for trid,res in totals.items():
		ravg = np.mean(res["metrics"], 0)
		rstd = np.std(res["metrics"], 0)
		rmin = np.amin(res["metrics"], 0)
		rmax = np.amax(res["metrics"], 0)
		res["stats"] = { "AVG": ravg, "STD": rstd, "MIN": rmin, "MAX": rmax }
		if plotsdir:
			plotbase = os.path.join(plotsdir, "%s-%s" % (trid, "Avg"))
			tid,rid = trid.split('-')
			idstr = '%s, Team %s, Run %s' % ("Avg", tid, rid)
			avgrungains = avggains(totals[trid]["rungains"])
			#avggainsovert = avggains(totals[trid]["gainsovert"])
			avg_plots(avgrungains, plotbase, idstr)
			allavgs["sys"].append(trid)
			allavgs["avgs"].append(avgrungains)


	metricind = metrics.index(sorter)
	for res in sorted(totals.values(), key=lambda x: x["stats"]["AVG"][metricind], reverse=True):
		print ("AVG\t%s\t%s\t" % (res["tid"], res["rid"])) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in res["stats"]["AVG"]])
		print ("STD\t%s\t%s\t" % (res["tid"], res["rid"])) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in res["stats"]["STD"]])
		print ("MIN\t%s\t%s\t" % (res["tid"], res["rid"])) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in res["stats"]["MIN"]])
		print ("MAX\t%s\t%s\t" % (res["tid"], res["rid"])) + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in res["stats"]["MAX"]])
	resultsarr = list(itertools.chain.from_iterable(results.itervalues()))
	ravg = np.mean(resultsarr, 0)
	rstd = np.std(resultsarr, 0)
	rmin = np.amin(resultsarr, 0)
	rmax = np.amax(resultsarr, 0)
	print "AVG\tALL\t-\t" + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in ravg])
	print "STD\tALL\t-\t" + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in rstd])
	print "MIN\tALL\t-\t" + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in rmin])
	print "MAX\tALL\t-\t" + "\t".join(["%d" % x if type(x) == "int" else "%0.4f" % x for x in rmax])
	if plotsdir:
		plotbase = os.path.join(plotsdir, "%s-%s" % ("ALL", "Avg"))
		avg_plots(allavgs["avgs"], plotbase, "Avg ALL", sysa=allavgs["sys"])

# Normalizes the importance score from Real>=0->[0-1], optionally weighting it by the proportion of the nugget matched
def norm_impt(nugg, match = None):
	if conf.binaryrel:
		return 1 if nugg["impt"] > 0 else 0
	#try:
	#	prop = nugg["length"]/(match["nuggend"] - match["nuggstart"])
	#except Exception:
	#	prop = 1
	#return exp(nugg["impt"])/ exp(max_impt) * prop
	#return nugg["impt"]/ max_impt * prop
	return exp(nugg["impt"])/ exp(max_impt)

def verbosity_discount(u_len, matches_len, avglen):
	return max(0, (u_len - matches_len) / avglen) + 1


def mk_gain_array(docs):
	upds = sorted(docs, key=lambda x: x["conf"], reverse=True)
	gains = np.cumsum([ x["gain"] for x in upds])
	latgains = np.cumsum([ x["latgain"] for x in upds])
	verbs = np.cumsum([ x["verbosity"] for x in upds])
	gaina = {"gain": gains, "latgain": latgains, "verb" : verbs}
	return gaina


def avg_plots(arrs, basefile, idstr, sysa=None):
	fixedaxes = conf.fixedaxes
	binrel = ".binrel" if conf.binaryrel else ""

	if sysa is None:
		sysa = [idstr]
		arrs = [arrs]

	fig, ax = plt.subplots()
	for sys, arr in zip(sysa, arrs):
		ax.plot(arr["ranks"], arr["gains"], label=sys)
	#if len(sysa) > 1:
	#	ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
	ax.set_xlabel('Ranks')
	ax.set_ylabel('Gain')
	if fixedaxes:
		ax.set_ylim(0.0, 1.0)

	ax.set_xscale('log')
	fig.suptitle('Gain@K Curves for %s' % (idstr), fontsize=16)
	plt.tight_layout()
	plt.subplots_adjust(top=0.90)
	plotfile = basefile + "_PK_AVG%s.png" % binrel
	plt.savefig(plotfile)
	plt.close()

	fig, ax = plt.subplots()
	for sys, arr in zip(sysa, arrs):
		ax.plot(arr["ranks"], arr["nhms"], label=sys)
	#if len(sysa) > 1:
	#	ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
	ax.set_xlabel('Ranks')
	ax.set_ylabel('nH')
	if fixedaxes:
		ax.set_ylim(0.0, 1.0)

	ax.set_xscale('log')
	fig.suptitle('H@K Curves for %s' % (idstr), fontsize=16)
	plt.tight_layout()
	plt.subplots_adjust(top=0.90)
	plotfile = basefile + "_HK_AVG%s.png" % binrel
	plt.savefig(plotfile)
	plt.close()

def mk_plots(scores, basefile, idstr):
	fixedaxes = conf.fixedaxes
	timearrs = {}

	arrs = scores.gainsbyconf()
	fig, axarr = plt.subplots(2,2)
	
	axarr[0,0].plot(arrs["ranks"], arrs["nhms"])
	#axarr[0,0].set_xlim(1,0)
	axarr[0,0].set_xlabel('Rank')
	axarr[0,0].set_ylabel('HM[nEG,C]')

	#axarr[0,1].plot(arrs["invranks"], arrs["nlathms"])
	#axarr[0,1].set_xlim(1,0)
	#axarr[0,1].set_xlabel('Inverse Rank')
	axarr[0,1].plot(arrs["ranks"], arrs["nlathms"])
	axarr[0,1].set_xlabel('Rank')
	axarr[0,1].set_ylabel('HM[nELG,LC]')
	
	axarr[1,0].plot(arrs["comps"], arrs["gains"])
	axarr[1,0].set_xlabel('Comprehensiveness')
	axarr[1,0].set_ylabel('Gain')

	axarr[1,1].plot(arrs["latcomps"], arrs["latgains"])
	axarr[1,1].set_xlabel('Latency Comprehensiveness')
	axarr[1,1].set_ylabel('Latency Gain')

	if fixedaxes:
		#axarr[0, 0].axis([1.0, 0, 0.0, 1.0])
		#axarr[0, 1].axis([1.0, 0, 0.0, 1.0])
		axarr[0, 0].set_ylim(0.0, 1.0)
		axarr[0, 1].set_ylim(0.0, 1.0)
		axarr[1, 0].axis([0, 1.0, 0.0, 1.0])
		axarr[1, 1].axis([0, 1.0, 0.0, 1.0])
	
	fig.suptitle('Gain/Comp Curves for %s' % (idstr), fontsize=16)
	plt.tight_layout()
	plt.subplots_adjust(top=0.90)
	plt.savefig(basefile + "_GC.png")
	plt.close()

	return arrs, timearrs



def read_nuggets(nuggets_file, matches, wikitimep=True):
	printd("Reading nuggets from %s" % nuggets_file)
	nuggets = {}
	nuggtots = {}
	nonmatched = 0
	with open(nuggets_file) as handle:
		linen = 0
		handle.readline()
		for line in handle:
			linen += 1
			parts = line.strip().split('\t')
			try:
				qid = re.sub(r'^TS[0-9]+\.', '', parts[0])
				nid = parts[1]
				if conf.matchedonly and (qid not in matches or nid not in matches[qid]):
					nonmatched += 1
					continue
				if qid not in nuggets:
					nuggets[qid] = {}
					nuggtots[qid] = { "impt": 0, "length": 0, "counts": {} }
				impt = float(parts[3])
				if impt <= 0:
					continue
				if wikitimep:
					wtime = int(parts[2])
				else:
					wtime = None
				nuggets[qid][nid] = { "time": wtime, "impt": impt, "length": int(parts[4]), "text": " ".join(parts[5:]) }
				impt = norm_impt(nuggets[qid][nid])
				nuggtots[qid]["impt"] += impt


				# TODO: remove "hack"
				nuggets[qid][nid]["length"] = nuggets[qid][nid]["text"].count(" ") + 1



				nuggtots[qid]["length"] += nuggets[qid][nid]["length"]
				if impt not in nuggtots[qid]["counts"]:
					nuggtots[qid]["counts"][impt] = 1
				else:
					nuggtots[qid]["counts"][impt] += 1

			except Exception, err:
				print >> sys.stderr, "Invalid line in %s, line %d: %s" % (nuggets_file, linen, err)
	for qid, nuggs in nuggets.iteritems():
		try:
			nuggtots[qid]["length"] /= len(nuggs.keys())
		except ZeroDivisionError:
			pass
	printd("Found %d nonmatched" % nonmatched)

	return (nuggets, nuggtots)

# Query_ID Update_ID Document_ID Sentence_ID Update_Length (Update_Text)
def read_updates(updates_file):
	printd("Reading updates from %s" % updates_file)
	supdates = {}
	with open(updates_file) as handle:
		handle.readline()
		linen = 0
		for line in handle:
			linen += 1
			parts = line.strip().split('\t')
			try:
				qid = re.sub(r'^TS[0-9]+\.', '', parts[0])
				updid = parts[1]
				#docid = parts[2]
				#sid	= parts[3]
				if qid not in supdates:
					supdates[qid] = {}
				#if docid not in supdates[qid]:
				#	supdates[qid][docid] = {}
				if len(parts) > 5:
					dup = parts[5]
					if dup == "NULL":
						dup = None
					utext = " ".join(parts[6:])
				else:
					dup = None
					utext = ""
				supdates[qid][updid] = { "length": int(parts[4]), "duplicate": dup, "text": utext, "doctime": None}

				#TODO: remove "hack"
				supdates[qid][updid]["length"] = supdates[qid][updid]["text"].count(" ") + 1

			except Exception, err:
				print >> sys.stderr, "Invalid line in %s, line %d: %s" % (updates_file, linen, err)
	return supdates

# Query_ID Team_ID Run_ID Document_ID Sentence_ID Decision_Timestamp Confidence_Value (Update_Length)
def read_runs(runs_files, updates):
	runs = {}
	for runs_file in runs_files:
		printd("Reading runs from %s" % runs_file)
		with open(runs_file) as handle:
			errs = 0
			linen = 0
			recc = 0
			ridc = 0
			qidc = 0
			for line in handle:
				linen += 1
				parts = line.strip().split()
				if len(parts) <= 1:
					errs+=1
					continue
				try:
					qid = re.sub(r'^TS[0-9]+\.', '', parts[0])
					try:
						int(qid)
					except Exception:
						errs+=1
						pass
					teamid = parts[1]
					runid = parts[2]
					docid = parts[3]
					sid	= parts[4]
					updtime = int(parts[5])
					if qid not in runs:
						runs[qid] = {}
					if teamid not in runs[qid]:
						runs[qid][teamid] = {}
						qidc+=1
					if runid not in runs[qid][teamid]:
						runs[qid][teamid][runid] = []
						ridc+=1
					conf = float(parts[6])
					if conf == float('inf'):
						conf = 1000
					runs[qid][teamid][runid].append({ "did": docid, "sid": sid, "time": updtime, "_conf": conf})
					updid = make_updid(docid,sid)
					if qid in updates and updid in updates[qid]:
						if updates[qid][updid]["doctime"] is not None and updtime < updates[qid][updid]["doctime"]:
							print >>sys.stderr,"Uh oh, bad update time %d < %d doc time for q %s u %s r %s" % (updtime, updates[qid][updid]["doctime"], qid, updid, make_runid(teamid, runid))
							runs[qid][teamid][runid].pop()
							continue
						if "time" not in updates[qid][updid] or updates[qid][updid]["time"] > updtime:
							updates[qid][updid]["time"] = updtime
						dupid = updates[qid][updid]["duplicate"]
						if dupid is not None and dupid in updates[qid] and ("time" not in updates[qid][dupid] or updates[qid][dupid]["time"] > updtime):
							updates[qid][dupid]["time"] = updtime
					recc+=1

				except Exception, err:
					print >> sys.stderr, "Invalid line in %s, line %d: %s" % (runs_file, linen, err)
					errs += 1
			if (errs > 0):
				print >>sys.stderr, "Found %d errors in file %s" % (errs, runs_file)
			printd("Read %d records in %d runs and %d queries" % (recc, ridc, qidc))
	for teams in runs.values():
		for truns in teams.values():
			for run in truns.values():
				confa = [x["_conf"] for x in run]
				cmin = min(confa)
				crng = max(confa) - cmin
				for upd in run:
					if crng == 0:
						upd["conf"] = 0.5
					else:
						upd["conf"] = (upd["_conf"] - cmin) / crng
	return runs

# Query_ID Update_ID Nugget_ID Update_Start Update_End
def read_matches(matches_file):
	printd("Reading matches from %s" % matches_file)
	matches = {}
	nuggmatches = {}
	with open(matches_file) as handle:
		handle.readline()
		linen = 0
		for line in handle:
			linen += 1
			parts = line.split('\t')
			try:
				qid = re.sub(r'^TS[0-9]+\.', '', parts[0])
				updid = parts[1]
				nid = parts[2]
				if qid not in matches:
					matches[qid] = {}
					nuggmatches[qid] = {}
				if updid not in matches[qid]:
					matches[qid][updid] = []
				if nid not in nuggmatches[qid]:
					nuggmatches[qid][nid] = []
				matches[qid][updid].append({ "nid": nid, "updstart": int(parts[3]), "updend": int(parts[4])})
				nuggmatches[qid][nid].append({ "updid": nid, "updstart": int(parts[3]), "updend": int(parts[4])})

			except Exception, err:
				print >> sys.stderr, "Invalid line in %s, line %d: %s" % (matches_file, linen, err)
	return matches, nuggmatches

def printd(string):
	if conf.debug:
		print >> sys.stderr, string

def fix_latency(nuggets, updates, matches):
	for qid,qmatches in matches.iteritems():
		if qid not in nuggets or qid not in updates:
			continue
		qnuggets = nuggets[qid]
		qupdates = updates[qid]
		for uid, upd in qupdates.iteritems():
			if uid in qmatches:
				for match in qmatches[uid]:
					if not match["nid"] in qnuggets:
						continue
					if not "time" in upd:
						printd("Update %s, %s has no time (were pooled runs excluded?)" % (qid, uid))
					elif qnuggets[match["nid"]]["time"] is None or qnuggets[match["nid"]]["time"] > upd['time']:
						qnuggets[match["nid"]]["time"] = upd['time']

					if upd["duplicate"] is not None and upd["duplicate"] in qupdates:
						uid = upd["duplicate"]
						if not "time" in qupdates[uid]:
							printd("Update %s, %s has no time (were pooled runs excluded?)" % (qid, uid))
						elif qnuggets[match["nid"]]["time"] is None or qnuggets[match["nid"]]["time"] > qupdates[uid]['time']:
							qnuggets[match["nid"]]["time"] = qupdates[uid]['time']

def read_duplicates(duplicates_file):
	global dup_map
	with open(duplicates_file) as dh:
		for line in dh:
			line = line.strip().split()
			if len(line) < 2:
				continue
			dup_map[line[1]] = line[0]
			dup_map[line[0]] = line[1]


class FuzzyList:
	def __init__(self, a):
		#self.a = sorted(a)
		self.a = a

	def index(self, x):
		'Locate the leftmost value exactly equal to x'
		i = bisect.bisect_left(self.a, x)
		if i != len(self.a) and self.a[i] == x:
			return i
		raise ValueError
	
	def find_lt(self, x):
		'Find rightmost value less than x'
		i = bisect.bisect_left(self.a, x)
		if i:
			return self.a[i-1]
		raise ValueError
	
	def find_le(self, x):
		'Find rightmost value less than or equal to x'
		i = bisect.bisect_right(self.a, x)
		if i:
			return self.a[i-1]
		raise ValueError
	
	def find_gt(self, x):
		'Find leftmost value greater than x'
		i = bisect.bisect_right(self.a, x)
		if i != len(self.a):
			return self.a[i]
		raise ValueError
	
	def find_ge(self, x):
		'Find leftmost item greater than or equal to x'
		i = bisect.bisect_left(self.a, x)
		if i != len(self.a):
			return self.a[i]
		raise ValueError

def main(args):
	global conf, debug, mpl, plt
	conf = args
	if args.debug:
		debug = True
	if args.plotsdir:
		#mpl.use('SVG')
		import matplotlib as mpl
		mpl.use('Agg')
		import matplotlib.pyplot as plt
		if False:
			plt.null()
		if not os.path.exists(args.plotsdir):
			os.makedirs(args.plotsdir)
	if conf.fixedlatency == 'updonly':
		wikitime = False
	else:
		wikitime = True
	matches, nuggmatches = read_matches(args.matches)
	(nuggets, nuggtots) = read_nuggets(args.nuggets, nuggmatches, wikitime)
	sample = read_updates(args.updates)
	runs = read_runs(args.runs, sample)
	if os.path.exists(args.duplicates_file):
		read_duplicates(args.duplicates_file)
	if conf.fixedlatency is not None:
		fix_latency(nuggets, sample, matches)

	if args.nuggetsfile:
		if not os.path.exists(os.path.dirname(args.nuggetsfile)):
			os.makedirs(os.path.dirname(args.nuggetsfile))
		nuggetsh = open(args.nuggetsfile,'w')
		print >> nuggetsh, "\t".join(("QID", "TID", "RID", "NID", "NTIME", "UTIME","CWORDS","NREL","S1","S2"))
	else:
		nuggetsh = None

	calc_metric(nuggets, sample, runs, matches, nuggtots, nuggetsh)

if __name__ == "__main__":
	argparser = argparse.ArgumentParser(description='Computes Evaluation Metrics for Temporal Summarization Track')
	argparser.add_argument('-n', '--nuggets', help='Nuggets File', default="/lustre/scratch/lukuang/Temporal_Summerization/TS/ts15eval/data/nuggets.tsv")
	argparser.add_argument('-u', '--updates', help='Updates File', default="/lustre/scratch/lukuang/Temporal_Summerization/TS/ts15eval/data/updates_sampled.tsv")
	argparser.add_argument('-m', '--matches', help='Matches File', default="/lustre/scratch/lukuang/Temporal_Summerization/TS/ts15eval/data/exactMatches2015.tsv")
	argparser.add_argument('--duplicates_file', help='Duplicates File', default="/lustre/scratch/lukuang/Temporal_Summerization/TS/ts15eval/data/duplicates.tsv")
	argparser.add_argument('runs', nargs="+", help='Runs File(s)')
	argparser.add_argument('-d', '--debug', action='store_true', help='Debug mode (lots of output)')
	argparser.add_argument('-i', '--ignore', action='store_true', help='Ignore unsampled updates (rather than considering non-relevant)')
	argparser.add_argument('-p', '--plotsdir', help='Create plots as well, stored in this directory')
	argparser.add_argument('-f', '--fixedaxes', action='store_true', help='Use fixed axes for plotting')
	argparser.add_argument('-l', '--fixedlatency', help='Fix latency ("updonly" - ignore wiki time completely, "all" - earliest of wiki and update time)')
	argparser.add_argument('-t', '--matchedonly', action='store_true', help='Only use matched nuggets for normalization')
	argparser.add_argument('-o', '--nuggetsfile', help='Create a nuggets matching file as well')
	argparser.add_argument('-b', '--binaryrel', action='store_true', help='Use binary relevance instead of graded relevance')
	main(argparser.parse_args())
