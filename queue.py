#!/bin/python
# path to python

# where is your writable directory? Jobs will be managed in a .queue directory here.
SCRATCH="FULL_PATH_TO_YOUR_SCRATCH_SPACE"

# username
USER="YOUR_USERNAME_HERE"

# how big is one batch of jobs? ex 10 means there must be 10 free slots to run another batch.
JOB_ARRAY_MAX=20

# max total jobs to run in parallel with this tool (ideally multiple of JOB_ARRAY_MAX)
QUEUE_MAX=140

##
##
## Customize everything before this line
##
##

import os, sys, shutil
import glob
import pickle
import time
import re
from subprocess import check_output
import argparse

basedir = os.path.dirname(os.path.realpath(__file__))

def joinpath(*args):
	build = args[0]
	for iarg in range(1,len(args)):
		build = os.path.join(build,args[iarg]);
	return build;

def existingProjects():
	projects = [];
	confdir = joinpath(SCRATCH, ".queue");
	if os.path.isdir(confdir):
		for folder in os.walk(confdir).next()[1]:
			projectdir = joinpath(confdir,folder);
			projects.append(projectdir);
		return projects
	else:
		return False

def quitWithMsg(msg):
	print("\n");
	print(msg);
	sys.exit(1);

def runningJobs():
	'''Returns list of job ids (just the 12345 number part)
	for all running jobs of the specified user'''

	list_running = check_output(["qstat -au "+USER+" | tail -n +6 | cut -d'.' -f1 | cut -d'[' -f1"], shell=True);
	list_running = list_running.split('\n');
	list_running = [int(e) for e in list_running if len(e) != 0];
	return list_running;

def splitArrayJob(jobfile,jobtext,begin,end):
	begin = int(begin);
	end = int(end);
	rxBegin = re.compile(r'''XBEGINX''');
	rxEnd = re.compile(r'''XENDX''');
	rxMultiplier = re.compile(r'''XMULTIPLIERX''');
	rxSet = re.compile(r'''XSETX''');
	rxOffset = re.compile(r'''XOFFSETX''');
	SETS = (end - begin + 1) / JOB_ARRAY_MAX;
	REMAINDER = (end - begin + 1) % JOB_ARRAY_MAX;
	firstJobMade=False;
	projectdir=joinpath(SCRATCH,".queue");
	jobs_to_add = [];
	projdirname = "array_"+jobfile;
	if not os.path.exists(joinpath(SCRATCH,".queue",projdirname)):
		os.makedirs(joinpath(SCRATCH,".queue",projdirname));
	for set in range(SETS):
		this_filename = str(set*JOB_ARRAY_MAX+begin)+"."+str(set*JOB_ARRAY_MAX+begin+JOB_ARRAY_MAX-1)+".sh";
		jobs_to_add.append(this_filename);
		open(joinpath(projectdir,"array_"+jobfile,this_filename),'w').write(rxOffset.sub(str(begin-1),rxSet.sub(str(JOB_ARRAY_MAX),rxMultiplier.sub(str(set),rxEnd.sub(str(JOB_ARRAY_MAX),rxBegin.sub(str(1),jobtext)))))); ## for each set, multiplier=set, begin=begin, end=begin+JOB_ARRAY_MAX-1
		firstJobMade=True;
	if (REMAINDER != 0):
		this_filename = str(SETS*JOB_ARRAY_MAX+begin)+"."+str(end)+".sh";
		jobs_to_add.append(this_filename);
		if (firstJobMade == True):
			open(joinpath(projectdir,"array_"+jobfile,this_filename),'w').write(rxOffset.sub(str(begin-1),rxSet.sub(str(JOB_ARRAY_MAX),rxMultiplier.sub(str(SETS),rxEnd.sub(str(REMAINDER),rxBegin.sub(str(1),jobtext)))))); ## at remainder, assume first job started: multiplier=SETS, begin=1, end=end
		else:
			open(joinpath(projectdir,"array_"+jobfile,this_filename),'w').write(rxOffset.sub(str(begin-1),rxSet.sub(str(JOB_ARRAY_MAX),rxMultiplier.sub(str(SETS),rxEnd.sub(str(end-begin+1),rxBegin.sub(str(1),jobtext)))))); ## at remainder, assume NOT first job started: multiplier=
	pickle.dump(jobs_to_add, open(joinpath(SCRATCH,".queue",projdirname,".held"),"wb"));
	submitted = [];
	pickle.dump(submitted, open(joinpath(SCRATCH,".queue",projdirname,".submitted"),"wb")); #write empty array so file exists

def checkOnJobsForProjects():
	"""Submits jobs for folders found in the .queue hidden folder.
	Returns False if there were jobs found to submit or running, True otherwise."""
	
	projects = existingProjects();
	if (projects == False):
		quitWithMsg("No projects found\n");
	running_jobs = runningJobs();
	available_slots = 0; #how many jobs we can submit at the end of evaluation
	zeroJobsLeft = True;
	for project in projects:
		submitted_jobs = pickle.load(open(joinpath(project,".submitted"),"rb"));
		held_jobs = pickle.load(open(joinpath(project,".held"),"rb"));
		for job in submitted_jobs:
			if (job not in running_jobs):
				submitted_jobs.remove(job);
		if (len(held_jobs) == 0 and len(submitted_jobs) == 0):
			shutil.rmtree(project) #remove finished project
			continue;
		else:
			zeroJobsLeft = False;
		available = QUEUE_MAX - (len(running_jobs)*JOB_ARRAY_MAX);
		if (available >= 0):
			available_slots += (available/JOB_ARRAY_MAX);
		while ((available_slots > 0) and (len(held_jobs) > 0)):
			job = held_jobs.pop();
			jobID = submitJobGetID(joinpath(project,job));
			submitted_jobs.append(jobID);
			available_slots -= 1;
		pickle.dump(submitted_jobs, open(joinpath(project,".submitted"),"wb"));
		pickle.dump(held_jobs, open(joinpath(project,".held"),"wb"));
	return zeroJobsLeft;

def submitJobGetID(jobFileFullPath):
	'''Submits a job file given the full path
	and returns the integer job id part of 12345.job.mgr[] etc.'''

	ID = check_output(["qsub "+jobFileFullPath], shell=True); 
	ID = int(ID.split('\n')[0].split('.')[0].split('[')[0]);
	return ID;

def daemonIsRunning():
	daemonfile = joinpath(SCRATCH,'.queue','.daemon');
	if os.path.exists(daemonfile) and os.path.isfile(daemonfile):
		return True;
	else:
		return False;

def markDaemonIsRunning():
	daemonfile = joinpath(SCRATCH,'.queue','.daemon');
	open(daemonfile, 'a').close();

def markDaemonNotRunning():
	daemonfile = joinpath(SCRATCH,'.queue','.daemon');
	if os.path.exists(daemonfile) and os.path.isfile(daemonfile):
		os.remove(daemonfile);

def getArrayRangeAndTemplateFile(filename):
	'''takes a filename of a qsub submit file.
	returns the numbers used in this type of line: #PBS -t 1-100
	and returns the new file contents replaced with template symbols: #PBS -t XBEGINX-XENDX
	and a new line beneath that: PBS_ARRAYID=$[${PBS_ARRAYID}+XMULTIPLIERX*XSETX+XOFFSETX]'''

	filetext = None;
	with open(filename, 'r') as filehandle:
		filetext = filehandle.read();
	regex = re.compile(r'''PBS -t[\s]*(\d+)[\s]*-[\s]*(\d+)''');
	match = regex.search(filetext);
	filetext = regex.sub(r'''PBS -t XBEGINX-XENDX
PBS_ARRAYID=$[${PBS_ARRAYID}+XMULTIPLIERX*XSETX+XOFFSETX]''',filetext);
	return (match.group(1), match.group(2), filetext);

def submitSelf():
	check_output(["qsub -j oe -o /dev/null -l mem=2gb,nodes=1:ppn=1,walltime=03:55:00 "+joinpath(SCRATCH,'.queue','queue.py')], shell=True);

def help():
	'''Returns args object.'''

	print("  Usage: ./queue.py [qsub file or resume]")
	print("")
	print("  qsub file: A qsub array job.")
	print("  resume: Resubmits self in job manager mode if necessary.")
	print("  <no arguments>: Assumes run in automated job manager mode")
	print("    and will kill itself and resubmit itself every 4 hours.")
	print("")
	print("  Warning: this script possibly produces many files.")
	print("    take care to remove job directories no longer")
	print("    needed by the end of the qsub file.")
	print("")
	print("  The working folder is "+joinpath(SCRATCH,".queue")+" which")
	print("  contains a semaphore .daemon file, and a project directory")
	print("  for each submitted qsub array file using this tool.")
	print("  Each project directory contains prepared qsub files for")
	print("  each smaller array segment, as well as two hidden files")
	print("  .held and .submitted. .held is a list of qsub files yet")
	print("  to be submitted. .submitted contains job ids for jobs")
	print("  that are running.")
	print("")
	print("  Workflow: submit a qsub array job. queue.py is automatically")
	print("  submitted as a 4 hour job which every minute checks if job")
	print("  status has changed. If so then submits a new chunk of jobs")
	print("  if there is room. A .daemon file is created at the beginning")
	print("  of the job manager 4 hour run, and removed at the end.")
	print("  This .daemon file helps prevent multiple job managers running.")
	print("  However, if you kill the job manager, simpley ./queue.py resume")
	print("  and the job manager will be forced into a running state after")
	print("  submission. The project directories in")
	print("  "+joinpath(SCRATCH,".queue")+" are each removed after")
	print("  all jobs in them are completed.");
	print("")

def main():
	if (len(sys.argv) > 1): # Users wants to submit a new job
		if (sys.argv[1] in ["-h","--h","--help","-?","--?"]):
			help()
			sys.exit(0);
		if (sys.argv[1] == "resume"):
			markDaemonIsRunning();
			shutil.copy("queue.py", joinpath(SCRATCH,'.queue','queue.py'));
			submitSelf();
			sys.exit(0);
		rangeBegin, rangeEnd, fileTemplated = getArrayRangeAndTemplateFile(sys.argv[1]);
		splitArrayJob(sys.argv[1], fileTemplated, rangeBegin, rangeEnd);
		shutil.copy("queue.py", joinpath(SCRATCH,'.queue','queue.py'));
		checkOnJobsForProjects();
		if not daemonIsRunning():
			markDaemonIsRunning();
			submitSelf();
	else:							# Not user-mode, but automated startup to maintain jobs
		if not daemonIsRunning():
			sys.stderr.write("Something is wrong, because we're running a new instance but the daemon flag is gone. Shutting down.\n");
			sys.exit(0);
		justUnder4Hours = 3600*4 - 60*10; #10 minutes under
		timeStart = time.time();
		while ((time.time() - timeStart) < justUnder4Hours):
			done = checkOnJobsForProjects();
			if (done == True):
				markDaemonNotRunning();
				sys.exit(0);
			else:
				time.sleep(60); # wait one minute
		submitSelf();
		sys.exit(0);

if __name__ == "__main__":
	main();
